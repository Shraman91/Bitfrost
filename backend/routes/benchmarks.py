import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from backend.config.settings import settings
from backend.db.firestore import get_db
from backend.models.benchmark import Benchmark, BenchmarkCreate, BenchmarkStatus
from backend.models.run import Run, RunStatus, RunLimits
from backend.agents.dispatcher import execute_agent
from backend.sandbox.runner import run_tests_in_sandbox

logger = logging.getLogger("agentarena.benchmarks")
router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])

# In-memory pubsub queues for live SSE streams
_live_subscribers: Dict[str, List[asyncio.Queue]] = {}


def broadcast_benchmark_event(benchmark_id: str, event: Dict[str, Any]):
    """Broadcast an update to all active SSE subscribers for this benchmark."""
    queues = _live_subscribers.get(benchmark_id, [])
    for q in queues:
        try:
            q.put_nowait(event)
        except Exception:
            pass


async def execute_run_task(
    benchmark_id: str,
    agent: Dict[str, Any],
    task: Dict[str, Any],
    model: str,
    semaphore: asyncio.Semaphore
):
    """
    Executes a single (agent x task) benchmark run under a concurrency semaphore.
    """
    async with semaphore:
        db = get_db()
        run_id = f"run_{agent['id']}_{task['id']}_{int(time.time() * 1000)}"
        run_limits = RunLimits(
            max_calls=settings.max_calls_per_run,
            max_tokens=settings.max_tokens_per_run,
            timeout=task.get("timeout", settings.default_run_timeout_seconds) * 3
        )

        # 1. Initialize Run doc in Firestore
        run_data = Run(
            id=run_id,
            benchmark_id=benchmark_id,
            agent_id=agent["id"],
            task_id=task["id"],
            model=model,
            status=RunStatus.RUNNING,
            limits=run_limits,
            created_at=time.time()
        ).model_dump()
        
        # If offline or no live Bifrost, propagate mock mode for deterministic dry runs
        if getattr(settings, "mock_llm", False) or not settings.openai_api_key:
            run_data["_mock_gateway"] = True

        db.collection("runs").document(run_id).set(run_data)
        broadcast_benchmark_event(benchmark_id, {"type": "run_started", "run": run_data})

        # 2. Prepare Agent payload conforming to AgentArena Contract
        llm_base_url = f"{settings.arena_api_url.rstrip('/')}/llm/{run_id}/v1"
        payload = {
            "run_id": run_id,
            "task": {
                "prompt": task.get("prompt", ""),
                "files": task.get("starter_files", {})
            },
            "llm_base_url": llm_base_url,
            "llm_api_key": "arena-benchmark-token",
            "model": model,
            "limits": run_limits.model_dump()
        }

        agent_result = None
        error_msg = None

        try:
            # 3. Call Agent
            agent_result = await execute_agent(agent, payload)
        except Exception as e:
            logger.error(f"Agent execution failed for {run_id}: {e}")
            error_msg = f"Agent failed: {str(e)}"

        # 4. Evaluate in Sandbox if agent returned files
        sandbox_res = None
        generated_files = {}
        notes = ""

        if agent_result and "files" in agent_result:
            generated_files = agent_result["files"]
            notes = agent_result.get("notes", "")
            try:
                # Merge starter files with generated files
                eval_files = {**task.get("starter_files", {}), **generated_files}
                sandbox_res = run_tests_in_sandbox(
                    files=eval_files,
                    hidden_tests=task.get("hidden_tests", ""),
                    timeout=task.get("timeout", 10)
                )
            except Exception as se:
                error_msg = f"Sandbox error: {str(se)}"
        else:
            if not error_msg:
                error_msg = "Agent did not return any code files."

        # 5. Fetch current metered usage from Firestore (recorded by proxy)
        current_run_snap = db.collection("runs").document(run_id).get()
        current_run = current_run_snap.to_dict() if current_run_snap.exists else run_data

        passed = sandbox_res.passed if sandbox_res else False
        score = sandbox_res.score if sandbox_res else 0.0
        passed_tests = sandbox_res.passed_tests if sandbox_res else 0
        total_tests = sandbox_res.total_tests if sandbox_res else 0
        test_output = f"{sandbox_res.stdout}\n{sandbox_res.stderr}".strip() if sandbox_res else ""

        final_status = RunStatus.COMPLETED if (sandbox_res and sandbox_res.error is None) else (
            RunStatus.FAILED if error_msg else RunStatus.COMPLETED
        )

        # 6. Update Run Record with final benchmark results
        updated_run_fields = {
            "status": final_status.value,
            "passed": passed,
            "score": score,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "files": generated_files,
            "notes": notes,
            "test_output": test_output,
            "error": error_msg or (sandbox_res.error if sandbox_res and not passed else None),
            "finished_at": time.time()
        }
        db.collection("runs").document(run_id).update(updated_run_fields)
        
        full_updated_run = {**current_run, **updated_run_fields}
        broadcast_benchmark_event(benchmark_id, {"type": "run_completed", "run": full_updated_run})

        # 7. Update Benchmark document progress
        bench_ref = db.collection("benchmarks").document(benchmark_id)
        bench_snap = bench_ref.get()
        if bench_snap.exists:
            bench_data = bench_snap.to_dict()
            new_completed = bench_data.get("completed_runs", 0) + 1
            total = bench_data.get("total_runs", 1)
            bench_update = {"completed_runs": new_completed}
            if new_completed >= total:
                bench_update["status"] = BenchmarkStatus.COMPLETED.value
                bench_update["finished_at"] = time.time()
            bench_ref.update(bench_update)
            broadcast_benchmark_event(benchmark_id, {
                "type": "benchmark_progress",
                "completed_runs": new_completed,
                "total_runs": total,
                "status": bench_update.get("status", bench_data.get("status"))
            })


async def run_benchmark_orchestrator(benchmark_id: str, agent_ids: List[str], task_ids: List[str], model: str):
    """
    Spawns and monitors all (agent x task) benchmark runs with concurrency limits.
    """
    db = get_db()
    semaphore = asyncio.Semaphore(settings.benchmark_concurrency)

    # Fetch agents
    agents_map = {}
    for a_id in agent_ids:
        snap = db.collection("agents").document(a_id).get()
        if snap.exists:
            agents_map[a_id] = snap.to_dict()
        else:
            # Fallback builtin defaults
            agents_map[a_id] = {"id": a_id, "name": a_id, "type": "builtin", "model": model}

    # Fetch tasks
    tasks_map = {}
    for t_id in task_ids:
        snap = db.collection("tasks").document(t_id).get()
        if snap.exists:
            tasks_map[t_id] = snap.to_dict()
        else:
            tasks_map[t_id] = {"id": t_id, "title": t_id, "prompt": "Coding task", "starter_files": {}, "hidden_tests": ""}

    # Create run coroutines
    coros = []
    for agent_id, agent_data in agents_map.items():
        for task_id, task_data in tasks_map.items():
            target_model = model or agent_data.get("model", "openai/gpt-4o-mini")
            coros.append(
                execute_run_task(
                    benchmark_id=benchmark_id,
                    agent=agent_data,
                    task=task_data,
                    model=target_model,
                    semaphore=semaphore
                )
            )

    await asyncio.gather(*coros, return_exceptions=True)


@router.post("", response_model=Benchmark)
def create_benchmark(b_in: BenchmarkCreate, background_tasks: BackgroundTasks):
    db = get_db()
    benchmark_id = f"bench_{int(time.time() * 1000)}"
    total_runs = len(b_in.agent_ids) * len(b_in.task_ids)

    bench = Benchmark(
        id=benchmark_id,
        agent_ids=b_in.agent_ids,
        task_ids=b_in.task_ids,
        model=b_in.model or "openai/gpt-4o-mini",
        status=BenchmarkStatus.RUNNING,
        total_runs=total_runs,
        completed_runs=0,
        created_at=time.time()
    )

    db.collection("benchmarks").document(benchmark_id).set(bench.model_dump())

    # Launch background orchestration
    background_tasks.add_task(
        run_benchmark_orchestrator,
        benchmark_id,
        b_in.agent_ids,
        b_in.task_ids,
        b_in.model or "openai/gpt-4o-mini"
    )

    return bench


@router.get("/{benchmark_id}")
def get_benchmark(benchmark_id: str):
    db = get_db()
    doc = db.collection("benchmarks").document(benchmark_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    bench_data = doc.to_dict()
    # Fetch all runs associated with this benchmark
    runs_docs = db.collection("runs").where("benchmark_id", "==", benchmark_id).stream()
    runs = [doc.to_dict() for doc in runs_docs]

    return {
        "benchmark": bench_data,
        "runs": runs
    }


@router.get("/{benchmark_id}/live")
async def live_benchmark_stream(benchmark_id: str):
    """
    SSE stream providing real-time updates as runs progress.
    """
    queue = asyncio.Queue()
    if benchmark_id not in _live_subscribers:
        _live_subscribers[benchmark_id] = []
    _live_subscribers[benchmark_id].append(queue)

    async def event_generator():
        try:
            # Emit initial snapshot
            db = get_db()
            doc = db.collection("benchmarks").document(benchmark_id).get()
            if doc.exists:
                yield f"data: {json.dumps({'type': 'init', 'benchmark': doc.to_dict()})}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
        finally:
            if benchmark_id in _live_subscribers and queue in _live_subscribers[benchmark_id]:
                _live_subscribers[benchmark_id].remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

