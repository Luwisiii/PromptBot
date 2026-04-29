from pydantic import BaseModel, field_validator
from typing import Literal


class AssistRequest(BaseModel):
    prompt: str
    target: Literal["image", "video", "audio"]

    # 🔥 STRICT MODE: reject empty / whitespace prompts
    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v):
        if not isinstance(v, str) or not v.strip():
            raise ValueError("prompt cannot be empty")
        return v.strip()


class AssistResponse(BaseModel):
    task_id: str
    status: str