# -*- coding: utf-8 -*-
"""
    webpanda.tasks
    ~~~~~~~~~~~~~~~~~
    webpanda tasks package
"""

from webpanda.core import Service
from webpanda.tasks.models import Task, Pipeline, PipelineType, TaskType, PipelineCatalog, PipelineArchive


class TaskService(Service):
    __model__ = Task

class TaskTypeService(Service):
    __model__ = TaskType


class PipelineService(Service):
    __model__ = Pipeline

class PipelineTypeService(Service):
    __model__ = PipelineType

class PipelineCatalogService(Service):
    __model__ = PipelineCatalog

class PipelineArchiveService(Service):
    __model__ = PipelineArchive

