#!/usr/bin/env bash

cd  /srv/test2/panda-web-client/bin/
source ../.venv/bin/activate
source setup.sh
celery worker -A webpanda.async.celery --loglevel=info --concurrency=2
