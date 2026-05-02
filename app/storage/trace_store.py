import json
import time
from app.storage.redis_client import r


def _now():
    return time.time()


def _key(task_id: str):
    return f"trace:{task_id}"


def init_trace(task_id: str):
    r.set(_key(task_id), json.dumps([]))


def add_trace(task_id: str, step: str, data: dict = None):
    existing = r.get(_key(task_id))
    trace = json.loads(existing) if existing else []

    trace.append({
        "step": step,
        "data": data or {},
        "timestamp": _now()
    })
    
    r.set(_key(task_id), json.dumps(trace))


def get_trace(task_id: str):
    data = r.get(_key(task_id))
    return json.loads(data) if data else []


def clear_trace(task_id: str):
    r.delete(_key(task_id))