from typing import Dict, Any
import copy


class ValidationError(Exception):
    pass


def validate_and_sanitize(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    STRICT MODE:
    - NO auto-healing prompts
    - NO hallucination
    - ONLY structural validation
    """

    payload = copy.deepcopy(payload)

    payload = _normalize(payload)
    _validate_required_fields(payload)
    _validate_business_rules(payload)

    payload["validation_status"] = "valid"
    return payload


# ------------------------------
# NORMALIZATION
# ------------------------------
def _normalize(p: Dict[str, Any]) -> Dict[str, Any]:

    p.setdefault("extras", {})
    p.setdefault("negative_prompt", None)
    p.setdefault("style", None)

    if "type" not in p:
        raise ValidationError("Missing type")

    if p["type"] not in ["image", "video", "audio"]:
        raise ValidationError("Invalid type")

    if "prompt" not in p:
        raise ValidationError("Missing prompt")

    if not isinstance(p["prompt"], str):
        raise ValidationError("Invalid prompt type")

    # 🔥 STRICT BLOCK
    if not p["prompt"].strip():
        raise ValidationError("EMPTY_PROMPT_REJECTED")

    return p


# ------------------------------
# REQUIRED FIELDS
# ------------------------------
def _validate_required_fields(p: Dict[str, Any]):

    required = ["type", "prompt", "media", "quality"]

    for r in required:
        if r not in p:
            raise ValidationError(f"Missing required field: {r}")

    if not isinstance(p["media"], dict):
        raise ValidationError("media must be object")

    if not isinstance(p["quality"], dict):
        raise ValidationError("quality must be object")


# ------------------------------
# BUSINESS RULES
# ------------------------------
def _validate_business_rules(p: Dict[str, Any]):

    if p["type"] == "image":
        _validate_image(p)
    elif p["type"] == "video":
        _validate_video(p)
    elif p["type"] == "audio":
        _validate_audio(p)


def _validate_image(p):
    media = p["media"]
    quality = p["quality"]

    for r in ["resolution", "aspect_ratio", "format"]:
        if r not in media:
            raise ValidationError(f"Image missing media.{r}")

    quality["steps"] = min(quality.get("steps", 30), 100)
    quality["guidance"] = min(quality.get("guidance", 7.5), 20)


def _validate_video(p):
    media = p["media"]

    for r in ["resolution", "duration", "fps"]:
        if r not in media:
            raise ValidationError(f"Video missing media.{r}")

    media["duration"] = min(media.get("duration", 8), 60)
    media["fps"] = min(media.get("fps", 24), 60)


def _validate_audio(p):
    media = p["media"]

    for r in ["duration", "sample_rate"]:
        if r not in media:
            raise ValidationError(f"Audio missing media.{r}")

    if media.get("sample_rate") not in [22050, 44100, 48000]:
        media["sample_rate"] = 44100