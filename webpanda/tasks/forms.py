# -*- coding: utf-8 -*-
"""
    webpanda.tasks.forms
    ~~~~~~~~~~~~~~~~~~~~~~~
    Tasks forms
"""
from webpanda.forms import RedirectForm
from wtforms import validators, TextAreaField


class NewPipelineForm(RedirectForm):
    ifiles = TextAreaField(u'Input files', [
        validators.DataRequired(),
        validators.Length(1, 1000)])