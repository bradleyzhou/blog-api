from flask import g
from flask_httpauth import HTTPBasicAuth

from ..models import User
from . import api
from .errors import unauthorized

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(name_or_email, password):
    user = User.query.filter_by(username=name_or_email).first()
    if not user:
        user = User.query.filter_by(email=name_or_email).first()
    if not user:
        return False
    g.current_user = user
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    pass
