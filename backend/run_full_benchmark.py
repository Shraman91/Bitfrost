import asyncio
import os
import sys
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from backend.db.firestore import get_db
    from backend.routes.benchmarks import run_benchmark_orchestrator
    from backend.routes.leaderboard import get_leaderboard
    from backend.models.benchmark import Benchmark, BenchmarkStatus
except ImportError:
    from db.firestore import get_db
    from routes.benchmarks import run_benchmark_orchestrator
    from routes.leaderboard import get_leaderboard
    from models.benchmark import Benchmark, BenchmarkStatus


async def main():
    db = get_db()
    print("=" * 70)
    print("AgentArena: Executing Full Benchmark of 3 Builtin Agents on Tasks")
    print("=" * 70)

    # 1. Fetch agents & tasks
    agents_docs = list(db.collection("agents").stream())
    tasks_docs = list(db.collection("tasks").stream())

    agent_ids = [doc.to_dict()["id"] for doc in agents_docs if doc.to_dict()]
    task_ids = [doc.to_dict()["id"] for doc in tasks_docs if doc.to_dict()]

    if not agent_ids or not task_ids:
        print("[!] No agents or tasks found in database. Running seed first...")
        from backend.seed import seed_database
        seed_database()
        agents_docs = list(db.collection("agents").stream())
        tasks_docs = list(db.collection("tasks").stream())
        agent_ids = [doc.to_dict()["id"] for doc in agents_docs]
        task_ids = [doc.to_dict()["id"] for doc in tasks_docs]

    print(f"[*] Agents ({len(agent_ids)}): {agent_ids}")
    print(f"[*] Tasks ({len(task_ids)}): {task_ids}")
    total_runs = len(agent_ids) * len(task_ids)
    print(f"[*] Total benchmark evaluations to execute: {total_runs}")

    # 2. Create benchmark document
    benchmark_id = f"bench_full_{int(time.time())}"
    bench = Benchmark(
        id=benchmark_id,
        agent_ids=agent_ids,
        task_ids=task_ids,
        model="openai/gpt-4o-mini",
        status=BenchmarkStatus.RUNNING,
        total_runs=total_runs,
        completed_runs=0,
        created_at=time.time()
    )
    db.collection("benchmarks").document(benchmark_id).set(bench.model_dump())
    print(f"[+] Created benchmark doc '{benchmark_id}'. Running orchestrator...")

    # 3. Run orchestrator
    t0 = time.time()
    await run_benchmark_orchestrator(
        benchmark_id=benchmark_id,
        agent_ids=agent_ids,
        task_ids=task_ids,
        model="openai/gpt-4o-mini"
    )
    elapsed = time.time() - t0
    print(f"[✓] Benchmark execution completed in {elapsed:.2f}s!")

    # 4. Fetch updated benchmark status
    bench_data = db.collection("benchmarks").document(benchmark_id).get().to_dict()
    print(f"[*] Benchmark status: {bench_data.get('status')} ({bench_data.get('completed_runs')}/{total_runs} runs)")

    # 5. Print Leaderboard Summary
    print("\n" + "=" * 70)
    print("AGENTARENA LEADERBOARD RESULTS")
    print("=" * 70)
    leaderboard = get_leaderboard()
    print(f"{'Rank':<6}{'Agent':<24}{'Pass Rate':<12}{'Score':<10}{'Avg Cost':<12}{'Efficiency':<12}")
    print("-" * 70)
    for i, entry in enumerate(leaderboard, 1):
        print(
            f"#{i:<5}{entry.agent_name:<24}{str(entry.pass_rate)+'%':<12}{entry.avg_score:<10}"
            f"{'$'+str(round(entry.avg_cost_usd, 5)):<12}{entry.efficiency_score:<12}"
        )
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
