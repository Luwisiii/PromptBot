from pydantic import BaseModel, field_validator
from typing import Literal, Optional, Dict, Any


class AssistRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    
    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("prompt cannot be empty")
        return v.strip()


class CopilotDecision(BaseModel):
    action: Literal["ask", "respond", "structured"]
    message: str
    data: Optional[Dict[str, Any]] = None