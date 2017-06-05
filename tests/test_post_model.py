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
        self.assertIsNotNone(p.created_at)
        self.assertIsNotNone(p.updated_at)
        self.assertEqual(p.author, u)

    def test_from_json(self):
        json_post = {
            'title': 'Title Json',
            'body': 'Body from *Json*.',
        }
        p = Post.from_json(json_post)
        self.assertEqual(p.title, 'Title Json')
        self.assertEqual(p.body, 'Body from *Json*.')

    def test_slug(self):
        json_post = {
            'title': 'Title a an Json',
            'body': 'Body from *Json*.',
        }
        p = Post.from_json(json_post)
        self.assertEqual(p.slug, 'title-json')

    def test_slug_collision(self):
        json_post = {
            'title': 'Title Json',
            'body': 'Body from *Json*.',
        }
        p = Post.from_json(json_post)
        db.session.add(p)
        db.session.commit()

        json_post_2 = {
            'title': 'Title Json',
            'body': 'Body 2 from *Json*.',
        }
        p2 = Post.from_json(json_post_2)
        db.session.add(p2)
        db.session.commit()

        self.assertEqual(p.slug, 'title-json')
        self.assertEqual(p2.slug, 'title-json-2')

    def test_slug_title_change(self):
        json_post = {
            'title': 'Title Json',
            'body': 'Body from *Json*.',
        }
        p = Post.from_json(json_post)
        db.session.add(p)
        db.session.commit()
        self.assertEqual(p.slug, 'title-json')

        p.title = 'Title Json'
        db.session.add(p)
        db.session.commit()
        self.assertEqual(p.slug, 'title-json')

        p.title = 'New Title'
        db.session.add(p)
        db.session.commit()
        self.assertEqual(p.slug, 'new-title')

        p.title = 'Title Json'
        db.session.add(p)
        db.session.commit()
        self.assertEqual(p.slug, 'title-json')
