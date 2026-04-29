from fastapi import APIRouter
import uuid

from app.schemas.contract import AssistRequest
from app.storage.redis_store import (
    init_task,
    set_processing,
    mark_failed,
    get_task,
    update_task
)

from app.storage.trace_store import init_trace, add_trace
from app.tasks.processor import process_task
from app.services.llm import compile_prompt

router = APIRouter()


@router.post("/assist")
async def assist(req: AssistRequest):

    task_id = str(uuid.uuid4())

    init_task(task_id, req.model_dump())
    init_trace(task_id)

    add_trace(task_id, "init_task", req.model_dump())

    try:
        compiled = compile_prompt(req.prompt, req.target)

        add_trace(task_id, "llm_compile", {"ok": True})

        # ✅ CLEAN SINGLE CONTRACT
        structured_payload = {
            "type": req.target,
            "prompt": req.prompt,
            "generation_prompt": compiled
        }

        update_task(task_id, {"compiled": structured_payload})
        add_trace(task_id, "compiled_ready")

        set_processing(task_id)
        add_trace(task_id, "processing_started")

        process_task.delay(task_id, structured_payload)

        add_trace(task_id, "queued")

        return {
            "task_id": task_id,
            "status": "PROCESSING"
        }

    except Exception as e:
        mark_failed(task_id, str(e))
        add_trace(task_id, "failed", {"error": str(e)})

        return {
            "task_id": task_id,
            "status": "FAILED",
            "error": str(e)
        }


@router.get("/result/{task_id}")
async def get_task_result(task_id: str):
    data = get_task(task_id)

    if not data:
        return {"task_id": task_id, "status": "NOT_FOUND"}

    return data


@router.get("/trace/{task_id}")
async def get_trace(task_id: str):

    from app.storage.trace_store import get_trace

    return {
        "task_id": task_id,
        "trace": get_trace(task_id)
    }