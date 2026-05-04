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


class PromptState(BaseModel):
    subject: Optional[str] = None
    composition: Optional[str] = None
    scene: Optional[str] = None
    style: Optional[list[str]] = None
    mood: Optional[str] = None
    prompt: Optional[str] = None

    class Config:
        extra = "forbid"


class CopilotDecision(BaseModel):
    action: Literal["ask", "respond", "structured"]
    state: Optional[PromptState] = None
    data: Optional[Dict[str, Any]] = None

    class Config:
        extra = "forbid"