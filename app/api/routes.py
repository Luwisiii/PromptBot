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
from app.services.intent import detect_intent

router = APIRouter()


@router.post("/assist")
async def assist(req: AssistRequest):

    session = load_session(req.session_id) if req.session_id else None
    intent = detect_intent(req.prompt, session)

    task_id = str(uuid.uuid4())
    init_task(task_id, req.model_dump())
    init_trace(task_id)

    try:
        # -----------------------------
        # 🧠 EDIT MODE
        # -----------------------------
        if intent == "EDIT_PROMPT":
            current_state = session

            decision = compile_prompt(
                req.prompt,
                edit_mode=True,
                state=current_state
            )

        # -----------------------------
        # 🆕 NEW PROMPT MODE
        # -----------------------------
        else:
            decision = compile_prompt(req.prompt, state=None)

        update_task(task_id, {"decision": decision})
        add_trace(task_id, "decision_ready", decision)

        # -----------------------------
        # 💾 SAVE FULL STATE
        # -----------------------------
        if req.session_id:
            save_session(
                session_id=req.session_id,
                state=decision.get("state", {})
            )

        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "decision": decision
        }

    except Exception as e:
        mark_failed(task_id, str(e))
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
    
@router.get("/session/{session_id}")
async def debug_session(session_id: str):
    from app.storage.redis_store import load_session
    return load_session(session_id)