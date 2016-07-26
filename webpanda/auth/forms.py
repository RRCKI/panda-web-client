from flask_wtf import Form
from wtforms import SubmitField, PasswordField, StringField, BooleanField
from wtforms.validators import EqualTo, Length
from wtforms.validators import Required

from webpanda.forms import RedirectForm
from webpanda.services import users_


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
        user = users_.first(username=self.username.data)
        if user is not None:
            self.username.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True