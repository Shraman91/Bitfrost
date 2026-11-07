# AgentArena Agent Contract Specification

The **AgentArena Contract** defines a framework-agnostic protocol that any AI coding agent must implement to be benchmarked on AgentArena.

---

## 1. Overview

AgentArena treats agents as black-box HTTP microservices. Whether built with LangChain, AutoGen, CrewAI, LlamaIndex, Smolagents, or custom Python/TypeScript scripts, any agent can be tested as long as it exposes an HTTP endpoint conforming to this contract.

```
AgentArena Orchestrator ─── POST {endpoint}/run ───> Your Agent
Your Agent ─── POST {llm_base_url}/chat/completions ───> Metering Proxy ───> Bifrost
```

---

## 2. Endpoint Specification

### `POST {agent_endpoint}/run`

#### Request Body
The orchestrator sends a JSON payload with the task details, metered LLM gateway URL, and limits:

```json
{
  "run_id": "run_naive_fizzbuzz-jazz_1731000000",
  "task": {
    "prompt": "Implement the function `fizzbuzz_jazz(n: int) -> list[str]` in `solution.py`.\n\nRules:\n- Multiples of 3: 'Fizz'\n- Multiples of 5: 'Buzz'\n- Multiples of 7: 'Jazz'\n- Multiples of combinations concatenate in order (e.g., 15 -> 'FizzBuzz', 105 -> 'FizzBuzzJazz').\n- Otherwise string representation of the number.",
    "files": {
      "solution.py": "def fizzbuzz_jazz(n: int) -> list[str]:\n    # Implement here\n    pass\n"
    }
  },
  "llm_base_url": "http://localhost:8000/llm/run_naive_fizzbuzz-jazz_1731000000/v1",
  "llm_api_key": "arena-benchmark-token",
  "model": "openai/gpt-4o-mini",
  "limits": {
    "max_calls": 15,
    "max_tokens": 60000,
    "timeout": 30
  }
}
```

#### Fields Description

| Field | Type | Description |
|---|---|---|
| `run_id` | `string` | Unique identifier for this evaluation run. |
| `task.prompt` | `string` | Human-readable instruction and specification of the coding task. |
| `task.files` | `object` | Mapping of filename to file content for starter code/templates. |
| `llm_base_url` | `string` | **Crucial:** OpenAI-compatible API base URL for this run. |
| `llm_api_key` | `string` | Bearer token to include in the `Authorization` header. |
| `model` | `string` | Target model identifier in `provider/model` format (e.g. `openai/gpt-4o-mini`). |
| `limits.max_calls` | `integer` | Maximum LLM calls allowed before the proxy returns `429`. |
| `limits.max_tokens` | `integer` | Maximum total tokens allowed before the proxy returns `429`. |
| `limits.timeout` | `integer` | Maximum overall timeout in seconds for this run. |

---

## 3. The Golden Rule of LLM Calls

> [!CAUTION]
> **Every single LLM API call made by your agent MUST be directed to `llm_base_url + "/chat/completions"`.**

If your agent calls OpenAI, Anthropic, or any other provider directly using their standard public URLs, those calls **will not be metered**, and your agent will register `0 tokens`, `0 cost`, and will be disqualified or fail limit validation.

### Example Using the Official `openai` Python SDK
```python
from openai import OpenAI

client = OpenAI(
    base_url=request_payload["llm_base_url"],
    api_key=request_payload["llm_api_key"]
)

response = client.chat.completions.create(
    model=request_payload["model"],
    messages=[{"role": "user", "content": request_payload["task"]["prompt"]}]
)
```

---

## 4. Response Format

Your agent must return a JSON response with the generated/modified files:

```json
{
  "files": {
    "solution.py": "def fizzbuzz_jazz(n: int) -> list[str]:\n    result = []\n    for i in range(1, n + 1):\n        s = ''\n        if i % 3 == 0: s += 'Fizz'\n        if i % 5 == 0: s += 'Buzz'\n        if i % 7 == 0: s += 'Jazz'\n        result.append(s if s else str(i))\n    return result\n"
  },
  "notes": "Completed in 1 LLM iteration using standard greedy assembly."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | `object` | **Yes** | Key-value dictionary where keys are relative file paths (e.g. `solution.py`) and values are the complete file contents. |
| `notes` | `string` | No | Optional notes or reasoning summaries to display in the run inspector. |

---

## 5. Health Check & Ping

When an agent is registered in the UI (`/agents`), AgentArena sends a connectivity ping:
```json
POST {agent_endpoint}/run
{
  "ping": true,
  "task": {"prompt": "ping"}
}
```
Your endpoint should return an HTTP `200` status with `{}` or `{"status": "ok"}`.
