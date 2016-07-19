# -*- coding: utf-8 -*-
"""
    webpanda.auth
    ~~~~~~~~~~~~~~~~~
    webpanda auth package
"""
from webpanda.auth.models import User, Grant, Client, Token
from webpanda.core import Service


class UserService(Service):
    __model__ = User

class ClientService(Service):
    __model__ = Client

class GrantService(Service):
    __model__ = Grant

class TokenService(Service):
    __model__ = Token