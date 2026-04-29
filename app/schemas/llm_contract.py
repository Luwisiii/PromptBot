from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any, List


class MediaSpec(BaseModel):
    type: Literal["image", "video", "audio"]
    prompt: str
    negative_prompt: Optional[str] = None
    style: Optional[str] = None

    media: Dict[str, Any]
    quality: Dict[str, Any]
    extras: Dict[str, Any]

    model_target: Optional[str] = None
    optimized_prompt: Optional[str] = None


# 🔥 NEW: USER-FACING PROMPT INTELLIGENCE OUTPUT
class GenerationPrompt(BaseModel):
    task: str
    goal: str
    identity_handling: Optional[Dict[str, Any]] = None
    scene: Dict[str, Any]
    environment: Optional[Dict[str, Any]] = None
    lighting: Optional[Dict[str, Any]] = None
    camera: Optional[Dict[str, Any]] = None
    style: Optional[Dict[str, Any]] = None
    generation_prompt: Dict[str, Any]
    variants: Optional[List[Dict[str, Any]]] = None