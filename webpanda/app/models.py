from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from webpanda.app import db

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
    clients = db.relationship('Client',
        backref=db.backref('user', lazy='joined'), lazy='dynamic')
    tokens = db.relationship('Token',
        backref=db.backref('user', lazy='joined'), lazy='dynamic')
    grants = db.relationship('Grant',
        backref=db.backref('user', lazy='joined'), lazy='dynamic')

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

    def __repr__(self):
        return '<SE=%s CE=%s>' % (self.se, self.ce)

    def __str__(self):
        return self.__repr__()

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

class Task(db.Model):
    extend_existing = True
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tag = db.Column(db.String(256))
    status = db.Column(db.String(64), default='defined')
    percentage = db.Column(db.Integer, default=0)
    def __repr__(self):
        return '<Task id=%s tag=%s>' % (self.id, self.tag)

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

class Client(db.Model):
    __tablename__ = 'clients'
    # human readable name, not required
    name = db.Column(db.String(40))

    # human readable description, not required
    description = db.Column(db.String(400))

    # creator of the client, not required
    user_id = db.Column(db.ForeignKey('users.id'))

    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), unique=True, index=True,
                              nullable=False)

    # public or confidential
    is_confidential = db.Column(db.Boolean)

    tokens = db.relationship('Token',
        backref=db.backref('client', lazy='joined'), lazy='dynamic')
    grants = db.relationship('Grant',
        backref=db.backref('client', lazy='joined'), lazy='dynamic')

    _redirect_uris = db.Column(db.Text)
    _default_scopes = db.Column(db.Text)

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

class Grant(db.Model):
    __tablename__ = 'grants'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE')
    )
    client_id = db.Column(
        db.String(40), db.ForeignKey('clients.client_id'),
        nullable=False,
    )

    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(255))
    expires = db.Column(db.DateTime)

    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

class Token(db.Model):
    __tablename__ = 'tokens'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('clients.client_id'),
        nullable=False,
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id')
    )

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class TransferTask(db.Model):
    __tablename__ = 'transfertasks'
    id = db.Column(db.Integer, primary_key=True)
    replica_id = db.Column(db.Integer, db.ForeignKey('replicas.id'))
    se = db.Column(db.String(40))
    task_id = db.Column(db.String(40))
    task_status = db.Column(db.String(20))

class TaskMeta(db.Model):
    __tablename__ = 'celery_taskmeta'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(255))
    status = db.Column(db.String(50))
    result = db.Column(db.BLOB)
    date_done = db.Column(db.DateTime)
    traceback = db.Column(db.Text)

class TaskSetMeta(db.Model):
    __tablename__ = 'celery_tasksetmeta'
    id = db.Column(db.Integer, primary_key=True)
    taskset_id = db.Column(db.String(255))
    result = db.Column(db.BLOB)
    date_done = db.Column(db.DateTime)

