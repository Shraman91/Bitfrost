from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
import time


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class RunLimits(BaseModel):
    max_calls: int = 15
    max_tokens: int = 60000
    timeout: int = 60


class Run(BaseModel):
    id: str
    benchmark_id: str
    agent_id: str
    task_id: str
    model: str
    status: RunStatus = RunStatus.PENDING
    passed: bool = False
    score: float = 0.0
    passed_tests: int = 0
    total_tests: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    llm_calls: int = 0
    error: Optional[str] = None
    files: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = None
    test_output: Optional[str] = None
    limits: RunLimits = Field(default_factory=RunLimits)
    created_at: float = Field(default_factory=time.time)
    finished_at: Optional[float] = None

