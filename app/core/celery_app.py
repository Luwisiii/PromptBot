from app.core.config import REDIS_URL
from celery import Celery

if not REDIS_URL:
    raise ValueError("REDIS_URL is missing")

celery = Celery(
    "promptbot",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.processor"],
)

celery.conf.broker_use_ssl = {"ssl_cert_reqs": "none"}
celery.conf.redis_backend_use_ssl = {"ssl_cert_reqs": "none"}