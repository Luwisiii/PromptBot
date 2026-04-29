import json
import time
import redis
from app.core.config import REDIS_URL

# ✅ FIX: use Render / Upstash Redis instead of localhost
r = redis.from_url(REDIS_URL, decode_responses=True)


def _now():
    return time.time()


def _save(task_id, data):
    r.set(f"task:{task_id}", json.dumps(data))


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
    update_task(task_id, {
        "status": "PROCESSING"
    })


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