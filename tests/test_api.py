import unittest
import json
import time
from datetime import datetime
from base64 import b64encode
from flask import url_for

from app import create_app
from app import db
from app.models import User
from app.models import Post
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
        self.datetime_format = '%a, %d %b %Y %H:%M:%S %Z'

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
        self.assertEqual(response.status_code, 403)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['error'], 'forbidden')

        # bad username
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('baduser', 'dog')
        )
        self.assertEqual(response.status_code, 403)

        # bad email
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('baduser@example.com', 'dog')
        )
        self.assertEqual(response.status_code, 403)

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
        self.assertEqual(response.status_code, 403)

        # get a token by an anonymous user
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers('', '')
        )
        self.assertEqual(response.status_code, 403)

        # get a token by a bad user
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers('baduser', 'cat')
        )
        self.assertEqual(response.status_code, 403)

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

        # get a non-existant post
        response = self.client.get(
            url_for('api.get_post', slug='xki9s9999'),
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 404)

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
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['body'], 'body of the *blog* post')
        self.assertIsNotNone(json_response['created_at'])
        self.assertIsNotNone(json_response['updated_at'])
        created_at = json_response['created_at']
        updated_at = json_response['updated_at']
        json_post = json_response

        # get the post from the user
        response = self.client.get(
            url_for('api.get_user_posts', username=u.username),
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        # edit post
        time.sleep(1)
        response = self.client.put(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'updated body',
                'title': 'Changed Title',
                }))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertNotEqual(json_response['url'], url)  # title changed
        self.assertEqual(json_response['title'], 'Changed Title')
        self.assertEqual(json_response['body'], 'updated body')
        self.assertEqual(json_response['created_at'], created_at)
        self.assertGreater(datetime.strptime(json_response['updated_at'],
                           self.datetime_format),
                           datetime.strptime(updated_at,
                           self.datetime_format))

        # title slug is in url
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'blog body',
                'title': 'The Greek in a Box with an Clock',
                }))
        self.assertEqual(response.status_code, 201)
        title_slug = 'greek-in-box-with-clock'
        url = response.headers.get('Location')
        self.assertIn(title_slug, url)
        self.assertNotIn('The', url)
        self.assertNotIn('a-', url)
        self.assertNotIn('an-', url)
        self.assertNotIn('Great', url)

        # title itself is not slugified
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['title'], 'The Greek in a Box with an Clock')

        # title put without change keeps url unchanged
        response = self.client.put(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'title': 'The Greek in a Box with an Clock',
                }))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn(title_slug, json_response['url'])
        self.assertNotIn(title_slug + '-1', json_response['url'])
        self.assertNotIn(title_slug + '-2', json_response['url'])

        # title change but slug unchanged keeps url unchanged
        response = self.client.put(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'title': 'the GrEEk in boX with clock a',
                }))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn(title_slug, json_response['url'])
        self.assertNotIn(title_slug + '-1', json_response['url'])
        self.assertNotIn(title_slug + '-2', json_response['url'])

        # title change result in url change
        response = self.client.put(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'updated body',
                'title': 'Changed Title',
                }))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertIn('changed-title', json_response['url'])

        # title slug collision
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'blog body 1',
                'title': 'Title',
                }))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        title_slug = 'title'
        self.assertIn(title_slug, url)

        # title is the same with slug collision
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['title'], 'Title')
        self.assertEqual(json_response['body'], 'blog body 1')

        # title slug collision 1
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'blog body 2',
                'title': 'Title',
                }))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        title_slug = 'title-2'
        self.assertIn(title_slug, url)

        # title is the same with slug collision
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['title'], 'Title')
        self.assertEqual(json_response['body'], 'blog body 2')

        # title slug collision 2
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'blog body 3',
                'title': 'Title',
                }))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        title_slug = 'title-3'
        self.assertIn(title_slug, url)

        # title is the same with slug collision
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['url'], url)
        self.assertEqual(json_response['title'], 'Title')
        self.assertEqual(json_response['body'], 'blog body 3')

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
            url_for('api.get_user', username=u1.username),
            headers=self.get_api_headers('susan@example.com', 'dog')
            )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'john')
        response = self.client.get(
            url_for('api.get_user', username=u2.username),
            headers=self.get_api_headers('susan@example.com', 'dog')
            )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['username'] == 'susan')

        # non-existant user
        response = self.client.get(
            url_for('api.get_user', username='s99si99'),
            headers=self.get_api_headers('susan@example.com', 'dog')
            )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            url_for('api.get_user_posts', username=9999),
            headers=self.get_api_headers('susan@example.com', 'dog')
            )
        self.assertEqual(response.status_code, 404)

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

        # not author, cannot edit
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

        # edit post by author
        response = self.client.put(
            url1,
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'body': 'updated body 1',
                'title': 'Changed Title 1',
                }))
        self.assertEqual(response.status_code, 200)

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

        # normal user cannot create a new user
        response = self.client.post(
            url_for('api.new_user'),
            headers=self.get_api_headers('susan@example.com', 'dog'),
            data=json.dumps({
                'username': 'newu',
                'email': 'newu@example.com',
                'password': 'rain',
                }))
        self.assertEqual(response.status_code, 403)

        # admin can creat new user
        response = self.client.post(
            url_for('api.new_user'),
            headers=self.get_api_headers('admin@example.com', 'cat'),
            data=json.dumps({
                'username': 'newu',
                'email': 'newu@example.com',
                'password': 'rain',
                }))
        self.assertEqual(response.status_code, 201)

        # username collision
        response = self.client.post(
            url_for('api.new_user'),
            headers=self.get_api_headers('admin@example.com', 'cat'),
            data=json.dumps({
                'username': 'newu',
                'email': 'newu1@example.com',
                'password': 'rain',
                }))
        self.assertEqual(response.status_code, 400)

        # user email collision
        response = self.client.post(
            url_for('api.new_user'),
            headers=self.get_api_headers('admin@example.com', 'cat'),
            data=json.dumps({
                'username': 'newu1',
                'email': 'newu@example.com',
                'password': 'rain',
                }))
        self.assertEqual(response.status_code, 400)

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

        # change non-existant user's password
        response = self.client.put(
            url_for('api.change_password', username='sp9d999g'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'password': 'changed',
                }))
        self.assertEqual(response.status_code, 400)

        # change other user's password
        response = self.client.put(
            url_for('api.change_password', username=u2.username),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'password': 'changed',
                }))
        self.assertEqual(response.status_code, 403)

        # change password by self
        response = self.client.put(
            url_for('api.change_password', username=u1.username),
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({
                'password': 'changed',
                }))
        self.assertEqual(response.status_code, 200)

        # bad auth indicates password has changed
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('john@example.com', 'cat'),
            )
        self.assertEqual(response.status_code, 403)

    def test_post_pagination(self):
        n_per_page = self.app.config['POSTS_PER_PAGE']
        n = 2 * n_per_page + 1
        User.generate_fake(20)
        Post.generate_fake(n)

        # page 1
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('', ''),
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['count'], n)
        self.assertEqual(len(json_response['posts']), n_per_page)
        self.assertIsNone(json_response['prev'])
        self.assertIsNotNone(json_response['next'])

        # page 2
        response = self.client.get(
            json_response['next'],
            headers=self.get_api_headers('', ''),
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['count'], n)
        self.assertEqual(len(json_response['posts']), n_per_page)
        self.assertIsNotNone(json_response['prev'])
        self.assertIsNotNone(json_response['next'])

        # last page
        response = self.client.get(
            json_response['next'],
            headers=self.get_api_headers('', ''),
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['count'], n)
        self.assertEqual(len(json_response['posts']), 1)
        self.assertIsNotNone(json_response['prev'])
        self.assertIsNone(json_response['next'])
