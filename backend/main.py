import sys
import os

# Ensure project root is in sys.path so 'backend.*' imports work from anywhere
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_backend_dir, ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.health import router as health_router
from backend.routes.proxy import router as proxy_router
from backend.routes.agents import router as agents_router
from backend.routes.tasks import router as tasks_router
from backend.routes.benchmarks import router as benchmarks_router
from backend.routes.runs import router as runs_router
from backend.routes.leaderboard import router as leaderboard_router

app = FastAPI(
    title="AgentArena API",
    description="Benchmarking platform for AI coding agents with strict metering gateway",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route modules
app.include_router(health_router)
app.include_router(proxy_router)
app.include_router(agents_router)
app.include_router(tasks_router)
app.include_router(benchmarks_router)
app.include_router(runs_router)
app.include_router(leaderboard_router)


@app.get("/")
def root():
    return {
        "name": "AgentArena API",
        "status": "online",
        "endpoints": [
            "/health",
            "/agents",
            "/tasks",
            "/benchmarks",
            "/leaderboard",
            "/runs/{id}",
            "/llm/{run_id}/v1/chat/completions"
        ],
        "docs": "/docs"
    }
