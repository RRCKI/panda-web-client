import os

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from webpanda import api, dashboard, pilot

os.environ['PANDA_URL'] = 'http://vcloud29.grid.kiae.ru:25085/server/panda'
os.environ['PANRA_URL_SSL'] = 'https://vcloud29.grid.kiae.ru:25443/server/panda'

application = DispatcherMiddleware(dashboard.create_app(config_name="development"), {
    '/api': api.create_app(config_name="development"),
    '/pilot': pilot.create_app(config_name="development")
})

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True)