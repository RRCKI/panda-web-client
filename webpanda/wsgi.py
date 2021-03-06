import site, os, sys

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from webpanda import api, dashboard, pilot

site.addsitedir('/srv/test2/panda-web-client/venv/lib/python2.7/site-packages')
basedir = '/srv/test2/panda-web-client'

application = DispatcherMiddleware(dashboard.create_app(config_name="production"), {
    '/api': api.create_app(config_name="production"),
    '/pilot': pilot.create_app(config_name="production")
})

if __name__ == "__main__":
    run_simple('0.0.0.0', 5000, application, use_reloader=True, use_debugger=True)
