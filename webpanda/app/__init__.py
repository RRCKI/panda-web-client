# -*- coding: utf-8 -*-
"""
    webpanda.frontend
    ~~~~~~~~~~~~~~~~~~
    launchpad frontend application package
"""
import os
from functools import wraps

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_oauthlib.provider import OAuth2Provider
from celery import Celery

from webpanda.core import db as db2
from webpanda import factory


app = Flask(__name__)
app.config.from_object('webpanda.app.config')
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

from webpanda.app.models import User, AnonymousUser

lm.anonymous_user = AnonymousUser
@lm.user_loader
def load_user(id):
    if id == 0:
        return AnonymousUser()
    return User.query.filter_by(id=id).first()


from webpanda.app import views
from webpanda.app import views_oauth
from webpanda.app import apis
from webpanda.app import admin

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(os.path.join(app.config['BASE_DIR'], app.config['LOG_DIR'], 'webclient.log'), 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    from webpanda.common.NrckiLogger import NrckiLogger
    oauth_log = NrckiLogger().getLogger('flask_oauthlib')



def create_app(settings_override=None):
    """Returns the Overholt dashboard application instance"""
    app = factory.create_app(__name__, __path__, settings_override)

#    migrate = Migrate(app, db)
#    manager = Manager(app)
#    manager.add_command('db', MigrateCommand)
    lm = LoginManager()
    lm.init_app(app)
    lm.login_view = 'dashboard.login'
    adm = Admin(app, name='WEBPANDA - Admin')
    oauth = OAuth2Provider(app)
    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)

    from webpanda.app.models import User, AnonymousUser

    lm.anonymous_user = AnonymousUser
    @lm.user_loader
    def load_user(id):
	if id == 0:
    	    return AnonymousUser()
	return User.query.filter_by(id=id).first()


    if not app.debug:
	import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(os.path.join(app.config['BASE_DIR'], app.config['LOG_DIR'], 'webclient.log'), 'a', 1 * 1024 * 1024, 10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        app.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        from webpanda.common.NrckiLogger import NrckiLogger
        oauth_log = NrckiLogger().getLogger('flask_oauthlib')


    # Register custom error handlers
    if not app.debug:
        for e in [500, 404]:
            app.errorhandler(e)(handle_error)

    return app


def handle_error(e):
    return render_template('errors/%s.html' % e.code), e.code


def route(bp, *args, **kwargs):
    def decorator(f):
        @bp.route(*args, **kwargs)
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator

def route_s(bp, *args, **kwargs):
    def decorator(f):
        @bp.route(*args, **kwargs)
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator


if __name__ == '__main__':
    #app.run()
    manager.run()
