import site, os, sys

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

#from webpanda.app import app as oldapp
#from webpanda import app as newapp
from webpanda import api, dashboard, pilot

site.addsitedir('/srv/test/panda-web-client/venv/lib/python2.7/site-packages')
basedir = '/srv/test/panda-web-client'
os.environ['PANDA_URL'] = 'http://vcloud29.grid.kiae.ru:25085/server/panda'
os.environ['PANRA_URL_SSL'] = 'https://vcloud29.grid.kiae.ru:25443/server/panda'

#application = DispatcherMiddleware(newapp.create_app(), {
#    '/api2': api.create_app()
#})

#application = DispatcherMiddleware(oldapp, {
#    '/api2': api.create_app(),
#    '/dashboard': dashboard.create_app()
#})

application = DispatcherMiddleware(dashboard.create_app(), {
    '/api': api.create_app(),
    '/pilot': pilot.create_app()
})

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True)