from sqlalchemy import Column, Integer, String, ForeignKey, Table, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from common import client_config
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

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

catalog = Table('catalog', Base.metadata,
    Column('container_id', Integer, ForeignKey('containers.id')),
    Column('file_id', Integer, ForeignKey('files.id'))
)

class Container(Base):
    __tablename__ = 'containers'
    id = Column(Integer, primary_key=True)
    guid = Column(String(36))
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
    guid = Column(String(36))
    type = Column(String(20)) #input/output
    se = Column(String(20)) #grid/dropbox/local
    lfn = Column(String(200)) #local file name
    token = Column(String(200)) #string of params to get file
    status = Column(String(20)) #ready/transfer
    transfertask = Column(String(40)) #ui transfer task id
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


    def __repr__(self):
        return '<Replica id=%s>' % self.id

