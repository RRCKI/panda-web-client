from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, DateTime, BigInteger, BLOB, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from webpanda.common import client_config

ROLE_USER = 0
ROLE_ADMIN = 1

Base = declarative_base()

class DB:
    def __init__(self):
        self.engine = create_engine(client_config.SQLALCHEMY_DATABASE_URI)
        Base.metadata.bind = self.engine
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()

    def getSession(self):
        return self.session

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), index=True)
    password_hash = Column(String(128))
    active = Column(Integer, default=1)
    last_seen = Column(DateTime)
    role = Column(Integer, default=ROLE_USER)
    jobs = relationship('Job',
        backref=backref('owner', lazy='joined'), lazy='dynamic')

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
        session = DB().getSession()
        session.add(self)
        session.commit()


class Distributive(Base):
    __tablename__ = 'distr'
    id = Column(Integer, primary_key=True)
    name = Column(String(64))
    version = Column(String(64))
    release = Column(Integer)
    jobs = relationship('Job',
        backref=backref('distr', lazy='joined'), lazy='dynamic')

    def __repr__(self):
        return '<Distributive id=%s>' % self.id

    def __str__(self):
        return '%s [%s]' % (self.name, self.version)

class Site(Base):
    __tablename__ = 'sites'
    id = Column(Integer, primary_key=True)
    se = Column(String(64))
    ce = Column(String(64))
    plugin = Column(String(20))
    active = Column(Integer, default=1)
    datadir = Column(String(200))

    def __repr__(self):
        return '<SE=%s CE=%s>' % (self.se, self.ce)

    def __str__(self):
        return self.__repr__()

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    pandaid = Column(Integer)
    status = Column(String(20))
    owner_id = Column(Integer, ForeignKey('users.id'))
    distr_id = Column(Integer, ForeignKey('distr.id'))
    params = Column(String(1000))
    container_id = Column(Integer, ForeignKey('containers.id'))
    creation_time = Column(DateTime)
    modification_time = Column(DateTime)
    ninputfiles = Column(Integer)
    noutputfiles = Column(Integer)
    registered = Column(Integer, default=0)
    registation_time = Column(DateTime)
    ce = Column(String(40))
    corecount = Column(Integer, default=0)
    attemptnr = Column(Integer, default=0)
    
catalog = Table('catalog', Base.metadata,
    Column('container_id', Integer, ForeignKey('containers.id')),
    Column('file_id', Integer, ForeignKey('files.id'))
)

class Container(Base):
    __tablename__ = 'containers'
    id = Column(Integer, primary_key=True)
    guid = Column(String(100))
    status = Column(String(20))
    jobs = relationship('Job',
        backref=backref('container', lazy='joined'), lazy='dynamic')
    files = relationship('File', secondary=catalog,
        backref=backref('containers', lazy='joined'), lazy='dynamic')

    def __repr__(self):
        return '<Container id=%s>' % self.id

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    scope = Column(String(64))
    attemptn = Column(Integer, default=0)
    guid = Column(String(100))
    type = Column(String(20)) #input/output
    lfn = Column(String(200)) #local file name
    status = Column(String(20)) #ready/transfer
    transfertask = Column(String(40)) #ui transfer task id
    fsize = Column(BigInteger)
    md5sum = Column(String(36))
    checksum = Column(String(36))
    modification_time = Column(DateTime)
    downloaded = Column(Integer, default=0)
    replicas = relationship('Replica',
        backref=backref('original', lazy='joined'), lazy='dynamic')

    def __repr__(self):
        return '<File id=%s>' % self.id

class Replica(Base):
    __tablename__ = 'replicas'
    id = Column(Integer, primary_key=True)
    original_id = Column(Integer, ForeignKey('files.id'))
    se = Column(String(20))
    status = Column(String(20)) #ready/transfer
    lfn = Column(String(200)) #local file name
    token = Column(String(200)) #string of params to get file

    def __repr__(self):
        return '<Replica id=%s>' % self.id

class TransferTask(Base):
    __tablename__ = 'transfertasks'
    id = Column(Integer, primary_key=True)
    replica_id = Column(Integer, ForeignKey('replicas.id'))
    se = Column(String(40))
    task_id = Column(String(40))
    task_status = Column(String(20))

class TaskMeta(Base):
    __tablename__ = 'celery_taskmeta'
    id = Column(Integer, primary_key=True)
    task_id = Column(String(255))
    status = Column(String(50))
    result = Column(BLOB)
    date_done = Column(DateTime)
    traceback = Column(Text)

class TaskSetMeta(Base):
    __tablename__ = 'celery_tasksetmeta'
    id = Column(Integer, primary_key=True)
    taskset_id = Column(String(255))
    result = Column(BLOB)
    date_done = Column(DateTime)
