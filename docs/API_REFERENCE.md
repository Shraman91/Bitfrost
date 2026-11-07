# AgentArena REST API Reference

The AgentArena backend exposes a comprehensive RESTful API alongside Server-Sent Events (SSE) for live streaming progress.

**Base URL**: `http://localhost:8000`  
**Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 1. Health

### `GET /health`
Verifies backend status, Bifrost gateway reachability, and database connectivity.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "bifrost": {
    "reachable": true,
    "url": "http://localhost:8080",
    "error": null
  },
  "database": {
    "connected": true,
    "type": "MockFirestoreClient"
  }
}
```

---

## 2. Metering Proxy

### `POST /llm/{run_id}/v1/chat/completions`
OpenAI-compatible chat completion proxy. All agent LLM calls must flow through this endpoint.

**Path Parameters**:
- `run_id`: The ID of the currently executing benchmark run.

**Request Body**: Standard OpenAI chat completions payload (`model`, `messages`, `temperature`, `max_tokens`, etc.).

**Behavior**:
- Verifies run exists and status is `running` or `pending`.
- Enforces `max_calls`, `max_tokens`, and timeout limits.
- Forwards request to Bifrost (`http://localhost:8080/v1/chat/completions`).
- Atomically records tokens in/out, computed cost in USD, and latency in ms into Firestore under `runs/{run_id}`.
- Returns Bifrost's OpenAI-compatible response unchanged.

---

## 3. Agents

### `GET /agents`
List all registered agents (both built-in and external).

**Response `200 OK`**:
```json
[
  {
    "id": "naive",
    "name": "Naive Single-Prompt",
    "type": "builtin",
    "model": "openai/gpt-4o-mini",
    "description": "Single-turn prompt asking LLM to generate code in one shot.",
    "endpoint": null,
    "created_at": 1731000000.0
  }
]
```

### `GET /agents/{id}`
Retrieve a specific agent by ID.

### `POST /agents`
Register a new external HTTP agent.

**Request Body**:
```json
{
  "name": "LangChain ReAct Agent",
  "type": "external_http",
  "endpoint": "http://localhost:8001/run",
  "model": "openai/gpt-4o-mini",
  "description": "Custom agent with tool execution"
}
```

### `PUT /agents/{id}`
Update an existing agent's configuration.

### `DELETE /agents/{id}`
Delete an agent from the registry.

### `POST /agents/test-connection`
Test connectivity to an external agent endpoint.

**Request Body**:
```json
{
  "endpoint": "http://localhost:8001/run"
}
```

**Response `200 OK`**:
```json
{
  "success": true,
  "status_code": 200,
  "latency_ms": 14.5,
  "message": "Endpoint reachable (HTTP 200)"
}
```

---

## 4. Tasks

### `GET /tasks`
List all available benchmark tasks.

**Response `200 OK`**:
```json
[
  {
    "id": "fizzbuzz-jazz",
    "title": "FizzBuzz Jazz",
    "difficulty": "easy",
    "timeout": 10,
    "prompt": "Implement the function fizzbuzz_jazz...",
    "starter_files": {"solution.py": "..."},
    "created_at": 1731000000.0
  }
]
```

### `GET /tasks/{id}`
Retrieve a task by ID.

---

## 5. Benchmarks

### `POST /benchmarks`
Create and launch a new benchmark suite across agents and tasks.

**Request Body**:
```json
{
  "agent_ids": ["naive", "react-lite", "token-saver"],
  "task_ids": ["fizzbuzz-jazz", "parse-csv", "lru-cache"],
  "model": "openai/gpt-4o-mini"
}
```

**Response `200 OK`**:
```json
{
  "id": "bench_1731000000000",
  "agent_ids": ["naive", "react-lite", "token-saver"],
  "task_ids": ["fizzbuzz-jazz", "parse-csv", "lru-cache"],
  "model": "openai/gpt-4o-mini",
  "status": "running",
  "total_runs": 9,
  "completed_runs": 0,
  "created_at": 1731000000.0
}
```

### `GET /benchmarks/{id}`
Retrieve benchmark status and all associated evaluation runs.

### `GET /benchmarks/{id}/live`
Server-Sent Events (SSE) stream providing real-time events (`run_started`, `run_completed`, `benchmark_progress`).

---

## 6. Runs

### `GET /runs/{id}`
Retrieve full run evaluation details, generated files, sandbox test outputs, and token/cost metrics.

**Response `200 OK`**:
```json
{
  "run": {
    "id": "run_naive_fizzbuzz-jazz_1731000000",
    "benchmark_id": "bench_1731000000000",
    "agent_id": "naive",
    "task_id": "fizzbuzz-jazz",
    "model": "openai/gpt-4o-mini",
    "status": "completed",
    "passed": true,
    "score": 1.0,
    "passed_tests": 5,
    "total_tests": 5,
    "tokens_in": 128,
    "tokens_out": 85,
    "tokens_total": 213,
    "cost_usd": 0.0000702,
    "latency_ms": 420.5,
    "llm_calls": 1,
    "files": {"solution.py": "..."},
    "test_output": "Ran 5 tests in 0.002s\n\nOK"
  },
  "task": {
    "id": "fizzbuzz-jazz",
    "title": "FizzBuzz Jazz"
  }
}
```

---

## 7. Leaderboard

### `GET /leaderboard`
Aggregated leaderboard ranking agents by **Efficiency Score**, **Pass Rate**, and economic cost.

**Response `200 OK`**:
```json
[
  {
    "agent_id": "token-saver",
    "agent_name": "Token-Saver",
    "agent_type": "builtin",
    "model": "openai/gpt-4o-mini",
    "total_runs": 10,
    "passed_runs": 9,
    "pass_rate": 90.0,
    "avg_score": 0.900,
    "avg_tokens": 145.2,
    "avg_tokens_in": 90.0,
    "avg_tokens_out": 55.2,
    "avg_cost_usd": 0.000045,
    "avg_latency_ms": 280.1,
    "avg_llm_calls": 1.0,
    "efficiency_score": 1783.5
  }
]
```
