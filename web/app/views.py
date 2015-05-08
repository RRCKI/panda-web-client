# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import render_template, flash, redirect, session, url_for, request, g, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm
from forms import LoginForm, RegisterForm
from models import User, ROLE_USER, ROLE_ADMIN
from datetime import datetime


@app.before_request
def before_request():
    g.user = current_user
    g.user.last_seen = datetime.utcnow()
    g.user.save()

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = g.user
    return render_template("index.html",
        title = 'Home',
        user = user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = g.user
    if user.is_authenticated():
        # if user is logged in we get out of here
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        # log user in
        login_user(user, remember = form.remember_me.data)
        flash('You are now logged in!')
        return redirect(request.args.get("next") or url_for("index"))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password_again = form.password_again.data
        user = User.query.filter_by(username=username).first()
        if user is not None:
            flash('Попробуйте другой login.')
            return redirect(url_for('register'))
        if password != password_again:
            flash('Пароли не совпадают.')
            return redirect(url_for('register'))
        user = User()
        user.username = username
        user.password = password
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500