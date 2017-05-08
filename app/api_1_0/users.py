from flask import jsonify
from flask import request
from flask import current_app
from flask import url_for

from . import api
from ..models import User, Post
from ..exceptions import NotFoundError


@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if user is None:
        raise NotFoundError('user not found')
    return jsonify(user.to_json())


@api.route('/users/<int:id>/posts')
def get_user_posts(id):
    user = User.query.get(id)
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
