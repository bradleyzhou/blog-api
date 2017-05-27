from datetime import datetime
from slugify import slugify
from flask import url_for
from flask import current_app
from sqlalchemy.orm.base import NO_VALUE
from sqlalchemy.orm.base import NEVER_SET
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from . import db
from .exceptions import ValidationError


class Permission:
    READ_ARTICLES = 0x01
    WRITE_ARTICLES = 0x02
    CREATE_USERS = 0x04
    RESET_PASSWORD = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.READ_ARTICLES |
                     Permission.WRITE_ARTICLES, True),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    is_anonymous = False

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN_EMAIL']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def __repr__(self):
        return '<User %r>' % self.username

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(username=forgery_py.internet.user_name(True),
                     email=forgery_py.internet.email_address(),
                     password=forgery_py.lorem_ipsum.word(),
                     )
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', username=self.username, _external=True),
            'username': self.username,
            'email': self.email,
            'posts': url_for('api.get_user_posts', username=self.username, _external=True),
        }
        return json_user

    @staticmethod
    def from_json(json_user):
        return User(username=json_user.get('username'),
                    email=json_user.get('email'),
                    password=json_user.get('password'),
                    )


class AnonymousUser(object):
    is_anonymous = True

    def can(self, permissions):
        return (Permission.READ_ARTICLES & permissions) == permissions

    def is_administrator(self):
        return False


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    slug = db.Column(db.Text, index=True, unique=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def generate_fake(count=100):
        from random import seed
        from random import randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            p = Post(title=forgery_py.lorem_ipsum.title(),
                     body=forgery_py.lorem_ipsum.paragraphs(),
                     timestamp=forgery_py.date.date(True),
                     author=u,
                     )
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def slugify_title(text, separator='-', max_length=40):
        slug = slugify(text,
                       separator=separator,
                       stopwords=['the', 'a', 'an'],
                       max_length=max_length,
                       word_boundary=True,
                       save_order=True,
                       )
        counter = 2
        new_slug = slug
        while db.session.query(Post.query.filter_by(slug=new_slug).exists()).scalar():
            new_slug = "{}{}{}".format(slug, separator, counter)
            counter += 1
        return new_slug

    @staticmethod
    def title_to_slug(target, value, oldvalue, initiator):
        old_slug = None
        if oldvalue is not NO_VALUE and oldvalue is not NEVER_SET:
            old_slug = Post.slugify_title(oldvalue)
        new_slug = Post.slugify_title(value)
        if value and not value == oldvalue and not old_slug == new_slug:
            target.slug = new_slug

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', slug=self.slug, _external=True),
            'title': self.title,
            'body': self.body,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', username=self.author.username, _external=True),
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        title = json_post.get('title')
        if title is None or title == '':
            raise ValidationError('Post does not have a title')
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('Post does not have a body')
        return Post(title=title, body=body)


db.event.listen(Post.title, 'set', Post.title_to_slug)
