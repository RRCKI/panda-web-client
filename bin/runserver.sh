#!/bin/bash
source ../.venv/bin/activate
source ./setup.sh
echo $PYTHONPATH
python ../webpanda/webpanda.wsgi