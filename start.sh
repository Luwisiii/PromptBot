#!/usr/bin/env bash

echo "REDIS CHECK: $REDIS_URL"

uvicorn app.main:app --host 0.0.0.0 --port 10000