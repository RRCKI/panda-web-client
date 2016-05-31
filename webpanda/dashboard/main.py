from flask import render_template, Blueprint, g
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.dashboard import route_s

bp = Blueprint('main', __name__)
_logger = NrckiLogger().getLogger("dashboard.main")


@route_s(bp, '/')
def index():
    user = g.user
    return render_template("index.html",
        title = 'Home',
        user = user)


@route_s(bp, '/help')
def help():
    return render_template("pandaweb/help.html")