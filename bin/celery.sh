#!/usr/bin/env bash
source ../.venv/bin/activate
source setup.sh
celery worker -A webpanda.async.celery --loglevel=info --concurrency=2
