from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AgentTaskPayload(BaseModel):
    prompt: str
    files: Dict[str, str] = Field(default_factory=dict)


class AgentRunLimits(BaseModel):
    max_calls: int = 15
    max_tokens: int = 60000
    timeout: int = 60


class AgentRunRequest(BaseModel):
    run_id: str
    task: AgentTaskPayload
    llm_base_url: str
    llm_api_key: str
    model: str
    limits: AgentRunLimits = Field(default_factory=AgentRunLimits)


class AgentRunResponse(BaseModel):
    files: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = ""

