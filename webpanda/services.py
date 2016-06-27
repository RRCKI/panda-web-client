# -*- coding: utf-8 -*-
"""
    webpanda.services
    ~~~~~~~~~~~~~~~~~
    services module
"""
from webpanda.auth import UserService
from webpanda.files import FileService, ContService, ReplicaService, CatalogService
from webpanda.tasks import TaskService, PipelineService, PipelineTypeService, TaskTypeService
from webpanda.jobs import JobService, SiteService, DistrService

# Auth
users_ = UserService()

# Tasks
tasks_ = TaskService()
task_types_ = TaskTypeService()
pipelines_ = PipelineService()
pipeline_types_ = PipelineTypeService()

# Jobs
jobs_ = JobService()
distrs_ = DistrService()
sites_ = SiteService()

# Files
files_ = FileService()
conts_ = ContService()
replicas_ = ReplicaService()
catalog_ = CatalogService()

# Async
