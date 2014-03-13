from flask import Flask, render_template, request, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.seasurf import SeaSurf
from flaskext.bcrpyt import Bcrypt
from sqlalchemy import desc
from datetime import datetime

app = Flask(__name__)
csrf = SeaSurf(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+psycopg2:///microblog'
#app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


class Post(db.Model):
    """A blog post."""
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    auth_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.timestamp = datetime.utcnow()


class User(db.Model):
    """A user."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime)
    posts = db.relationship('Post', backref="author")

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.timestamp = datetime.utcnow()


@app.route("/")
def list_view():
    """The home page: a list of all posts in reverse chronological order.
    """
    raw_posts = read_posts()
    posts = []
    for post in raw_posts:
        posts.append({
            'title': post.title,
            'body': post.body,
            'date': post.timestamp,
            'id': post.id,
        })

    return render_template('list.html', posts=posts)


@app.route("/posts/<id>")
def permalink_view(id):
    """Fetch and render a single blog post."""
    raw_post = read_post(id)
    post = {
        'title': raw_post.title,
        'body': raw_post.body,
        'date': raw_post.timestamp,
        'id': raw_post.id,
    }

    return render_template('permalink.html', post=post)


@app.route("/add", methods=['GET', 'POST'])
def add_view():
    """Add a new post. If the request method is GET, returns a form that
    allows the user to add a new post. If the request method is POST,
    validates the incoming post, then inserts it and redirects the user
    to the homepage (list view)."""
    if request.method == 'POST':
        if session['logged_in']:
            write_post(
                request.form['title'],
                request.form['body'],
            )
        return redirect(url_for('list_view'))
    else:
        return render_template('add.html')


@app.route("/login", methods=['GET', 'POST'])
def login_view():
    """Allows a user to log in."""
    if request.method == 'POST':
        try:
            password = read_user(request.form['username'])
        except:
            pass
        else:
            if bcrypt.check_password_hash(
                    password, request.form['password']):
                pass
                #log in
            else:
                pass
                #return some sort of error
        return redirect(url_for('list_view'))
    else:
        return render_template('login.html')


def write_post(title, body):
    """Create a new blog post."""
    new_post = Post(title, body)

    db.session.add(new_post)
    db.session.commit()


def read_posts():
    """Retrieve all blog posts in reverse chronological order."""
    posts = Post.query.order_by(desc(Post.timestamp)).all()
    return posts


def read_post(id):
    """Retrieve a single post by its id."""
    post = Post.query.filter_by(id=str(id)).first()
    if post is None:
        raise IndexError("There exists no post with the specified id.")
    return post


def add_user(username, password):
    """Add a new user to the database's 'user' table."""
    new_user = User(username, bcrypt.generate_password_hash(password))

    db.session.add(new_user)
    db.session.commit()


def read_user(username):
    """Fetch the password associated with a username from the database."""
    password = User.query.filter_by(username=username).first()
    return password


if __name__ == '__main__':
    manager.run()
