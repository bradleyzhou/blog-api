import unittest
import json
from base64 import b64encode
from flask import url_for

from app import create_app
from app import db
from app.models import User
from app.models import Role


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        # allow testing url_for() with _external=True
        self.app.config['SERVER_NAME'] = 'test.test'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def test_404(self):
        response = self.client.get(
            '/wrong/url',
            headers=self.get_api_headers('email', 'password')
        )
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error'] == 'not found')

    def test_no_auth(self):
        response = self.client.get(url_for('api.get_posts'),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_password_auth(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat',
                 username='john', role=r)
        db.session.add(u)
        db.session.commit()

        # email and password
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('john@example.com', 'cat')
        )
        self.assertEqual(response.status_code, 200)

        # username and password
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('john', 'cat')
        )
        self.assertEqual(response.status_code, 200)

        # bad password
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('john@example.com', 'dog')
        )
        self.assertEqual(response.status_code, 401)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error'] == 'unauthorized')

        # bad username
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('baduser', 'dog')
        )
        self.assertEqual(response.status_code, 401)

        # bad email
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('baduser@example.com', 'dog')
        )
        self.assertEqual(response.status_code, 401)

    def test_token_auth(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat',
                 username='john', role=r)
        db.session.add(u)
        db.session.commit()

        # bad token
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers('bad-token', '')
        )
        self.assertEqual(response.status_code, 401)

        # get a token by an anonymous user
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers('', '')
        )
        self.assertEqual(response.status_code, 401)

        # get a token by a bad user
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers('baduser', 'cat')
        )
        self.assertEqual(response.status_code, 401)

        # get a token
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers('john@example.com', 'cat')
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        # good token
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers(token, '')
        )
        self.assertEqual(response.status_code, 200)

    def test_anonymous(self):
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('', '')
        )
        self.assertEqual(response.status_code, 200)

    def test_posts(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat',
                 username='john', role=r)
        db.session.add(u)
        db.session.commit()

        # write an empty post
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': '',
                'title': '',
                }))
        self.assertEqual(response.status_code, 400)

        # write a post
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'body of the *blog* post',
                'title': 'Title of blog',
                }))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # get the new post
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url)
        self.assertTrue(json_response['body'] == 'body of the *blog* post')
        self.assertTrue(json_response['body_html'] ==
                        '<p>body of the <em>blog</em> post</p>')
        json_post = json_response

        # get the post from the user
        response = self.client.get(
            url_for('api.get_user_posts', id=u.id),
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertTrue(json_response.get('count', 0) == 1)
        self.assertTrue(json_response['posts'][0] == json_post)

        # edit post
        response = self.client.put(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'updated body',
                'title': 'Changed Title',
                }))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url)
        self.assertTrue(json_response['title'] == 'Changed Title')
        self.assertTrue(json_response['body'] == 'updated body')
        self.assertTrue(json_response['body_html'] == '<p>updated body</p>')

    def test_users(self):
        # add two users
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='john@example.com', username='john',
                  password='cat', role=r)
        u2 = User(email='susan@example.com', username='susan',
                  password='dog', role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        # get users
        response = self.client.get(
            url_for('api.get_user', id=u1.id),
            headers=self.get_api_headers('susan@example.com', 'dog')
            )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'john')
        response = self.client.get(
            url_for('api.get_user', id=u2.id),
            headers=self.get_api_headers('susan@example.com', 'dog')
            )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'susan')

    def test_posts_permission(self):
        # add two users and an admin
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        adminr = Role.query.filter_by(name='Administrator').first()
        self.assertIsNotNone(adminr)
        u1 = User(email='john@example.com', username='john',
                  password='cat', role=r)
        u2 = User(email='susan@example.com', username='susan',
                  password='dog', role=r)
        adminu = User(email='admin@example.com', username='admin',
                      password='cat', role=adminr)
        db.session.add_all([adminu, u1, u2])
        db.session.commit()

        # write a post for each user
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'body 1 of the *blog* post',
                'title': 'Title of Blog 1',
                }))
        self.assertEqual(response.status_code, 201)
        url1 = response.headers.get('Location')
        self.assertIsNotNone(url1)
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('susan@example.com', 'dog'),
            data=json.dumps({
                'body': 'body 2 of the *blog* post',
                'title': 'Title of Blog 2',
                }))
        self.assertEqual(response.status_code, 201)
        url2 = response.headers.get('Location')
        self.assertIsNotNone(url2)

        # edit post by a different author
        response = self.client.put(
            url1,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'updated body 1',
                'title': 'Changed Title 1',
                }))
        self.assertEqual(response.status_code, 200)
        response = self.client.put(
            url2,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'updated body 2',
                'title': 'Changed Title 2',
                }))
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error'] == 'forbidden')
        response = self.client.put(
            url1,
            headers=self.get_api_headers('admin@example.com', 'cat'),
            data=json.dumps({
                'body': 'updated body 3',
                'title': 'Changed Title 3',
                }))
        self.assertEqual(response.status_code, 403)

    def test_create_user(self):
        # add an admin and a user
        adminr = Role.query.filter_by(name='Administrator').first()
        self.assertIsNotNone(adminr)
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        adminu = User(email='admin@example.com', username='admin',
                      password='cat', role=adminr)
        u = User(email='susan@example.com', username='susan',
                 password='dog', role=r)
        db.session.add_all([adminu, u])
        db.session.commit()

        # create a new user
        response = self.client.post(
            url_for('api.new_user'),
            headers=self.get_api_headers('susan@example.com', 'dog'),
            data=json.dumps({
                'username': 'newu',
                'email': 'newu@example.com',
                'password': 'rain',
                }))
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            url_for('api.new_user'),
            headers=self.get_api_headers('admin@example.com', 'cat'),
            data=json.dumps({
                'username': 'newu',
                'email': 'newu@example.com',
                'password': 'rain',
                }))
        self.assertEqual(response.status_code, 201)

    def test_change_password(self):
        # add two users
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(email='john@example.com', username='john',
                  password='cat', role=r)
        u2 = User(email='susan@example.com', username='susan',
                  password='dog', role=r)
        db.session.add_all([u1, u2])
        db.session.commit()

        response = self.client.put(
            url_for('api.change_password', id=u2.id),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'password': 'changed',
                }))
        self.assertEqual(response.status_code, 403)
        response = self.client.put(
            url_for('api.change_password', id=u1.id),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'password': 'changed',
                }))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            )
        self.assertEqual(response.status_code, 401)
