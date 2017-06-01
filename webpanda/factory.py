from datetime import datetime
import os

from flask import Flask, g
from celery import Celery
from flask import request
from flask_login import current_user

from webpanda.config import config
from webpanda.auth.models import AnonymousUser
from webpanda.common.NrckiLogger import NrckiLogger

from webpanda.core import db, lm
from webpanda.helpers import register_blueprints
from webpanda.middleware import HTTPMethodOverrideMiddleware
from webpanda.services import users_


def create_app(package_name, package_path, settings_override=None,
               register_security_blueprint=True, config_name="development"):
    """Returns a :class:`Flask` application instance configured with common
    functionality for the chatfirst platform.
    :param package_name: application package name
    :param package_path: application package path
    :param settings_override: a dictionary of settings to override
    :param register_security_blueprint: flag to specify if the Flask-Security
                                        Blueprint should be registered. Defaults
                                        to `True`.
    """
    app = Flask(package_name, instance_relative_config=True)

    app.config.from_object('webpanda.settings')
    app.config.from_object(config[config_name])
    app.config.from_pyfile('settings.cfg', silent=True)
    app.config.from_object(settings_override)
    if 'SQLALCHEMY_DATABASE_URI' in os.environ.keys():
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']

    db.init_app(app)
    #security.init_app(app, SQLAlchemyUserDatastore(db, User, Role),
    #                  register_blueprint=register_security_blueprint)

    register_blueprints(app, package_name, package_path)

    app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)

    app.log = NrckiLogger().getLogger(package_name)

    # Prepare auth
    lm.init_app(app)
    lm.login_view = 'auth.main_auth'

    lm.anonymous_user = AnonymousUser

    @lm.user_loader
    def load_user(id):
        if id == 0:
            return AnonymousUser()
        return users_.get(id=id)

    @app.before_request
    def before_request():
        g.user = current_user
        g.user.last_seen = datetime.utcnow()
        g.user.save()

        values = request.form.to_dict()
        app.log.info("incoming request: {method} {url}; Form: {form}; Data: {data}".format(method=request.method,
                                                                                       url=request.full_path,
                                                                                       form=str(values), data=str(
                request.get_json(silent=True))))

    return app


def create_celery_app(app=None):
    app = app or create_app('webpanda', os.path.dirname(__file__))
    celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery