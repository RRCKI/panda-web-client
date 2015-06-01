#!/usr/bin/env bash
source setup.sh
cd ..
venv/bin/python webpanda/mq/consumer.py webpanda.job

