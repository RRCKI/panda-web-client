from urlparse import urlparse, urljoin

from flask.ext.wtf import Form
from flask import url_for, redirect, request
from wtforms import StringField, PasswordField, SubmitField, BooleanField, HiddenField
from wtforms.validators import Required, EqualTo, Length
from app.models import User


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))

class LoginForm(RedirectForm):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('remember_me', default = False)
    submit = SubmitField('Login')

class RegisterForm(RedirectForm):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    password_again = PasswordField('Password again',
                                   validators=[Required(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(username = self.username.data).first()
        if user != None:
            self.username.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True




