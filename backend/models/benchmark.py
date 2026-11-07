from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
import time


class BenchmarkStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BenchmarkCreate(BaseModel):
    agent_ids: List[str] = Field(..., min_length=1, description="Agents to benchmark")
    task_ids: List[str] = Field(..., min_length=1, description="Tasks to run agents on")
    model: Optional[str] = Field(default=None, description="Optional override model for all runs")


class Benchmark(BaseModel):
    id: str
    agent_ids: List[str]
    task_ids: List[str]
    model: Optional[str] = None
    status: BenchmarkStatus = BenchmarkStatus.PENDING
    total_runs: int = 0
    completed_runs: int = 0
    created_at: float = Field(default_factory=time.time)
    finished_at: Optional[float] = None

