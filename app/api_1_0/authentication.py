from flask import g
from flask import jsonify
from flask_httpauth import HTTPBasicAuth

from ..models import User
from ..models import AnonymousUser
from . import api
from .errors import unauthorized

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(name_or_email_or_token, password):
    if name_or_email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    if password == '':
        g.current_user = User.verify_auth_token(name_or_email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(username=name_or_email_or_token).first()
    if not user:
        user = User.query.filter_by(email=name_or_email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@api.route('/token')
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({
        'token': g.current_user.generate_auth_token(expiration=3600),
        'expiration': 3600,
    })


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    pass
