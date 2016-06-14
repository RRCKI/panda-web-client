# -*- coding: utf-8 -*-
"""
    webpanda.tasks.models
    ~~~~~~~~~~~~~~~~~~~~~~
    Task models
"""

from webpanda.core import db
from webpanda.helpers import JsonSerializer


tasks_jobs = db.Table(
    'tasks_jobs',
    db.Column('task_id', db.Integer(), db.ForeignKey('tasks.id')),
    db.Column('job_id', db.Integer(), db.ForeignKey('jobs.id')))


class TaskTypeJsonSerializer(JsonSerializer):
    pass


class TaskType(TaskTypeJsonSerializer, db.Model):
    __tablename__ = 'task_types'
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(256))
    trf_template = db.Column(db.String(1024))
    ifiles_template = db.Column(db.String(1024))
    ofiles_template = db.Column(db.String(1024))

    def __repr__(self):
        return '<TaskType id=%s>' % self.id


class PipelineTypeJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'name']


class PipelineType(PipelineTypeJsonSerializer, db.Model):
    __tablename__ = 'pipeline_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    init_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    pre_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    split_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    prun_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    merge_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    post_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)
    finish_tasktype_id = db.Column(db.Integer, db.ForeignKey('task_types.id'), default=None)

    def __repr__(self):
        return '<PipelineType id=%s>' % self.id


class TaskJsonSerializer(JsonSerializer):
    pass


class Task(TaskJsonSerializer, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    task_type_id = db.Column(db.Integer, db.ForeignKey('task_types.id'))
    tag = db.Column(db.String(256))
    creation_time = db.Column(db.DateTime)
    modification_time = db.Column(db.DateTime)
    status = db.Column(db.String(64), default='defined')
    jobs = db.relationship('Job', secondary=tasks_jobs)
    trf = db.Column(db.String(1024))
    input = db.Column(db.Integer, db.ForeignKey('containers.id'), default=None)
    output = db.Column(db.Integer, db.ForeignKey('containers.id'), default=None)
    def __repr__(self):
        return '<Task id=%s tag=%s>' % (self.id, self.tag)


class PipelineJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'name']


class Pipeline(PipelineJsonSerializer, db.Model):
    __tablename__ = 'pipelines'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('pipeline_types.id'))
    name = db.Column(db.String(256))
    tag = db.Column(db.String(256))
    current_state = db.Column(db.String(256))
    init_task = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    pre_task = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    split_task = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    prun_task = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    merge_task = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    post_task = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)
    finish_task = db.Column(db.Integer, db.ForeignKey('tasks.id'), default=None)

    def __repr__(self):
        return '<Pipeline id=%s name=%s>' % (self.id, self.name)






