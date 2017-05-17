import os
import re
from string import letters
import webapp2
import jinja2
from google.appengine.ext import db
import hashlib
import hmac

# Secret for encrypting Passwords

SECRET = "fart"

# Location of Templates

template_dir = os.path.join(os.path.dirname(__file__), 'template')
jinja_env = \
    jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                       autoescape=True)


# Post Database


class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.StringProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    post_likes = db.IntegerProperty(required=True)

# this function genrate a secure value to be stored in a cookie.


def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(SECRET, val).hexdigest())

# this function check if the value and its secure version actually matches,
#     if true it returns the value itself else False


def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val
    else:
        return False


def blog_key(name='default'):
    return db.Key.from_path('blog', name)

# Database Model for Comments


class Comments(db.Model):
    author = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

# Database Model for Likes


class Likes(db.Model):
    user_id = db.IntegerProperty(required=True)

# Database Model for User


class User_db(db.Model):
    email = db.EmailProperty(required=True)
    username = db.StringProperty(required=True)
    password_hash = db.StringProperty(required=True)
    register_Date = db.DateTimeProperty(auto_now_add=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    # This funtion render view of html using template.

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    # Set Secure Cookie on browser

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie', '%s=%s; Path=/' % (str(name), str(cookie_val)))
    # Read Secure Cookie from browser

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)
# Set the username of user Securely in the browser cookies,
#             and redirect the user to the welcome page

    def login(self, user):
        self.set_secure_cookie('username', user.username)
        self.redirect('/welcome')

    def logged(self):
        username = self.read_secure_cookie('username')
        if username:
            user = User_db.all().filter('username = ', username).get()
            if user:
                return username
            else:
                return False
        else:
            return False
# check if user has alredy liked the post or not
#             if liked then returns the like from Like table
#             else return False

    def liked(self, username, post_key):
        if username:
            user = db.GqlQuery(
                'SELECT * FROM User_db WHERE username = :user',
                user=username)
            user_id = user.get().key().id()
            like = Likes.all()
            like.ancestor(post_key)
            like.filter('user_id = ', user_id)
            like = like.get()
            if like:
                return like
            else:
                return False
        else:
            return False

# genrate Hash for password for storing it Securely in database.


def hash_password(password):
    return hashlib.sha256(password + SECRET).hexdigest()

# get request Handler for publishing main index page


class MainPage(Handler):
    def get(self):
        posts = \
            db.GqlQuery('SELECT * FROM Post ORDER BY created DESC LIMIT 10')
        self.render('front.html', posts=posts, user=self.logged())

# get request Handler for publishing main welcome page


class Welcome(Handler):
    def get(self):
        posts = \
            db.GqlQuery('SELECT * FROM Post ORDER BY created DESC LIMIT 10')
        self.render('welcome.html', posts=posts, user=self.logged())


class PostPage(Handler):
    # get request Handler for publishing view post page
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        comments = Comments.all()
        comments.ancestor(key)
        comments.order('last_modified')
        username = self.logged()
        like = self.liked(username, key)
        self.render('post.html', post=post, user=username,
                    comments=comments, like=like)
# post request listning for new comments from post page

    def post(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        user = self.logged()
        content = self.request.get('comment')
        if user:
            if content:
                content = content.replace('\n', '<br>')
                comment = Comments(parent=key, author=user,
                                   content=content)
                comment.put()
                self.redirect('/%s' % str(post.key().id()))
            else:
                self.redirect('/%s?error=emptyCmnt'
                              % str(post.key().id()))
        else:
            self.redirect('/%s?error="notLogged"'
                          % str(post.key().id()))


class Like(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        user = self.logged()
        if user:
            like = self.liked(user, key)
            if not like:
                user = db.GqlQuery(
                    'SELECT * FROM User_db WHERE username = :user', user=user)
                user = user.get()
                user_id = user.key().id()
                if post.author == self.logged():
                    self.redirect('/%s?error=ownPost' % post_id)
                else:
                    new_like = Likes(parent=key, user_id=user_id)
                    new_like.put()
                    post.post_likes += 1
                    post.put()
                    self.redirect('/%s' % post_id)
            elif like:
                like.delete()
                post.post_likes -= 1
                post.put()
                self.redirect('/%s' % post_id)
        else:
            self.redirect('/%s?error=notLogged' % post_id)


class DeletePost(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        user = self.logged()
        if post.author == user:
            if not post:
                self.error(404)
            else:
                self.render('post.html', post=post)
                post.delete()
                self.redirect('/')
        else:
            self.redirect('/%s?error=notPostOwner')


class NewPost(Handler):
    def get(self):
        if self.logged():
            self.render('new.html', user=self.logged())
        else:
            self.redirect('/login')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        if subject and content:
            if self.logged():
                content = content.replace('\n', '<br>')
                p = Post(parent=blog_key(), subject=subject,
                         content=content, author=self.logged(),
                         post_likes=0)
                p.put()
                self.redirect('/%s' % str(p.key().id()))
            else:
                self.redirect('/login')
        else:
            self.render('new.html', user=self.logged(),
                        error="Fields Can't Be Enpty")


class EditPost(Handler):
    def get(self, post_id):
        user = self.logged()
        if user:
            pkey = db.Key.from_path('Post', int(post_id),
                                    parent=blog_key())
            post = db.get(pkey)
            if not post:
                self.error(404)
                return
            if user != post.author:
                self.redirect('/%s?error=notPostOwner' % post_id)
            else:
                self.render('edit.html', user=self.logged(), post=post)
        else:
            self.redirect('/login')

    def post(self, post_id):
        subject = self.request.get('subject')
        content = self.request.get('content')
        user = self.logged()
        if subject and content:
            if user:
                pkey = db.Key.from_path(
                    'Post', int(post_id),
                    parent=blog_key())
                post = db.get(pkey)
                if not post:
                    self.error(404)
                    return
                if user != post.author:
                    self.redirect('/%s?error=notPostOwner' % post_id)
                else:
                    content = content.replace('\n', '<br>')
                    post.content = content
                    post.subject = subject
                    post.put()
                    self.redirect('/%s' % post_id)
            else:
                self.redirect('/%s?error=notLogged' % pkey)
        else:
            self.render('new.html', user=self.logged(),
                        error="Fields Can't Be Enpty")


class DeleteComment(Handler):
    def get(self, post_id, comment_id):
        user = self.logged()
        if user:
            pkey = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(pkey)
            if not post:
                self.error(404)
                return
            key = db.Key.from_path('Comments', int(comment_id), parent=pkey)
            comment = db.get(key)
            if user == comment.author:
                comment.delete()
                self.redirect('/%s' % post_id)
            else:
                self.redirect('/%s?error=notCmntOwner' % post_id)
        else:
            self.redirect('/%s?error="notLogged"' % post_id)


class EditComment(Handler):
    def get(self, post_id, comment_id):
        user = self.logged()
        if user:
            pkey = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(pkey)
            if not post:
                self.error(404)
                return
            key = db.Key.from_path('Comments', int(comment_id), parent=pkey)
            comment = db.get(key)
            if user == comment.author:
                self.render('editcomment.html', user=user, comment=comment)
            else:
                self.redirect('/%s?error=notCmntOwner' % post_id)

    def post(self, post_id, comment_id):
        user = self.logged()
        if user:
            pkey = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(pkey)
            if not post:
                self.error(404)
                return
            key = db.Key.from_path('Comments', int(comment_id), parent=pkey)
            comment = db.get(key)
            if user == comment.author:
                content = self.request.get('comment')
                if content:
                    comment.content = content
                    comment.put()
                    self.redirect('/%s' % post_id)
                else:
                    self.redirect('/%s?error=emptyCmnt' % post_id)
            else:
                self.redirect('/%s?error=notCmntOwner' % post_id)


class Signup(Handler):
    def get(self):
        self.render('signup.html')

    def post(self):
        email = self.request.get('email')
        username = self.request.get('username')
        password = self.request.get('password')
        vpass = self.request.get('verify')
        if not email and username and password and vpass:
            error = ' All fields are required'
            self.render('signup.html', error=error)
        elif not password == vpass:
            error = 'Passwords do not match'
            self.render('signup.html', error=error)
        else:
            if User_db.all().filter('email = ', email).get():
                error = 'Email Already existing'
                self.render('signup.html', error=error)
            elif User_db.all().filter('username = ', username).get():
                error = 'Username Already Taken'
                self.render('signup.html', error=error)
            else:
                password = hash_password(password)
                p = User_db(
                    email=email,
                    username=username,
                    password_hash=password)
                p.put()
                self.redirect('/welcome')


class Login(Handler):
    # renders the login page
    def get(self):
        self.render('login.html')
# request for username and password

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        if not username and password:
            error = ' Enter both password and username '
            self.render('login.html', error=error)
        else:
            user = User_db.all().filter('username = ', username).get()
            if not user:

                error = 'User does not exsist !'
                self.render('login.html', error=error)
            else:
                password = hash_password(password)
                if user.password_hash != password:
                    error = 'Password Incorrect !'
                    self.render('login.html', error=error)
                else:
                    self.login(user)

# check if user is alredy logged out or not
#             if not then logout user


class Logout(Handler):
    def get(self):
        if self.logged():
            self.set_secure_cookie('username', '')
            self.redirect('/login')
        else:
            self.redirect('/login')


app = webapp2.WSGIApplication([
    ('/?', MainPage),
    ('/signup', Signup),
    ('/login', Login),
    ('/welcome', Welcome),
    ('/(\d+)', PostPage),
    ('/newpost', NewPost),
    ('/delete:(\d+)', DeletePost),
    ('/edit:(\d+)', EditPost),
    ('/editcomment:(\d+)&(\d+)', EditComment),
    ('/deletecomment:(\d+)/(\d+)', DeleteComment),
    ('/like:(\d+)', Like),
    ('/logout', Logout),
], debug=True)

