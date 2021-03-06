# -*- coding: utf-8 -*-
"""
    webpanda.files
    ~~~~~~~~~~~~~~~~~
    webpanda files package
"""
from webpanda.core import Service
from webpanda.files.models import File, Container, Replica, Catalog, TransferTask, TaskMeta, TaskSetMeta


class FileService(Service):
    __model__ = File


class ContService(Service):
    __model__ = Container


class ReplicaService(Service):
    __model__ = Replica


class CatalogService(Service):
    __model__ = Catalog


class TransferTaskService(Service):
    __model__ = TransferTask


class TaskMetaService(Service):
    __model__ = TaskMeta


class TaskSetMetaService(Service):
    __model__ = TaskSetMeta
