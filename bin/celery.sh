#!/usr/bin/env bash
source ../venv/bin/activate
source setup.sh
celery worker -A app.celery --loglevel=info