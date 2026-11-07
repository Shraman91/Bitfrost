import pytest
import time
import httpx
from backend.main import app
from backend.db.firestore import get_db

@pytest.mark.asyncio
async def test_proxy_run_not_found():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/llm/nonexistent_run_123/v1/chat/completions",
            json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_proxy_limits_enforced():
    db = get_db()
    run_id = "test_run_limits"
    db.collection("runs").document(run_id).set({
        "id": run_id,
        "benchmark_id": "bench_1",
        "agent_id": "naive",
        "task_id": "task_1",
        "model": "openai/gpt-4o-mini",
        "status": "running",
        "llm_calls": 2,
        "tokens_total": 100,
        "limits": {"max_calls": 2, "max_tokens": 1000, "timeout": 60},
        "created_at": time.time()
    })

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/llm/{run_id}/v1/chat/completions",
            json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "hello"}]}
        )
        assert response.status_code == 429
        assert "exceeded limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_proxy_forwards_and_records_usage():
    db = get_db()
    run_id = "test_run_forwarding"
    db.collection("runs").document(run_id).set({
        "id": run_id,
        "benchmark_id": "bench_1",
        "agent_id": "naive",
        "task_id": "task_1",
        "model": "openai/gpt-4o-mini",
        "status": "running",
        "llm_calls": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "tokens_total": 0,
        "cost_usd": 0.0,
        "latency_ms": 0.0,
        "limits": {"max_calls": 10, "max_tokens": 10000, "timeout": 60},
        "created_at": time.time(),
        "_mock_gateway": True
    })

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            f"/llm/{run_id}/v1/chat/completions",
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": "Implement FizzBuzz in Python"}]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert "usage" in data
        assert data["usage"]["prompt_tokens"] > 0
        assert data["usage"]["completion_tokens"] > 0

        # Verify Firestore document was updated
        updated_run = db.collection("runs").document(run_id).get().to_dict()
        assert updated_run["llm_calls"] == 1
        assert updated_run["tokens_in"] == data["usage"]["prompt_tokens"]
        assert updated_run["tokens_out"] == data["usage"]["completion_tokens"]
        assert updated_run["tokens_total"] == data["usage"]["total_tokens"]
        assert updated_run["cost_usd"] > 0.0
        assert updated_run["latency_ms"] >= 0.0
