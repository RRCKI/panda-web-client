# -*- coding: utf-8 -*-
"""
    webpanda.jobs.models
    ~~~~~~~~~~~~~~~~~~~~~~
    Job models
"""

from webpanda.core import db
from webpanda.helpers import JsonSerializer


class JobJsonSerializer(JsonSerializer):
    __json_hidden__ = ['jobs']


class Job(JobJsonSerializer, db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    pandaid = db.Column(db.Integer)
    status = db.Column(db.String(20))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    distr_id = db.Column(db.Integer, db.ForeignKey('distr.id'))
    params = db.Column(db.String(1000))
    container_id = db.Column(db.Integer, db.ForeignKey('containers.id'))
    creation_time = db.Column(db.DateTime)
    modification_time = db.Column(db.DateTime)
    ninputfiles = db.Column(db.Integer)
    noutputfiles = db.Column(db.Integer)
    registered = db.Column(db.Integer, default=0)
    registation_time = db.Column(db.DateTime)
    ce = db.Column(db.String(40))
    corecount = db.Column(db.Integer, default=0)
    tags = db.Column(db.String(256), default='')
    attemptnr = db.Column(db.Integer, default=0)
    def __repr__(self):
        return '<Job id=%s>' % self.id