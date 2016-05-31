# -*- coding: utf-8 -*-
"""
    webpanda.auth
    ~~~~~~~~~~~~~~~~~
    webpanda auth package
"""
from webpanda.auth.models import User
from webpanda.core import Service


class UserService(Service):
    __model__ = User