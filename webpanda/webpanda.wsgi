import site, os, sys

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from webpanda.app import app
from webpanda import api

site.addsitedir('/srv/test/panda-web-client/venv/lib/python2.7/site-packages')
basedir = '/srv/test/panda-web-client'
os.environ['PANDA_URL'] = 'http://vcloud29.grid.kiae.ru:25085/server/panda'
os.environ['PANRA_URL_SSL'] = 'https://vcloud29.grid.kiae.ru:25443/server/panda'

application = DispatcherMiddleware(app, {
    '/api2': api.create_app()
})

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True)