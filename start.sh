#!/usr/bin/env bash

echo "REDIS_URL=$REDIS_URL"

# wait a moment for env to be ready
sleep 3

# start celery in background
celery -A app.core.celery_app worker --loglevel=info &

# start fastapi
uvicorn app.main:app --host 0.0.0.0 --port 10000