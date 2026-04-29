import os
from celery import Celery

redis_url = os.getenv("REDIS_URL")

celery = Celery(
    "promptbot",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.processor"],
)

# Required for Upstash (TLS rediss://)
celery.conf.broker_use_ssl = {"ssl_cert_reqs": "none"}
celery.conf.redis_backend_use_ssl = {"ssl_cert_reqs": "none"}