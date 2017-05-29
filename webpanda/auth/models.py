from datetime import datetime

import ldap
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from webpanda.core import db

ROLE_USER = 0
ROLE_ADMIN = 1


def get_ldap_connection():
    conn = ldap.initialize(current_app.config['LDAP_PROVIDER_URL'])
    return conn


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

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.active == 1

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def verify_ldap(username, password):
        conn = get_ldap_connection()

        ldap_result_id = conn.search(current_app.config['LDAP_BASE_DN'], ldap.SCOPE_SUBTREE,
                                     "uid= {user}".format(user=username), None)

        result_type, result_data = conn.result(ldap_result_id, 0)

        if type(result_data) == list and result_data != [] and len(result_data) != 0:
            if result_type == ldap.RES_SEARCH_ENTRY:
                dn = result_data[0][0]
            else:
                print "bad result type"
                raise ldap.INVALID_CREDENTIALS
        else:
            print "bad return list"
            raise ldap.INVALID_CREDENTIALS

        conn.simple_bind_s(dn, password)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<User name=%s>' % self.username


class AnonymousUser():
    def __init__(self):
        self.id = 0
        self.username = 'anonymous'
        self.password = ''
        self.last_seen = datetime.utcnow()

    @property
    def is_authenticated(self):
        return False

    @property
    def is_active(self):
        return False

    @property
    def is_anonymous(self):
        return True

    def get_id(self):
        return None

    def verify_password(self, password):
        return password.__eq__('')

    def save(self):
        pass


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