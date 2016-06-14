# -*- coding: utf-8 -*-
"""
    webpanda.tasks
    ~~~~~~~~~~~~~~~~~
    webpanda tasks package
"""

from webpanda.core import Service
from webpanda.tasks.models import Task, Pipeline, PipelineType


class TaskService(Service):
    __model__ = Task


class PipelineService(Service):
    __model__ = Pipeline

class PipelineTypeService(Service):
    __model__ = PipelineType