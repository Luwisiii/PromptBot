#!/usr/bin/env bash

echo "REDIS CHECK: $REDIS_URL"

celery -A app.core.celery_app worker --loglevel=info &

uvicorn app.main:app --host 0.0.0.0 --port 10000