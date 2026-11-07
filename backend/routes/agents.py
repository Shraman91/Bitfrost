import time
import httpx
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.db.firestore import get_db
from backend.models.agent import Agent, AgentCreate, AgentType

router = APIRouter(prefix="/agents", tags=["agents"])


class ConnectionTestRequest(BaseModel):
    endpoint: str


class ConnectionTestResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    message: str


@router.get("", response_model=List[Agent])
def list_agents():
    db = get_db()
    docs = db.collection("agents").stream()
    return [Agent(**doc.to_dict()) for doc in docs]


@router.get("/{agent_id}", response_model=Agent)
def get_agent(agent_id: str):
    db = get_db()
    doc = db.collection("agents").document(agent_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Agent not found")
    return Agent(**doc.to_dict())


@router.post("", response_model=Agent)
def create_agent(agent_in: AgentCreate):
    db = get_db()
    agent_id = agent_in.id or f"agent-{int(time.time() * 1000)}"
    
    agent = Agent(
        id=agent_id,
        name=agent_in.name,
        type=agent_in.type,
        endpoint=agent_in.endpoint,
        model=agent_in.model,
        description=agent_in.description,
        created_at=time.time()
    )
    
    db.collection("agents").document(agent_id).set(agent.model_dump())
    return agent


@router.put("/{agent_id}", response_model=Agent)
def update_agent(agent_id: str, agent_in: AgentCreate):
    db = get_db()
    doc_ref = db.collection("agents").document(agent_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Agent not found")

    existing = doc.to_dict()
    updated = {
        **existing,
        "name": agent_in.name,
        "type": agent_in.type,
        "endpoint": agent_in.endpoint,
        "model": agent_in.model,
        "description": agent_in.description,
    }
    doc_ref.set(updated)
    return Agent(**updated)


@router.delete("/{agent_id}")
def delete_agent(agent_id: str):
    db = get_db()
    doc_ref = db.collection("agents").document(agent_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Agent not found")
    doc_ref.delete()
    return {"status": "deleted", "id": agent_id}


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_agent_connection(req: ConnectionTestRequest):
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(
                req.endpoint,
                json={"ping": True, "task": {"prompt": "ping"}}
            )
            latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            # Accept any 2xx or 4xx (endpoint is alive and responded)
            if resp.status_code < 500:
                return ConnectionTestResponse(
                    success=True,
                    status_code=resp.status_code,
                    latency_ms=latency_ms,
                    message=f"Endpoint reachable (HTTP {resp.status_code})"
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    status_code=resp.status_code,
                    latency_ms=latency_ms,
                    message=f"Endpoint returned server error HTTP {resp.status_code}"
                )
    except Exception as e:
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return ConnectionTestResponse(
            success=False,
            latency_ms=latency_ms,
            message=f"Connection failed: {str(e)}"
        )

