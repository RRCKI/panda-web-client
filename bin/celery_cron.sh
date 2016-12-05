#!/usr/bin/env bash

cd /srv/test2/panda-web-client/bin/
source ../.venv/bin/activate
source setup.sh
celery -A webpanda.async.celery beat
