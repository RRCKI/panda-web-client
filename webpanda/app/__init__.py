from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_oauthlib.provider import OAuth2Provider
from celery import Celery
import os

app = Flask(__name__)
app.config.from_object('app.config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
adm = Admin(app, name='WEBPANDA - Admin')
oauth = OAuth2Provider(app)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from models import User, AnonymousUser
#from models_oauth import *

lm.anonymous_user = AnonymousUser
@lm.user_loader
def load_user(id):
    if id == 0:
        return AnonymousUser()
    return User.query.filter_by(id=id).first()


from app import views
from app import views_oauth
from app import apis
from app import admin

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(os.path.join(app.config['BASE_DIR'], app.config['LOG_DIR'], 'webclient.log'), 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('microblog startup')

if __name__ == '__main__':
    #app.run()
    manager.run()
