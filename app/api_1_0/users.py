from flask import g
from flask import jsonify
from flask import request
from flask import current_app
from flask import url_for

from .. import db
from ..models import User
from ..models import Post
from ..models import Permission
from ..exceptions import NotFoundError
from ..exceptions import ForbiddenError
from ..exceptions import ValidationError
from ..validators import validate_request_json
from ..validators import validate_username
from ..validators import validate_password
from ..validators import validate_email
from . import api
from .decorators import permission_required


@api.route('/users/<string:username>')
def get_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        raise NotFoundError('user not found')
    return jsonify(user.to_json())


@api.route('/users/<string:username>/posts')
def get_user_posts(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        raise NotFoundError('user not found')
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total,
    })


@api.route('/users/', methods=['POST'])
@permission_required(Permission.CREATE_USERS)
def new_user():
    validate_request_json()
    validate_username(request.json.get('username'))
    validate_email(request.json.get('email'))
    validate_password(request.json.get('password'))
    user = User.from_json(request.json)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_json()), 201, \
        {'Location': url_for('api.get_user', username=user.username, _external=True)}


@api.route('/users/<string:username>/password', methods=['PUT'])
def change_password(username):
    validate_request_json()
    validate_password(request.json.get('password'))
    user = User.query.filter_by(username=username).first()
    if user is None:
        raise ValidationError('user not found')
    if not g.current_user.is_administrator() and g.current_user != user:
        raise ForbiddenError('Insufficient permissions')
    user.password = request.json.get('password')
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_json())
