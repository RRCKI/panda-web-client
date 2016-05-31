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


class PipelineJsonSerializer(JsonSerializer):
    __json_public__ = ['id', 'name']


class Pipeline(PipelineJsonSerializer, db.Model):
    __tablename__ = 'pipelines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))

    def __repr__(self):
        return '<Pipeline id=%s name=%s>' % (self.id, self.name)


class TaskJsonSerializer(JsonSerializer):
    pass


class Task(TaskJsonSerializer, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'))
    pipeline = db.relationship('Pipeline',
        backref=db.backref('tasks', lazy='dynamic'))
    tag = db.Column(db.String(256))
    creation_time = db.Column(db.DateTime)
    modification_time = db.Column(db.DateTime)
    status = db.Column(db.String(64), default='defined')
    jobs = db.relationship('Job', secondary=tasks_jobs)
    def __repr__(self):
        return '<Task id=%s tag=%s>' % (self.id, self.tag)


