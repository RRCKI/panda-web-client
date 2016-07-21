# -*- coding: utf-8 -*-
from flask_login import login_user, logout_user
from flask import Blueprint, render_template, request, url_for, flash, g

from webpanda.app.forms import LoginForm, RegisterForm
from webpanda.auth.models import User
from webpanda.dashboard import route, route_s
from webpanda.services import users_
from werkzeug.utils import redirect
from webpanda.common.NrckiLogger import NrckiLogger

bp = Blueprint('auth', __name__)
_logger = NrckiLogger().getLogger("dashboard.auth")


@route(bp, '/login', methods=['GET', 'POST'])
def login():
    user = g.user
    if user.is_authenticated:
        # if user is logged in we get out of here
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = users_.first(username=form.username.data)
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))
        # log user in
        login_user(user, remember = form.remember_me.data)
        flash('You are now logged in!')
        return redirect(request.args.get("next") or url_for("main.index"))
    return render_template('dashboard/auth/login.html', form=form)


@route_s(bp, '/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@route(bp, '/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
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

    return render_template('dashboard/auth/register.html', form=form)