# -*- coding: utf-8 -*-
"""
    webpanda.tasks
    ~~~~~~~~~~~~~~~~~
    webpanda tasks package
"""

from webpanda.core import Service
from webpanda.tasks.models import Task, Pipeline


class TaskService(Service):
    __model__ = Task


class PipelineService(Service):
    __model__ = Pipeline
