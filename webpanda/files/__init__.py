# -*- coding: utf-8 -*-
"""
    webpanda.files
    ~~~~~~~~~~~~~~~~~
    webpanda files package
"""
from webpanda.core import Service
from webpanda.files.models import File, Container, Replica


class FileService(Service):
    __model__ = File


class ContService(Service):
    __model__ = Container


class ReplicaService(Service):
    __model__ = Replica
