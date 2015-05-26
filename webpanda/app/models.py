from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from app import db


ROLE_USER = 0
ROLE_ADMIN = 1

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    active = db.Column(db.Integer, default=1)
    last_seen = db.Column(db.DateTime)
    role = db.Column(db.Integer, default=ROLE_USER)
    jobs = db.relationship('Job',
        backref=db.backref('owner', lazy='joined'), lazy='dynamic')

    def is_active(self):
        return self.active == 1

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<User name=%s>' % (self.username)

class AnonymousUser():
    id = 0
    username = 'anonymous'
    password = ''
    last_seen = datetime.utcnow()

    def is_authenticated(self):
        return False
    def is_active(self):
        return True
    def is_anonymous(self):
        return True

    def get_id(self):
        return 0
    def verify_password(self, password):
        return password.__eq__('')

    def save(self):
        pass

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

class Job(db.Model):
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

    def __repr__(self):
        return '<Job id=%s>' % self.id

catalog = db.Table('catalog',
    db.Column('container_id', db.Integer, db.ForeignKey('containers.id')),
    db.Column('file_id', db.Integer, db.ForeignKey('files.id'))
)

class Container(db.Model):
    __tablename__ = 'containers'
    id = db.Column(db.Integer, primary_key=True)
    guid = db.Column(db.String(36))
    jobs = db.relationship('Job',
        backref=db.backref('container', lazy='joined'), lazy='dynamic')
    files = db.relationship('File', secondary=catalog,
        backref=db.backref('containers', lazy='joined'), lazy='dynamic')

    def __repr__(self):
        return '<Container id=%s>' % self.id

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    scope = db.Column(db.String(64))
    attemptn = db.Column(db.Integer, default=0)
    guid = db.Column(db.String(36))
    type = db.Column(db.String(20)) #input/output
    se = db.Column(db.String(20)) #grid/dropbox/local
    lfn = db.Column(db.String(200)) #local file name
    token = db.Column(db.String(200)) #string of params to get file
    status = db.Column(db.String(20)) #ready/transfer
    replicas = db.relationship('Replica',
        backref=db.backref('original', lazy='joined'), lazy='dynamic')

    def __repr__(self):
        return '<File id=%s>' % self.id

class Replica(db.Model):
    __tablename__ = 'replicas'
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, db.ForeignKey('files.id'))
    se = db.Column(db.String(20))
    status = db.Column(db.String(20)) #ready/transfer
    lfn = db.Column(db.String(200)) #local file name

    def __repr__(self):
        return '<Replica id=%s>' % self.id



