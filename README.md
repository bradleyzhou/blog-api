# bradleyzhou.com
Source code of the website blog.bradleyzhou.com REST-ful APIs


## Run the dev server
```
# prepare the setup
export FLASK_APP=manage.py
export ADMIN_NAME=admin
export ADMIN_EMAIL=admin@example.com
export ADMIN_KEY=password

# if need a quick test database, init a sqlite db first:
flask db init
flask db migrate
flask db upgrade
flask deploy

# start the dev server
flask run
```

## Build and deploy using Docker
### Build Docker image
Depends on [the `pu` image](https://github.com/bradleyzhou/pun)
```
git clone https://github.com/bradleyzhou/blog-api.git
cd blog-api
docker build -t blogapi .
```

### Run Docker image for production (example)
```
docker run -v /tmp/app.sock:/app/app.sock blogapi
```

### Run with other Docker images
This Docker image is designed to work with Nginx setup by unix socket file. The Nginx could be installed and configured, or spun-up by a Docker image.

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
