#!/bin/bash
source /Users/it/sources/1_BIO/panda-web-client/.venv/bin/activate
PYTHONPATH=/Users/it/sources/1_BIO/panda-web-client:$PYTHONPATH
PYTHONPATH=/Users/it/sources/1_BIO/panda-server/pandaserver:$PYTHONPATH
echo $PYTHONPATH
python /Users/it/sources/1_BIO/panda-web-client/webpanda/webpanda.wsgi