from flask import jsonify

from app.exceptions import ValidationError
from app.exceptions import NotFoundError
from . import api


def bad_request(message):
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


def not_found(message):
    response = jsonify({'error': 'not found', 'message': message})
    response.status_code = 404
    return response


def not_allowed(message):
    response = jsonify({'error': 'not allowed', 'message': message})
    response.status_code = 405
    return response


def server_error(message):
    response = jsonify({'error': 'internal error', 'message': message})
    response.status_code = 500
    return response


@api.app_errorhandler(400)
def e400(e):
    return bad_request(str(e))


@api.app_errorhandler(401)
def e401(e):
    return unauthorized(str(e))


@api.app_errorhandler(403)
def e403(e):
    return forbidden(str(e))


@api.app_errorhandler(404)
def e404(e):
    return not_found(str(e))


@api.app_errorhandler(405)
def e405(e):
    return not_allowed(str(e))


@api.app_errorhandler(500)
def e500(e):
    return server_error(str(e))


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])


@api.errorhandler(NotFoundError)
def not_found_error(e):
    return not_found(e.args[0])
