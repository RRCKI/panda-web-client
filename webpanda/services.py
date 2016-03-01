# -*- coding: utf-8 -*-
"""
    webpanda.services
    ~~~~~~~~~~~~~~~~~
    services module
"""
from webpanda.tasks import TaskService
from webpanda.jobs import JobService


tasks = TaskService()
jobs = JobService()