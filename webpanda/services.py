# -*- coding: utf-8 -*-
"""
    webpanda.services
    ~~~~~~~~~~~~~~~~~
    services module
"""
from webpanda.auth import UserService, GrantService, ClientService, TokenService
from webpanda.files import FileService, ContService, ReplicaService, CatalogService, TransferTaskService, TaskMetaService, TaskSetMetaService
from webpanda.tasks import TaskService, PipelineService, PipelineTypeService, TaskTypeService, PipelineCatalogService, \
    PipelineArchiveService
from webpanda.jobs import JobService, SiteService, DistrService

# Auth
users_ = UserService()
clients_ = ClientService()
grants_ = GrantService()
tokens_ = TokenService()

# Tasks
tasks_ = TaskService()
task_types_ = TaskTypeService()
pipelines_ = PipelineService()
pipeline_types_ = PipelineTypeService()
pipeline_catalog_ = PipelineCatalogService()
pipeline_archive_ = PipelineArchiveService()

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
transfers_ = TransferTaskService()
transfers_meta_ = TaskMetaService()
transfers_set_meta_ = TaskSetMetaService()
