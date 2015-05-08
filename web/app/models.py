from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin, AnonymousUserMixin
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
        return '<User %r>' % (self.username)

class AnonymousUser(AnonymousUserMixin):
    id = 0
    username = 'anonymous'
    password = ''
    last_seen = datetime.utcnow()
    def verify_password(self, password):
        return password.__eq__('')

    def save(self):
        pass