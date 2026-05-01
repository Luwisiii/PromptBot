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
from app.services.llm import compile_prompt

router = APIRouter()


@router.post("/assist")
async def assist(req: AssistRequest):

    task_id = str(uuid.uuid4())

    init_task(task_id, req.model_dump())
    init_trace(task_id)
    add_trace(task_id, "init_task", req.model_dump())

    try:
        decision = compile_prompt(req.prompt)

        update_task(task_id, {"decision": decision})
        add_trace(task_id, "decision_ready", decision)

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