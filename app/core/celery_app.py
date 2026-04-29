from celery import Celery

celery = Celery(
    "promptbot",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.tasks.processor"]
)