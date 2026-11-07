from typing import Dict, Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str = Field(..., description="Unique task identifier, e.g. lru-cache")
    title: str = Field(..., description="Human-readable title")
    difficulty: str = Field(default="medium", description="easy | medium | hard")
    timeout: int = Field(default=10, description="Test execution timeout in seconds")
    prompt: str = Field(..., description="Detailed instructions for the agent")
    starter_files: Dict[str, str] = Field(default_factory=dict, description="File paths and initial contents")
    hidden_tests: str = Field(..., description="Unit test script that tests the generated code")

