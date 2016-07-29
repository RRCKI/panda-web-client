# -*- coding: utf-8 -*-
"""
    webpanda.files.forms
    ~~~~~~~~~~~~~~~~~~~~~~~
    Files forms
"""
from webpanda.forms import RedirectForm
from wtforms import SelectField, SubmitField
from wtforms import StringField
from wtforms.validators import Required
from wtforms.validators import Length


class NewFileForm(RedirectForm):
    path = StringField(u'PATH', validators=[Required(), Length(1, 64)])
    submitbtn = SubmitField(u'Upload')


class NewContainerForm(RedirectForm):
    ftpdir = StringField(u'FTP DIR', validators=[Length(1, 64)])
    submitbtn = SubmitField(u'Upload')