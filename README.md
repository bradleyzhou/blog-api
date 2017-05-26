# bradleyzhou.com
Source code of the website blog.bradleyzhou.com REST-ful APIs


## Run the dev server
```
FLASK_APP=manage.py flask run

# if need a quick test database, init a sqlite db first:
FLASK_APP=manage.py flask db init
FLASK_APP=manage.py flask db migrate
FLASK_APP=manage.py flask db upgrade
ADMIN_NAME=admin ADMIN_EMAIL=admin@example.com ADMIN_KEY=password FLASK_APP=manage.py flask add_admin
```

## Build and deploy using Docker
### Build Docker image
Depends on [the `pu` image](https://github.com/bradleyzhou/pun)
```
git clone https://github.com/bradleyzhou/blog-api.git
cd blog-api
docker build -t blogapi .
```

### Run Docker image (example)
```
docker run -v /tmp/app.sock:/app/app.sock blogapi
```

### Run with other Docker images
This Docker image is designed to work with  Nginx setup by unix socket file. The Nginx could be installed and configured, or spun-up by a Docker image.

For an exmaple, see the [blog-deploy repo](https://github.com/bradleyzhou/blog-deploy)

## API Design Draft
Base URL: https://blog.bradleyzhou.com/api/v1.0


Action | Request Method | Endpoint | Auth | Response
-------|----------------|----------|--------|--------
Get available APIs (TODO) | ?? | / |  Anonymous/Username+password/Token | Available APIs according to auth status
Get all posts | GET | /posts/ |  Anonymous/Username+password/Token | Paginated posts
Get a post | GET | /posts/title-of-post |  Anonymous/Username+password/Token | A single post
Create a new post | POST | /posts/ | Username+password/Token | A link to newly created post
Update/modify an existing post | PUT | /posts/title-of-post | Username+password/Token | The updated post
Get a user | GET | /users/name | Anonymous/Username+password/Token | The user infomation
Get posts of a user | GET | /users/name/posts/ | Anonymous/Username+password/Token | Paginated posts of the user
