import os
from celery import Celery

redis_url = os.environ.get("REDIS_URL")

if not redis_url:
    raise ValueError("REDIS_URL is missing")

celery = Celery(
    "promptbot",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.processor"],
)

celery.conf.broker_use_ssl = {"ssl_cert_reqs": "none"}
celery.conf.redis_backend_use_ssl = {"ssl_cert_reqs": "none"}