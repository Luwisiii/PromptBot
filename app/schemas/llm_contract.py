from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any


class MediaSpec(BaseModel):
    type: Literal["image", "video", "audio"]
    prompt: str
    negative_prompt: Optional[str] = None
    style: Optional[str] = None

    media: Dict[str, Any]
    quality: Dict[str, Any]
    extras: Dict[str, Any]

    # 🔥 Phase 5 (optional future use)
    model_target: Optional[str] = None
    optimized_prompt: Optional[str] = None