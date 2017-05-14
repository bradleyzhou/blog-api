import unittest
import time

from app import create_app
from app import db
from app.models import User
from app.models import Role
from app.models import AnonymousUser
from app.models import Permission


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

    def test_user_field(self):
        User.generate_fake(1)
        u = User.query.first()
        self.assertIsNotNone(u.username)
        self.assertIsNotNone(u.email)
        self.assertIsNotNone(u.role)

    def test_password_setter(self):
        u = User(password='cat')
        self.assertIsNotNone(u.password_hash)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_valid_authorization_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(expiration=3600)
        self.assertTrue(User.verify_auth_token(token) == u)

    def test_invalid_authorization_token(self):
        u = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u)
        db.session.add(u2)
        db.session.commit()
        token = u.generate_auth_token(expiration=3600)
        self.assertTrue(User.verify_auth_token(token) != u2)

    def test_expired_authorization_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(expiration=1)
        time.sleep(2)
        self.assertTrue(User.verify_auth_token(token) != u)

    def test_roles_and_permissions(self):
        u = User(email='john@example.com', password='cat')
        r = Role.query.filter_by(name='User').first()
        self.assertEqual(u.role, r)
        self.assertFalse(u.is_administrator())
        self.assertTrue(u.can(Permission.READ_ARTICLES))
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.CREATE_USERS))
        self.assertFalse(u.can(Permission.ADMINISTER))

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.is_administrator())
        self.assertTrue(u.can(Permission.READ_ARTICLES))
        self.assertFalse(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.CREATE_USERS))
        self.assertFalse(u.can(Permission.ADMINISTER))

    def test_administrator(self):
        admin_email = 'admin@example.com'
        self.app.config['ADMIN_EMAIL'] = admin_email
        u = User(email=admin_email, password='cat')
        self.app.config['ADMIN_EMAIL'] = ''
        self.assertTrue(u.is_administrator())
        self.assertTrue(u.can(Permission.READ_ARTICLES))
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertTrue(u.can(Permission.CREATE_USERS))
        self.assertTrue(u.can(Permission.RESET_PASSWORD))
        self.assertTrue(u.can(Permission.ADMINISTER))

    def test_to_json(self):
        u = User(username='John', email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        json_user = u.to_json()
        expected_keys = ['url', 'username', 'email', 'posts']
        self.assertEqual(sorted(json_user.keys()), sorted(expected_keys))
        self.assertTrue('api/v1.0/users/' in json_user['url'])

    def test_from_json(self):
        json_user = {
            'username': 'John',
            'email': 'john@example.com',
            'password': 'cat',
        }
        u = User.from_json(json_user)
        self.assertEqual(u.username, json_user['username'])
        self.assertEqual(u.email, json_user['email'])
