from fastapi import APIRouter
import uuid

from app.schemas.contract import AssistRequest
from app.storage.redis_store import (
    init_task,
    mark_failed,
    get_task,
    update_task,
    load_session,
    save_session
)

from app.storage.trace_store import init_trace, add_trace
from app.services.llm import compile_prompt

router = APIRouter()


# -----------------------------
# DOMAIN GATE
# -----------------------------
def classify_prompt_intent(text: str) -> str:
    t = text.lower().strip()

    multimedia_hints = [
        "image", "photo", "picture", "art", "illustration",
        "video", "cinematic", "film", "scene", "shot",
        "audio", "sound", "music", "voice",
    ]

    generation_verbs = [
        "make", "create", "generate", "build", "design", "write", "craft"
    ]

    if any(v in t for v in generation_verbs) or "prompt" in t:
        if any(h in t for h in multimedia_hints):
            return "proceed"
        return "ask_intent"

    if any(h in t for h in multimedia_hints):
        return "proceed"

    return "reject"


# -----------------------------
# ASSIST ENDPOINT
# -----------------------------
@router.post("/assist")
async def assist(req: AssistRequest):

    intent = classify_prompt_intent(req.prompt)

    if intent == "reject":
        return {
            "action": "respond",
            "message": "This PromptBot is for multimedia prompt creation. Ask for image, video, or audio prompts.",
            "data": None
        }

    if intent == "ask_intent":
        return {
            "action": "ask",
            "message": "What type of prompt would you like? (image, video, or audio)",
            "data": None
        }

    # -----------------------------
    # TASK INIT
    # -----------------------------
    task_id = str(uuid.uuid4())

    init_task(task_id, req.model_dump())
    init_trace(task_id)
    add_trace(task_id, "init_task", req.model_dump())

    try:

        # -----------------------------
        # SESSION MEMORY LOAD
        # -----------------------------
        final_prompt = req.prompt

        if req.session_id:
            session = load_session(req.session_id)

            if session and isinstance(session, dict):
                last_prompt = session.get("last_prompt")

                if last_prompt:
                    final_prompt = f"""
You are editing a previously generated prompt.

=== PREVIOUS PROMPT ===
{last_prompt}

=== USER MODIFICATION ===
{req.prompt}

Rules:
- Only modify what is necessary
- Keep structure consistent
- Preserve style and quality
"""
                    add_trace(task_id, "memory_applied", {
                        "last_prompt": last_prompt,
                        "user_input": req.prompt
                    })

        # -----------------------------
        # LLM CALL
        # -----------------------------
        decision = compile_prompt(final_prompt)

        update_task(task_id, {"decision": decision})
        add_trace(task_id, "decision_ready", decision)

        # -----------------------------
        # SESSION SAVE (IMPORTANT FIX)
        # -----------------------------
        if req.session_id:
            save_session(
            session_id=req.session_id,
            last_prompt=decision.get("message", ""),
            decision=decision
        )

            add_trace(task_id, "memory_saved", {
                "session_id": req.session_id
            })

        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "decision": decision
        }

    except Exception as e:
        mark_failed(task_id, str(e))
        add_trace(task_id, "failed", {"error": str(e)})

        return {
            "task_id": task_id,
            "status": "FAILED",
            "error": str(e)
        }


# -----------------------------
# RESULT ENDPOINT
# -----------------------------
@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    data = get_task(task_id)

    if not data:
        return {"task_id": task_id, "status": "NOT_FOUND"}

    return data


# -----------------------------
# TRACE ENDPOINT
# -----------------------------
@router.get("/trace/{task_id}")
async def get_trace_result(task_id: str):
    from app.storage.trace_store import get_trace

    return {
        "task_id": task_id,
        "trace": get_trace(task_id)
    }