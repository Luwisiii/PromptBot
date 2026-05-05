import json
import time
from app.storage.redis_client import r


def _now():
    return time.time()


# -------------------------
# TASK STORAGE (UNCHANGED)
# -------------------------
def _save(task_id, data):
    r.setex(f"task:{task_id}", 3600, json.dumps(data))


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
# 🧠 SESSION STATE + DIFF SYSTEM
# -------------------------
SESSION_TTL = 1800  # 30 min


def _session_key(session_id: str):
    return f"session:{session_id}"


# -------------------------
# DIFF ENGINE (OPTION 2 CORE)
# -------------------------
def compute_diff(old: dict, new: dict) -> dict:
    diff = {}

    all_keys = set(old.keys()) | set(new.keys())

    for k in all_keys:
        old_val = old.get(k)
        new_val = new.get(k)

        if old_val != new_val:
            diff[k] = {
                "from": old_val,
                "to": new_val
            }

    return diff


# -------------------------
# LOAD SESSION
# -------------------------
def load_session(session_id: str):
    data = r.get(_session_key(session_id))
    if not data:
        return None

    return json.loads(data)


# -------------------------
# SAVE SESSION (WITH DIFF TRACKING)
# -------------------------
def save_session(session_id: str, state: dict):
    key = _session_key(session_id)
    
    existing = r.get(key)
    existing_data = json.loads(existing) if existing else {}

    old_state = existing_data.get("state", {})
    history = existing_data.get("history", [])
    
    diff = compute_diff(old_state, state)

    snapshot = {
        "state": state,
        "diff": diff,
        "timestamp": _now()
    }

    history.append(snapshot)
    
    history = history[-20:]

    payload = {
        "state": state,
        "history": history,
        "updated_at": _now()
    }

    r.setex(key, SESSION_TTL, json.dumps(payload))


# -------------------------
# CLEAR SESSION
# -------------------------
def clear_session(session_id: str):
    r.delete(_session_key(session_id))