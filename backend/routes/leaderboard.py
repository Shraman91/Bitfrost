from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from backend.db.firestore import get_db

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


class AgentLeaderboardEntry(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: str
    model: str
    total_runs: int
    passed_runs: int
    pass_rate: float
    avg_score: float
    avg_tokens: float
    avg_tokens_in: float
    avg_tokens_out: float
    avg_cost_usd: float
    avg_latency_ms: float
    avg_llm_calls: float
    efficiency_score: float


@router.get("", response_model=List[AgentLeaderboardEntry])
def get_leaderboard():
    db = get_db()
    
    # 1. Fetch all agents
    agents_docs = db.collection("agents").stream()
    agents = {doc.to_dict()["id"]: doc.to_dict() for doc in agents_docs if doc.to_dict()}

    # 2. Fetch all runs
    runs_docs = db.collection("runs").stream()
    all_runs = [doc.to_dict() for doc in runs_docs if doc.to_dict()]

    # 3. Group runs by agent_id
    agent_runs: Dict[str, List[Dict[str, Any]]] = {}
    for run in all_runs:
        a_id = run.get("agent_id")
        if not a_id:
            continue
        if a_id not in agent_runs:
            agent_runs[a_id] = []
        agent_runs[a_id].append(run)

    # 4. Compute aggregate metrics
    leaderboard: List[AgentLeaderboardEntry] = []

    # Include all known agents even if 0 runs
    for agent_id, agent_info in agents.items():
        runs = agent_runs.get(agent_id, [])
        total_runs = len(runs)
        
        if total_runs > 0:
            passed_runs = sum(1 for r in runs if r.get("passed", False))
            pass_rate = round((passed_runs / total_runs) * 100.0, 2)
            avg_score = round(sum(r.get("score", 0.0) for r in runs) / total_runs, 3)
            avg_tokens = round(sum(r.get("tokens_total", 0) for r in runs) / total_runs, 1)
            avg_tokens_in = round(sum(r.get("tokens_in", 0) for r in runs) / total_runs, 1)
            avg_tokens_out = round(sum(r.get("tokens_out", 0) for r in runs) / total_runs, 1)
            avg_cost = round(sum(r.get("cost_usd", 0.0) for r in runs) / total_runs, 6)
            avg_latency = round(sum(r.get("latency_ms", 0.0) for r in runs) / total_runs, 1)
            avg_calls = round(sum(r.get("llm_calls", 0) for r in runs) / total_runs, 1)
            
            # Efficiency score = pass_rate / normalized_cost
            # Normalized cost: scale to cents with a small epsilon
            normalized_cost = (avg_cost * 100.0) + 0.05
            efficiency_score = round(pass_rate / normalized_cost, 2)
        else:
            passed_runs = 0
            pass_rate = 0.0
            avg_score = 0.0
            avg_tokens = 0.0
            avg_tokens_in = 0.0
            avg_tokens_out = 0.0
            avg_cost = 0.0
            avg_latency = 0.0
            avg_calls = 0.0
            efficiency_score = 0.0

        leaderboard.append(
            AgentLeaderboardEntry(
                agent_id=agent_id,
                agent_name=agent_info.get("name", agent_id),
                agent_type=agent_info.get("type", "builtin"),
                model=agent_info.get("model", "openai/gpt-4o-mini"),
                total_runs=total_runs,
                passed_runs=passed_runs,
                pass_rate=pass_rate,
                avg_score=avg_score,
                avg_tokens=avg_tokens,
                avg_tokens_in=avg_tokens_in,
                avg_tokens_out=avg_tokens_out,
                avg_cost_usd=avg_cost,
                avg_latency_ms=avg_latency,
                avg_llm_calls=avg_calls,
                efficiency_score=efficiency_score
            )
        )

    # Sort by efficiency score descending, then pass_rate descending
    leaderboard.sort(key=lambda x: (x.efficiency_score, x.pass_rate), reverse=True)
    return leaderboard

