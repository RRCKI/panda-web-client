#!/bin/bash
source ../venv/bin/activate
source setup.sh
supervisord -c /srv/test/panda-web-client/config/supervisord.conf