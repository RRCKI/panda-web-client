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
    se = SelectField(u'SE', coerce=str)
    url = StringField(u'URL', validators=[Required(), Length(1, 64)])
    container = StringField(u'Container (guid)', validators=[Length(1, 64)])
    submitbtn = SubmitField(u'Upload file')


class NewContainerForm(RedirectForm):
    ftpdir = StringField(u'FTP DIR', validators=[Length(1, 64)])
    submitbtn = SubmitField(u'Upload')