# -*- coding: utf-8 -*-
import ldap
from flask import current_app
from flask_login import login_user, logout_user
from flask import Blueprint, render_template, request, url_for, flash, g
from werkzeug.utils import redirect

from webpanda.auth.forms import LoginForm
from webpanda.auth.forms import RegisterForm
from webpanda.auth.models import User
from webpanda.auth.scripts import get_token_by_code, sso_get_user, get_auth_endpoint
from webpanda.dashboard import route, route_s
from webpanda.services import users_
from webpanda.common.NrckiLogger import NrckiLogger

bp = Blueprint('auth', __name__)
_logger = NrckiLogger().getLogger("dashboard.auth")


@route(bp, '/auth', methods=['GET'])
def main_auth():
    url = get_auth_endpoint() if current_app.config["AUTH_AUTH_ENDPOINT"] else url_for('auth.login')
    return redirect(url)


@route(bp, '/login', methods=['GET', 'POST'])
def login():
    user = g.user
    _logger.debug("Trying to login user: {user}".format(user=user.username))
    if user.is_authenticated:
        # if user is logged in we get out of here
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate():
        # Check credentials
        if current_app.config['LDAP_PROVIDER_URL'] and form.ldap.data:
            # Use LDAP service
            try:
                User.verify_ldap(form.username.data, form.password.data)
            except ldap.INVALID_CREDENTIALS:
                flash(
                    'Invalid username or password. Please try again.',
                    'danger')
                return render_template('dashboard/auth/login.html', form=form)

            user = users_.first(username=form.username.data)

            if user is None:
                user = User()
                user.username = form.username.data
                user.active = 1
                users_.save(user)
        else:
            # Use local service
            user = users_.first(username=form.username.data)
            if user is None or not user.verify_password(form.password.data):
                flash('Invalid username or password.')
                return redirect(url_for('auth.login'))

        # log user in
        login_user(user, remember=form.remember_me.data)
        flash('You are now logged in!')
        return redirect(request.args.get("next") or url_for("main.index"))

    return render_template('dashboard/auth/login.html',
                           form=form,
                           url=get_auth_endpoint())


@route_s(bp, '/logout')
def logout():
    # Logout user internally
    logout_user()

    # Redirect to SSO user logout
    url = current_app.config["AUTH_LOGOUT_ENDPOINT"] if current_app.config["AUTH_LOGOUT_ENDPOINT"] else url_for('main.index')
    return redirect(url)


@route(bp, '/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate():
        username = form.username.data
        password = form.password.data
        password_again = form.password_again.data
        user = users_.first(username=username)
        if user is not None:
            flash('Попробуйте другой login.')
            return redirect(url_for('auth.register'))
        if password != password_again:
            flash('Пароли не совпадают.')
            return redirect(url_for('auth.register'))
        user = User()
        user.username = username
        user.password = password
        user.active = 0
        user.role = 0
        users_.save(user)
        return redirect(url_for('auth.login'))

    return render_template('dashboard/auth/register.html',
                           form=form)


@route(bp, '/redirect', methods=['GET'])
def redirect_callback():
    code = request.args.get('code', None, type=str)

    if code:
        token = get_token_by_code(code)
        username = sso_get_user(token)

        user = users_.first(username=username)

        if user is None:
            user = User()
            user.username = username
            user.active = 1
            users_.save(user)

        # log user in
        login_user(user, remember=False)
        flash('You are now logged in!')

    return redirect(url_for('main.index'))