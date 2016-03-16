#!/usr/bin/env bash
source /srv/test/panda-web-client/venv/bin/activate
source setup.sh
celery worker -A webpanda.tasks.celery --loglevel=info --concurrency=2
