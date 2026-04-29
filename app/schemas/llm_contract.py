from pydantic import BaseModel
from typing import Optional, Dict, Any, List


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