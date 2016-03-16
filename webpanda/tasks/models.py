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


class TaskJsonSerializer(JsonSerializer):
    pass


class Task(TaskJsonSerializer, db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tag = db.Column(db.String(256))
    status = db.Column(db.String(64), default='defined')
    percentage = db.Column(db.Integer, default=0)
    jobs = db.relationship('Job', secondary=tasks_jobs)
    def __repr__(self):
        return '<Task id=%s tag=%s>' % (self.id, self.tag)

