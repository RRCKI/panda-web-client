#!/usr/bin/env bash
source ../venv/bin/activate
source setup.sh
celery worker -A webpanda.app.celery --loglevel=info