# -*- coding: utf-8 -*-
"""
    webpanda.jobs.forms
    ~~~~~~~~~~~~~~~~~~~~~~~
    Jobs forms
"""
from webpanda.forms import RedirectForm
from wtforms import IntegerField, StringField, BooleanField, SubmitField, HiddenField, TextAreaField, SelectField
from wtforms import validators
from wtforms.validators import Length, Required


class NewJobForm(RedirectForm):
    site = SelectField(u'Computing site', [validators.required()], coerce=int)
    distr = SelectField(u'Distributive', coerce=str)
    params = TextAreaField(u'Parameters', [validators.required(), validators.length(1, 1000)])
    container = HiddenField(default="")
    corecount = IntegerField('Cores', default=1)
    ftpdir = StringField(u'FTP DIR')
    submitbtn = SubmitField(u'Send job')
    onebyone = BooleanField(u'One file one job', default=False)
    tags = StringField(u'Tags')


class JobResendForm(RedirectForm):
    id_ = IntegerField('id_', default=1)


class JobKillForm(RedirectForm):
    id_ = IntegerField('id_', default=1)


class NewDistrForm(RedirectForm):
    name = StringField('Name', [validators.required(), validators.length(1, 64)])
    version = StringField('Version', [validators.required(), validators.length(1, 64)])
    release = IntegerField('Release')