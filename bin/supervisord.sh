#!/bin/bash
source ../.venv/bin/activate
source setup.sh
supervisord -c ../config/supervisord.conf