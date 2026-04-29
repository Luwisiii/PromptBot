from app.core.celery_app import celery
from app.storage.redis_store import (
    save_result,
    set_processing,
    mark_failed
)

from app.storage.trace_store import add_trace

from app.services.prompt_optimizer import (
    optimize_image,
    optimize_video,
    optimize_audio
)

from app.services.model_router import route_model
from app.services.safety_validator import validate_and_sanitize

import time
import re


def score_prompt(prompt: str) -> float:
    if not prompt or not prompt.strip():
        return 0.0

    prompt = prompt.strip()
    score = 0.5

    if len(prompt) > 10:
        score += 0.1
    if len(prompt) > 30:
        score += 0.1

    keywords = [
        "cinematic", "detailed", "lighting", "neon",
        "wide shot", "photorealistic", "ultra", "volumetric"
    ]

    for k in keywords:
        if k in prompt.lower():
            score += 0.05

    if re.match(r"^[^a-zA-Z]+$", prompt):
        score -= 0.4

    return max(0.0, min(1.0, score))


def boost_prompt(prompt: str, score: float, media_type: str) -> str:
    if not prompt or not prompt.strip():
        return ""

    if score >= 0.7:
        return prompt

    if media_type == "image":
        return f"{prompt}, ultra detailed, cinematic lighting"

    if media_type == "video":
        return f"{prompt}, cinematic motion, smooth camera movement"

    if media_type == "audio":
        return f"{prompt}, studio quality audio"

    return prompt


@celery.task(bind=True, max_retries=3)
def process_task(self, task_id, structured_payload):

    try:
        set_processing(task_id)
        add_trace(task_id, "processing_started")
        time.sleep(1.5)

        # =========================
        # VALIDATION
        # =========================
        structured_payload = validate_and_sanitize(structured_payload)
        add_trace(task_id, "validated")

        t = structured_payload["type"]
        prompt = structured_payload.get("prompt", "")

        # =========================
        # SCORING (PHASE 9.5)
        # =========================
        score = score_prompt(prompt)
        structured_payload["prompt_score"] = score

        add_trace(task_id, "prompt_scored", {"score": score})

        prompt = boost_prompt(prompt, score, t)
        structured_payload["prompt"] = prompt

        add_trace(task_id, "prompt_boosted")

        # =========================
        # ROUTING
        # =========================
        structured_payload = route_model(structured_payload)

        add_trace(task_id, "routed", {
            "model_target": structured_payload.get("model_target")
        })

        if not structured_payload.get("model_target"):
            structured_payload["model_target"] = "sdxl"

        # =========================
        # OPTIMIZATION
        # =========================
        style = structured_payload.get("style")
        extras = structured_payload.get("extras", {})

        if t == "image":
            optimized = optimize_image(prompt, style, extras)
        elif t == "video":
            optimized = optimize_video(prompt, style, extras)
        elif t == "audio":
            optimized = optimize_audio(prompt, style, extras)
        else:
            optimized = prompt

        structured_payload["optimized_prompt"] = optimized

        add_trace(task_id, "optimized")

        # =========================
        # FINAL VALIDATION
        # =========================
        structured_payload = validate_and_sanitize(structured_payload)
        add_trace(task_id, "final_validation")

        # =========================
        # RESULT
        # =========================
        result = {
            "task_id": task_id,
            "type": t,
            "model_target": structured_payload["model_target"],
            "input": {
                "prompt": prompt,
                "optimized_prompt": optimized,
                "prompt_score": score
            },
            "model_config": structured_payload.get("model_config", {}),
            "output": {
                "mock": True,
                "message": f"Routed to {structured_payload['model_target']}"
            },
            "metadata": {
                "phase": "phase-10-trace-enabled",
                "validation_status": structured_payload.get("validation_status"),
                "prompt_score": score
            }
        }

        save_result(task_id, result)
        add_trace(task_id, "completed")

        return {"task_id": task_id, "status": "SUCCESS"}

    except Exception as e:

        add_trace(task_id, "error", {"error": str(e)})

        if self.request.retries >= self.max_retries:
            mark_failed(task_id, str(e))
            raise

        raise self.retry(countdown=2, exc=e)