from datetime import datetime, timedelta

from flask import request, jsonify, session, g, Blueprint
from flask import render_template
from flask_login import login_required

from werkzeug.security import gen_salt
from werkzeug.utils import redirect

from webpanda.services import clients_, grants_, tokens_, users_
from webpanda.api import route
from webpanda.auth import Grant
from webpanda.auth import Token
from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.core import oauth


bp = Blueprint('auth', __name__)
_logger = NrckiLogger().getLogger("api.main")


@oauth.clientgetter
def load_client(client_id):
    return clients_.first(client_id=client_id)

@oauth.grantgetter
def load_grant(client_id, code):
    return grants_.first(client_id=client_id, code=code)

@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    # decide the expires time yourself
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=g.user,
        expires=expires
    )
    grants_.save(grant)
    return grant

@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return tokens_.first(access_token=access_token)
    elif refresh_token:
        return tokens_.first(refresh_token=refresh_token)

@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = tokens_.find(client_id=request.client.client_id,
                                 user_id=request.user.id)
    # make sure that every client has only one token connected to a user
    for t in toks:
        tokens_.delete(t)

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id,
    )
    tokens_.save(tok)
    return tok

@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    user = users_.first(username=username)
    if user.verify_password(password):
        return user
    return None

@route(bp, '/oauth/authorize', methods=['GET', 'POST'])
@login_required
@oauth.authorize_handler
def authorize(*args, **kwargs):
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        client = clients_.first(client_id=client_id)
        kwargs['client'] = client
        kwargs['user'] = client.user
        return render_template('oauth/authorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'

@route(bp, '/oauth/token', methods=['POST'])
@oauth.token_handler
def access_token():
    return {'version': '0.1.0'}

@route(bp, '/oauth/revoke', methods=['POST'])
@oauth.revoke_handler
def revoke_token(): pass

@oauth.invalid_response
def invalid_require_oauth(req):
    return jsonify(message=req.error_message), 401

# @route('/api/me')
# @oauth.require_oauth()
# def me():
#     user = request.oauth.user
#     return jsonify(username=user.username)
#
# @route('/api', methods=('GET', 'POST'))
# def home():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         user = users_.first(username=username)
#         if not user:
#             user = User(username=username)
#             users_.save(user)
#         session['id'] = user.id
#         return redirect('/')
#     user = g.user
#     return render_template('oauth/home.html', user=user)
#
# @route('/api/client')
# @login_required
# def client():
#     user = g.user
#     if not user:
#         return redirect('/')
#     item = Client(
#         client_id=gen_salt(40),
#         client_secret=gen_salt(50),
#         _redirect_uris=' '.join([
#             'http://localhost:8000/authorized',
#             'http://127.0.0.1:8000/authorized',
#             'http://127.0.1:8000/authorized',
#             'http://127.1:8000/authorized',
#             ]),
#         _default_scopes='email',
#         user_id=user.id,
#     )
#     clients_.save(client)
#     return jsonify(
#         client_id=item.client_id,
#         client_secret=item.client_secret,
#     )
