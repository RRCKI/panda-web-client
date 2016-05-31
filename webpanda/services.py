# -*- coding: utf-8 -*-
"""
    webpanda.services
    ~~~~~~~~~~~~~~~~~
    services module
"""
from webpanda.auth import UserService
from webpanda.tasks import TaskService, PipelineService
from webpanda.jobs import JobService


tasks = TaskService()
pipelines = PipelineService()
jobs = JobService()
users = UserService()
