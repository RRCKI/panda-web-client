# -*- coding: utf-8 -*-
"""
    webpanda.tasks.models
    ~~~~~~~~~~~~~~~~~~~~~~
    Task models
"""

from webpanda.core import db, WebpandaError
from webpanda.helpers import JsonSerializer


tasks_jobs = db.Table(
    'tasks_jobs',
    db.Column('task_id', db.Integer(), db.ForeignKey('tasks.id')),
    db.Column('job_id', db.Integer(), db.ForeignKey('jobs.id')))


class PipelineCatalog(db.Model):
    __tablename__ = 'pipeline_catalog2'
    pipeline_type_id = db.Column(db.Integer, db.ForeignKey('pipeline_types.id'), primary_key=True)
    current_task_type_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), primary_key=True)
    next_task_type_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), primary_key=True)

    pipeline_type = db.relationship("PipelineType", back_populates="tasks")
    current_task_type = db.relationship("TaskType", foreign_keys=[current_task_type_id])
    next_task_type = db.relationship("TaskType", foreign_keys=[next_task_type_id])


class TaskTypeJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'method']


class TaskType(TaskTypeJsonSerializer, db.Model):
    __tablename__ = 'task_types'
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(256))
    trf_template = db.Column(db.String(1024))
    ifiles_template = db.Column(db.String(1024))
    ofiles_template = db.Column(db.String(1024))
    tasks = db.relationship("Task", back_populates="task_type")
    distr_id = db.Column(db.Integer, db.ForeignKey('distr.id'))
    distr = db.relationship("Distributive")

    def __repr__(self):
        return '<TaskType id=%s>' % self.id


class PipelineTypeJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'name']


class PipelineType(PipelineTypeJsonSerializer, db.Model):
    __tablename__ = 'pipeline_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    pipelines = db.relationship("Pipeline", back_populates="pipeline_type")
    tasks = db.relationship("PipelineCatalog", back_populates="pipeline_type")

    def __repr__(self):
        return '<PipelineType id=%s>' % self.id


class TaskJsonSerializer(JsonSerializer):
    __json_public__ = ['tag', 'id', 'task_type', 'owner_id', 'creation_time', 'modification_time', 'status']


class Task(TaskJsonSerializer, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_type_id = db.Column(db.Integer, db.ForeignKey('task_types.id'))
    task_type = db.relationship("TaskType", back_populates="tasks")
    tag = db.Column(db.String(256))
    creation_time = db.Column(db.DateTime)
    modification_time = db.Column(db.DateTime)
    status = db.Column(db.String(64), default='defined')
    #TODO place comment - task_status= ?(defined, starting, sent,running finished, cancelled, failed). Also for pipelines -?
    jobs = db.relationship('Job', secondary=tasks_jobs)
    trf = db.Column(db.String(1024))
    input = db.Column(db.Integer, db.ForeignKey('containers.id'), default=None)
    output = db.Column(db.Integer, db.ForeignKey('containers.id'), default=None)
    comment = db.Column(db.String(1024))
    params = db.Column(db.Text)

    def __repr__(self):
        return '<Task id=%s tag=%s>' % (self.id, self.tag)


class PipelineJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'owner_id', 'type_id', 'tag', 'current_task_id', 'status']


class Pipeline(PipelineJsonSerializer, db.Model):
    __tablename__ = 'pipelines'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('pipeline_types.id'))
    pipeline_type = db.relationship("PipelineType", back_populates="pipelines")
    tag = db.Column(db.String(256))
    current_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    status = db.Column(db.String(256))
    creation_time = db.Column(db.DateTime)
    modification_time = db.Column(db.DateTime)

    def __repr__(self):
        return '<Pipeline id=%s name=%s>' % (self.id, self.name)














