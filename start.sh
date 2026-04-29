#!/usr/bin/env bash

# start celery in background
celery -A app.core.celery_app worker --loglevel=info &

# start fastapi
uvicorn app.main:app --host 0.0.0.0 --port 10000