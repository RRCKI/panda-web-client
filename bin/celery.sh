#!/usr/bin/env bash
source /srv/test/panda-web-client/venv/bin/activate
source setup.sh
celery worker -A webpanda.app.celery --loglevel=info --concurrency=2
