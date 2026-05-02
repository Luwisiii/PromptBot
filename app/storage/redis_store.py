import json
import time
from app.storage.redis_client import r


def _now():
    return time.time()


# -------------------------
# TASK STORAGE
# -------------------------
def _save(task_id, data):
    r.setex(f"task:{task_id}", 3600, json.dumps(data))  # TTL added


def get_task(task_id):
    data = r.get(f"task:{task_id}")
    return json.loads(data) if data else None


def update_task(task_id, patch: dict):
    data = get_task(task_id)

    if not data:
        return

    data.update(patch)
    data["updated_at"] = _now()
    _save(task_id, data)


def init_task(task_id, data):
    payload = {
        "task_id": task_id,
        "status": "PENDING",
        "created_at": _now(),
        "updated_at": _now(),
        "input": {"raw": data},
        "compiled": None,
        "output": None,
        "error": None
    }
    
    _save(task_id, payload)


def set_processing(task_id):
    update_task(task_id, {"status": "PROCESSING"})


def save_result(task_id, result):
    update_task(task_id, {
        "status": "SUCCESS",
        "output": {
            "result": result,
            "generated_at": _now()
        },
        "error": None
    })


def mark_failed(task_id, error):
    update_task(task_id, {
        "status": "FAILED",
        "error": str(error)
    })


# -------------------------
# SESSION MEMORY (FIXED)
# -------------------------
SESSION_TTL = 1800  # 30 min


def _session_key(session_id: str):
    return f"session:{session_id}"


def load_session(session_id: str):
    data = r.get(_session_key(session_id))
    return json.loads(data) if data else None


def save_session(session_id: str, last_prompt: str, decision: dict = None):
    payload = {
        "last_prompt": last_prompt,
        "last_decision": decision,
        "updated_at": _now()
    }

    r.setex(_session_key(session_id), SESSION_TTL, json.dumps(payload))


def clear_session(session_id: str):
    r.delete(_session_key(session_id))