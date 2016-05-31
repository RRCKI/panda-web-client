# -*- coding: utf-8 -*-
"""
    webpanda.files.models
    ~~~~~~~~~~~~~~~~~~~~~~
    Files models
"""
from webpanda.core import db


catalog = db.Table('catalog',
    db.Column('container_id', db.Integer, db.ForeignKey('containers.id')),
    db.Column('file_id', db.Integer, db.ForeignKey('files.id'))
)


#class Catalog(db.Model):
#    __tablename__ = 'catalog'
#    container_id = db.Column(db.Integer, db.ForeignKey('containers.id'), primary_key=True)
#    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), primary_key=True)
#    type = db.Column(db.String(50))
#    file = db.relationship("File", back_populates="containers")
#    cont = db.relationship("Container", back_populates="files")


class Container(db.Model):
    __tablename__ = 'containers'
    id = db.Column(db.Integer, primary_key=True)
    guid = db.Column(db.String(100))
    status = db.Column(db.String(20))
    jobs = db.relationship('Job',
        backref=db.backref('container', lazy='joined'), lazy='dynamic')
    files = db.relationship('File', secondary=catalog,
        backref=db.backref('containers', lazy='joined'), lazy='dynamic')
#    files = db.relationship("Catalog", back_populates="cont")

    def __repr__(self):
        return '<Container id=%s>' % self.id


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    scope = db.Column(db.String(64))
    attemptn = db.Column(db.Integer, default=0)
    guid = db.Column(db.String(100))
    type = db.Column(db.String(20)) #input/output
    lfn = db.Column(db.String(200)) #local file name
    status = db.Column(db.String(20)) #ready/transfer
    transfertask = db.Column(db.String(40)) #ui transfer task id
    fsize = db.Column(db.BigInteger)
    md5sum = db.Column(db.String(36))
    checksum = db.Column(db.String(36))
    modification_time = db.Column(db.DateTime)
    downloaded = db.Column(db.Integer, default=0)
    replicas = db.relationship('Replica',
        backref=db.backref('original', lazy='joined'), lazy='dynamic')
#    containers = db.relationship("Catalog", back_populates="file")

    def __repr__(self):
        return '<File id=%s>' % self.id


class Replica(db.Model):
    __tablename__ = 'replicas'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, db.ForeignKey('files.id'))
    se = db.Column(db.String(20))
    status = db.Column(db.String(20)) #ready/transfer
    lfn = db.Column(db.String(200)) #local file name
    token = db.Column(db.String(200)) #string of params to get file

    def __repr__(self):
        return '<Replica id=%s>' % self.id