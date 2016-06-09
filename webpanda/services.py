# -*- coding: utf-8 -*-
"""
    webpanda.services
    ~~~~~~~~~~~~~~~~~
    services module
"""
from webpanda.auth import UserService
from webpanda.files import FileService, ContService, ReplicaService
from webpanda.tasks import TaskService, PipelineService
from webpanda.jobs import JobService, SiteService, DistrService

# Auth
users_ = UserService()

# Tasks
tasks_ = TaskService()
pipelines_ = PipelineService()

# Jobs
jobs_ = JobService()
distrs_ = DistrService()
sites_ = SiteService()

# Files
files_ = FileService()
conts_ = ContService()
replicas_ = ReplicaService()

# Async