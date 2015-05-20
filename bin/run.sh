#!/usr/bin/env bash
export PYTHONPATH=$PYTHONPATH:$PANDACOMMON:$PANDASERVER:$NRCKICLIENT
export PANDA_URL=http://vcloud29.grid.kiae.ru:25085/server/panda
export PANDA_URL_SSL=https://vcloud29.grid.kiae.ru:25443/server/panda
../venv/bin/python ../web/run.py