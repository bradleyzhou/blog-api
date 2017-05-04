# bradleyzhou.com
Source code of the website www.bradleyzhou.com

## API Design Draft
* Base URL: https://blog.bradleyzhou.com/api/v1.0

* Get a list of APIs
```
GET https://blog.bradleyzhou.com/api/v1.0
```

* Get all posts
```
GET /posts/
```

* Get a specific post
```
GET /posts/3291
```

* Create a new post
```
POST /posts/
```

* Update/Modify a specific post
```
PUT /posts/3291
```

* Delete a post
```
DELETE /posts/3291
```

* Delete all posts
```
DELETE /posts/
```

* Get comments of a post
```
GET /posts/3291/comments/
```

* Get a user
```
GET /users/492
```

* GET posts by a user
```
GET /users/492/posts/
```
