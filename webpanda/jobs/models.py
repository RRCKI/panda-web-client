# -*- coding: utf-8 -*-
"""
    webpanda.jobs.models
    ~~~~~~~~~~~~~~~~~~~~~~
    Job models
"""

from webpanda.core import db
from webpanda.helpers import JsonSerializer


class Distributive(db.Model):
    __tablename__ = 'distr'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    version = db.Column(db.String(64))
    release = db.Column(db.Integer)
    jobs = db.relationship('Job',
        backref=db.backref('distr', lazy='joined'), lazy='dynamic')

    def __repr__(self):
        return '<Distributive id=%s>' % self.id

    def __str__(self):
        return '%s [%s]' % (self.name, self.version)


class Site(db.Model):
    __tablename__ = 'sites'
    id = db.Column(db.Integer, primary_key=True)
    se = db.Column(db.String(64))
    ce = db.Column(db.String(64))
    plugin = db.Column(db.String(20))
    active = db.Column(db.Integer, default=1)
    datadir = db.Column(db.String(200))
    encode_commands = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return '<SE=%s CE=%s>' % (self.se, self.ce)

    def __str__(self):
        return self.__repr__()


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