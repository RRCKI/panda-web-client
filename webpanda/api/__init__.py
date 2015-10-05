import os

from flask import Flask
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from flask_oauthlib.provider import OAuth2Provider
from celery import Celery


app = Flask(__name__)
app.config.from_object('api.config')
db = SQLAlchemy(app)
manager = Manager(app)
oauth = OAuth2Provider(app)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from webpanda.api import views

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(os.path.join(app.config['BASE_DIR'], app.config['LOG_DIR'], 'webapi.log'), 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    from webpanda.common.NrckiLogger import NrckiLogger
    oauth_log = NrckiLogger().getLogger('flask_oauthlib')

    app.logger.info('api startup')

if __name__ == '__main__':
    app.run()