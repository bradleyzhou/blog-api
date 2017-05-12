import re
from flask import request

from .models import User
from .exceptions import ValidationError

_username_re = re.compile(r'^[A-Za-z][A-Za-z0-9_.]*$')
_email_re = re.compile(r'[^@]+@[^@]+\.[^@]+')


def validate_request_json():
    if request.json is None:
        raise ValidationError('Invalid JSON data')


def validate_username(username):
    if not _username_re.match(username):
        raise ValidationError('Usernames must have only letters, '
                              'numbers, dots or underscores')
    if User.query.filter_by(username=username).first():
        raise ValidationError('Username already in use.')


def validate_email(email):
    if not _email_re.match(email):
        raise ValidationError('Invalid email address')
    if User.query.filter_by(email=email).first():
        raise ValidationError('Email already registered.')


def validate_password(password):
    if password is None or password.strip() == '':
        raise ValidationError('Password must not be empty')
