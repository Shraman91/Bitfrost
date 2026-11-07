from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import time


class AgentType(str, Enum):
    BUILTIN = "builtin"
    EXTERNAL_HTTP = "external_http"


class AgentBase(BaseModel):
    name: str = Field(..., description="Display name of the agent")
    type: AgentType = Field(default=AgentType.EXTERNAL_HTTP, description="builtin or external_http")
    endpoint: Optional[str] = Field(default=None, description="HTTP endpoint for external agents, e.g. http://localhost:8001/run")
    model: str = Field(default="openai/gpt-4o-mini", description="Target LLM model addressed as provider/model")
    description: Optional[str] = Field(default="", description="Description of the agent's strategy or framework")


class AgentCreate(AgentBase):
    id: Optional[str] = Field(default=None, description="Optional custom ID (e.g. naive, react-lite)")


class Agent(AgentBase):
    id: str
    created_at: float = Field(default_factory=time.time)

