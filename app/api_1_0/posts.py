from flask import g
from flask import jsonify
from flask import request
from flask import url_for
from flask import current_app

from ..models import Post
from ..models import Permission
from ..validators import validate_request_json
from .. import db
from . import api
from .errors import forbidden
from .errors import not_found
from .decorators import permission_required


@api.route('/posts/')
@permission_required(Permission.READ_ARTICLES)
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/posts/<string:slug>')
@permission_required(Permission.READ_ARTICLES)
def get_post(slug):
    post = Post.query.filter_by(slug=slug).first()
    if post is None:
        return not_found('post not found')
    return jsonify(post.to_json())


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    validate_request_json()
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, \
        {'Location': url_for('api.get_post', slug=post.slug, _external=True)}


@api.route('/posts/<string:slug>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(slug):
    validate_request_json()
    post = Post.query.filter_by(slug=slug).first()
    if post is None:
        return not_found('post not found')
    if g.current_user != post.author:
        return forbidden('Insufficient permissions')
    post.title = request.json.get('title', post.title)
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    return jsonify(post.to_json())
