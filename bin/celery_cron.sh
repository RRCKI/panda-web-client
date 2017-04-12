#!/usr/bin/env bash

source ../.venv/bin/activate
source setup.sh
celery -A webpanda.async.celery beat
