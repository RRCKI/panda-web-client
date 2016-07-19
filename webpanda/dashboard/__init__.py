# -*- coding: utf-8 -*-
"""
    webpanda.dashboard
    ~~~~~~~~~~~~~
    webpanda dashboard application package
"""
from datetime import datetime

from functools import wraps

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import login_required, current_user
from flask import jsonify, g

from webpanda.auth.models import ROLE_ADMIN, User
from webpanda.core import WebpandaError, WebpandaFormError, db
from webpanda.files.models import Replica, File, Container, TaskSetMeta, TaskMeta
from webpanda.helpers import JSONEncoder
from webpanda import factory
from webpanda.jobs import Job
from webpanda.jobs.models import Site, Distributive
from webpanda.tasks import Pipeline, Task


def create_app(settings_override=None, register_security_blueprint=False):
    """Returns the Webpanda API application instance"""

    app = factory.create_app(__name__, __path__, settings_override,
                             register_security_blueprint=register_security_blueprint)

    # Set the default JSON encoder
    app.json_encoder = JSONEncoder
    app.debug = True

    # Register custom error handlers
    app.errorhandler(WebpandaError)(on_webpanda_error)
    app.errorhandler(WebpandaFormError)(on_webpanda_form_error)
    app.errorhandler(404)(on_404)

    adm = Admin(app, name='WEBPANDA - Admin')

    class MyModelView(ModelView):
        def is_accessible(self):
            return current_user.is_authenticated and current_user.role == ROLE_ADMIN

    adm.add_view(MyModelView(User, db.session))
    adm.add_view(MyModelView(Distributive, db.session))
    adm.add_view(MyModelView(Site, db.session))
    adm.add_view(MyModelView(Job, db.session))
    adm.add_view(MyModelView(Container, db.session))
    adm.add_view(MyModelView(File, db.session))
    adm.add_view(MyModelView(Replica, db.session))
    adm.add_view(MyModelView(TaskMeta, db.session))
    adm.add_view(MyModelView(TaskSetMeta, db.session))
    adm.add_view(MyModelView(Pipeline, db.session))
    adm.add_view(MyModelView(Task, db.session))

    @app.before_request
    def before_request():
        g.user = current_user
        g.user.last_seen = datetime.utcnow()
        g.user.save()


    return app


def route(bp, *args, **kwargs):
    kwargs.setdefault('strict_slashes', False)

    def decorator(f):
        @bp.route(*args, **kwargs)
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator


def route_s(bp, *args, **kwargs):
    kwargs.setdefault('strict_slashes', False)

    def decorator(f):
        @bp.route(*args, **kwargs)
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator

def on_webpanda_error(e):
    return jsonify(dict(error=e.msg)), 400


def on_webpanda_form_error(e):
    return jsonify(dict(errors=e.errors)), 400


def on_404(e):
    return jsonify(dict(error='Not found')), 404
