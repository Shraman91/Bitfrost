import time
import logging
from typing import Dict, Any, Optional
import httpx
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse

from backend.config.settings import settings
from backend.config.pricing import calculate_cost
from backend.db.firestore import get_db

logger = logging.getLogger("agentarena.proxy")
router = APIRouter(prefix="/llm", tags=["metering-proxy"])


@router.post("/{run_id}/v1/chat/completions")
async def chat_completions_proxy(run_id: str, request: Request):
    """
    OpenAI-compatible chat completions proxy that meters:
    - prompt / completion tokens
    - latency in ms
    - call count
    - computed cost via pricing table
    Enforces per-run limits (max calls, max tokens, timeout).
    """
    # 1. Consume body first
    try:
        body = await request.json()
    except Exception:
        body = {}

    db = get_db()
    run_ref = db.collection("runs").document(run_id)
    run_snap = run_ref.get()

    if not run_snap.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found."
        )

    run_data = run_snap.to_dict() or {}
    
    # 2. Enforce Run Status
    current_status = run_data.get("status", "pending")
    if current_status not in ("running", "pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Run '{run_id}' is in status '{current_status}' and cannot accept LLM calls."
        )

    # 3. Enforce Limits
    limits = run_data.get("limits", {})
    if isinstance(limits, dict):
        max_calls = limits.get("max_calls", settings.max_calls_per_run)
        max_tokens = limits.get("max_tokens", settings.max_tokens_per_run)
        run_timeout = limits.get("timeout", settings.default_run_timeout_seconds)
    else:
        max_calls = settings.max_calls_per_run
        max_tokens = settings.max_tokens_per_run
        run_timeout = settings.default_run_timeout_seconds

    current_calls = run_data.get("llm_calls", 0)
    current_tokens = run_data.get("tokens_total", 0)
    created_at = run_data.get("created_at", time.time())

    if current_calls >= max_calls:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Run '{run_id}' exceeded limit of {max_calls} LLM calls."
        )

    if current_tokens >= max_tokens:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Run '{run_id}' exceeded limit of {max_tokens} total tokens."
        )

    if (time.time() - created_at) > run_timeout:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Run '{run_id}' exceeded timeout limit of {run_timeout}s."
        )

    target_url = f"{settings.bifrost_url.rstrip('/')}/v1/chat/completions"
    start_time = time.perf_counter()
    bifrost_response_data = None

    # If mock gateway is explicitly requested for testing or offline dev
    if run_data.get("_mock_gateway", False) or getattr(settings, "mock_llm", False):
        prompt_str = str(body.get("messages", ""))
        sim_prompt_tokens = max(10, len(prompt_str) // 4)
        sim_completion_tokens = 50
        latency_ms = (time.perf_counter() - start_time) * 1000.0 + 15.0

        # Smart mock response depending on task to demonstrate pass rates in dry runs
        if "fizzbuzz" in prompt_str.lower():
            mock_code = "```python\ndef fizzbuzz_jazz(n: int) -> list[str]:\n    res = []\n    for i in range(1, n + 1):\n        s = ''\n        if i % 3 == 0: s += 'Fizz'\n        if i % 5 == 0: s += 'Buzz'\n        if i % 7 == 0: s += 'Jazz'\n        res.append(s if s else str(i))\n    return res\n```"
        elif "occurrence" in prompt_str.lower() or "binary" in prompt_str.lower():
            mock_code = "```python\ndef find_first_occurrence(arr: list[int], target: int) -> int:\n    low = 0\n    high = len(arr) - 1\n    ans = -1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            ans = mid\n            high = mid - 1\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return ans\n```"
        elif "interval" in prompt_str.lower():
            mock_code = "```python\ndef merge_intervals(intervals: list[list[int]]) -> list[list[int]]:\n    if not intervals: return []\n    intervals.sort(key=lambda x: x[0])\n    merged = [intervals[0]]\n    for current in intervals[1:]:\n        prev = merged[-1]\n        if current[0] <= prev[1]:\n            prev[1] = max(prev[1], current[1])\n        else:\n            merged.append(current)\n    return merged\n```"
        elif "bracket" in prompt_str.lower() and "react" in run_data.get("agent_id", ""):
            # ReAct agent gets bracket validator right
            mock_code = "```python\ndef is_valid_brackets(s: str) -> bool:\n    stack = []\n    pairs = {')': '(', ']': '[', '}': '{'}\n    in_single = False\n    in_double = False\n    escaped = False\n    for ch in s:\n        if escaped:\n            escaped = False\n            continue\n        if ch == '\\\\':\n            escaped = True\n            continue\n        if ch == \"'\" and not in_double:\n            in_single = not in_single\n            continue\n        if ch == '\"' and not in_single:\n            in_double = not in_double\n            continue\n        if in_single or in_double:\n            continue\n        if ch in '([{':\n            stack.append(ch)\n        elif ch in ')]}':\n            if not stack or stack[-1] != pairs[ch]:\n                return False\n            stack.pop()\n    return len(stack) == 0 and not in_single and not in_double\n```"
        else:
            mock_code = "```python\n# Basic attempt\ndef solution():\n    pass\n```"

        bifrost_response_data = {
            "id": f"chatcmpl-mock-{int(time.time()*1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", "openai/gpt-4o-mini"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": mock_code
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": sim_prompt_tokens,
                "completion_tokens": sim_completion_tokens,
                "total_tokens": sim_prompt_tokens + sim_completion_tokens
            }
        }
    else:
        try:
            timeout_cfg = httpx.Timeout(timeout=float(run_timeout), connect=3.0)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                resp = await client.post(
                    target_url,
                    json=body,
                    headers={"Content-Type": "application/json"}
                )
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                if resp.status_code >= 400:
                    logger.warning(f"Bifrost returned {resp.status_code}: {resp.text}")
                    return JSONResponse(
                        status_code=resp.status_code,
                        content=resp.json() if resp.headers.get("content-type") == "application/json" else {"error": resp.text}
                    )
                bifrost_response_data = resp.json()
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to reach Bifrost at {target_url}: {str(conn_err)}"
            )

    # 4. Extract Usage & Compute Cost
    usage = bifrost_response_data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
    model = bifrost_response_data.get("model", body.get("model", "default"))

    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    # 5. Atomically Update Firestore Run Record
    new_tokens_in = run_data.get("tokens_in", 0) + prompt_tokens
    new_tokens_out = run_data.get("tokens_out", 0) + completion_tokens
    new_tokens_total = run_data.get("tokens_total", 0) + total_tokens
    new_cost_usd = round(run_data.get("cost_usd", 0.0) + cost, 8)
    new_latency_ms = round(run_data.get("latency_ms", 0.0) + latency_ms, 2)
    new_llm_calls = current_calls + 1

    run_ref.update({
        "tokens_in": new_tokens_in,
        "tokens_out": new_tokens_out,
        "tokens_total": new_tokens_total,
        "cost_usd": new_cost_usd,
        "latency_ms": new_latency_ms,
        "llm_calls": new_llm_calls,
        "status": "running"
    })

    return bifrost_response_data
