from base64 import b64encode

import requests
from flask import current_app

from webpanda.core import WebpandaError


def encode_cred(client, secret):
    return b64encode("{client}:{secret}".format(client=client, secret=secret))


def get_auth_endpoint():
    """
    Generates auth url from SSO
    :return:
    """
    url = current_app.config["AUTH_AUTH_ENDPOINT"]
    redirect_uri = current_app.config["AUTH_REDIRECT_URI"]
    client_id = current_app.config["AUTH_CLIENT"]

    return "{url}?scope=openid&response_type=code&client_id={client_id}&redirect_uri={redirect_uri}".format(
        url=url,
        client_id=client_id,
        redirect_uri=redirect_uri
    )


def get_token_by_code(code):
    url = current_app.config["AUTH_TOKEN_ENDPOINT"]
    redirect_uri = current_app.config["AUTH_REDIRECT_URI"]
    client = current_app.config["AUTH_CLIENT"]
    secret = current_app.config["AUTH_SECRET"]
    headers = dict()
    headers["Authorization"] = "Basic {code}".format(code=encode_cred(client, secret))

    params = dict()
    params['grant_type'] = "authorization_code"
    params["code"] = code
    params["redirect_uri"] = redirect_uri

    rv = requests.post(url, data=params, headers=headers, verify=False)

    data = rv.json()

    if "error" not in data.keys():
        access_token = data["access_token"]
        token_type = data["token_type"]
        refresh_token = data["refresh_token"]
        expires_in = data["expires_in"]
        id_token = data["id_token"]

        return access_token

    raise WebpandaError("Bad get_token response: " + str(data))


def sso_get_user(token):
    url = current_app.config["AUTH_USERINFO_ENDPOINT"]
    headers = dict()
    headers["Authorization"] = "Bearer {code}".format(code=token)

    rv = requests.get(url, headers=headers, verify=False)

    data = rv.json()

    if "error" not in data.keys():
        return data['sub'].split(":")[-1]

    raise WebpandaError("Bad sso_get_user response: " + str(data))


def sso_logout_user():
    url = current_app.config["AUTH_LOGOUT_ENDPOINT"]

    rv = requests.get(url, verify=False)

    data = rv.json()

    if "error" not in data.keys():
        return True

    raise WebpandaError("Bad sso_logout_user response: " + str(data))
