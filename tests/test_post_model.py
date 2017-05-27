import unittest

from app import create_app
from app import db
from app.models import Post
from app.models import User
from app.models import Role


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        # allow testing url_for() with _external=True
        self.app.config['SERVER_NAME'] = 'test.test'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_post_field(self):
        User.generate_fake(1)
        u = User.query.first()
        Post.generate_fake(1)
        p = Post.query.first()
        self.assertIsNotNone(p.title)
        self.assertIsNotNone(p.body)
        self.assertIsNotNone(p.timestamp)
        self.assertEqual(p.author, u)

    def test_from_json(self):
        json_post = {
            'title': 'Title Json',
            'body': 'Body from *Json*.',
        }
        p = Post.from_json(json_post)
        self.assertEqual(p.title, 'Title Json')
        self.assertEqual(p.body, 'Body from *Json*.')
