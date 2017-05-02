# -*- coding: utf-8 -*-
"""
    webpanda.api
    ~~~~~~~~~~~~~
    webpanda api application package
"""

from functools import wraps

from flask import jsonify, current_app

from webpanda.core import WebpandaError, WebpandaFormError, oauth
from webpanda.helpers import JSONEncoder
from webpanda import factory


def create_app(settings_override=None, register_security_blueprint=False):
    """Returns the Webpanda API application instance"""

    app = factory.create_app(__name__, __path__, settings_override,
                             register_security_blueprint=register_security_blueprint)

    oauth.init_app(app)
    app.debug = True

    # Set the default JSON encoder
    app.json_encoder = JSONEncoder

    # Register custom error handlers
    app.errorhandler(WebpandaError)(on_webpanda_error)
    app.errorhandler(WebpandaFormError)(on_webpanda_form_error)
    app.errorhandler(404)(on_404)

    return app


def route(bp, *args, **kwargs):
    kwargs.setdefault('strict_slashes', False)

    def decorator(f):
        @bp.route(*args, **kwargs)
        @wraps(f)
        def wrapper(*args, **kwargs):
            sc = 200
            rv = f(*args, **kwargs)
            if isinstance(rv, tuple):
                sc = rv[1]
                rv = rv[0]
            return jsonify(dict(data=rv)), sc
        return f

    return decorator


def route_s(bp, *args, **kwargs):
    kwargs.setdefault('strict_slashes', False)

    def decorator(f):
        @bp.route(*args, **kwargs)
        @oauth.require_oauth('api')
        @wraps(f)
        def wrapper(*args, **kwargs):
            sc = 200
            rv = f(*args, **kwargs)
            if isinstance(rv, tuple):
                sc = rv[1]
                rv = rv[0]
            return jsonify(dict(data=rv)), sc
        return f

    return decorator


def on_webpanda_error(e):
    current_app.log.error(e.msg)
    return jsonify(dict(error=e.msg)), 400


def on_webpanda_form_error(e):
    return jsonify(dict(errors=e.errors)), 400


def on_404(e):
    return jsonify(dict(error='Not found')), 404
