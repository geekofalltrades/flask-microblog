from flask import Flask, render_template, request, \
    redirect, url_for, flash, session
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.seasurf import SeaSurf
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from passlib.hash import bcrypt
from sqlalchemy import desc
from datetime import datetime

app = Flask(__name__)
app.config.from_pyfile('default_config.py')
app.config.from_envvar('MICROBLOG_CONFIG', silent=True)

db = SQLAlchemy(app)

csrf = SeaSurf(app)

migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


class Post(db.Model):
    """A blog post."""
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True, nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    auth_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, title=None, body=None, auth_id=None):
        self.title = title
        self.body = body
        self.auth_id = auth_id
        self.timestamp = datetime.utcnow()


class User(db.Model):
    """A user."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    posts = db.relationship('Post', backref="author")

    def __init__(self, username=username, password=password):
        self.username = username
        self.password = password
        self.timestamp = datetime.utcnow()


@app.route("/")
def list_view():
    """The home page: a list of all posts in reverse chronological order.
    """
    posts = read_posts()
    return render_template('list.html', posts=posts)


@app.route("/posts/<id>")
def permalink_view(id):
    """Fetch and render a single blog post."""
    post = read_post(id)
    return render_template('permalink.html', post=post)


@app.route("/add", methods=['GET', 'POST'])
def add_view():
    """Add a new post. If the request method is GET, returns a form that
    allows the user to add a new post. If the request method is POST,
    validates the incoming post, then inserts it and redirects the user
    to the homepage (list view)."""
    if request.method == 'POST':
        if session.get('logged_in', False):
            write_post(
                request.form['title'],
                request.form['body'],
                session.get('user_id', None),
            )
        else:
            flash(
                "You must be logged in to perform that action.",
                category="error"
            )
        return redirect(url_for('list_view'))
    else:
        return render_template('add.html')


@app.route("/login", methods=['GET', 'POST'])
def login_view():
    """Allows a user to log in."""
    if request.method == 'POST':
        try:
            password, user_id = read_user(request.form['username'])
        except NotFoundError as e:
            flash(e.message, category="error")
            return redirect(url_for('login_view'))
        else:
            if bcrypt.verify(request.form['password'], password):
                session['logged_in'] = True
                session['username'] = request.form['username']
                session['user_id'] = user_id
            else:
                flash("Incorrect password.", category='error')
                return redirect(url_for('login_view'))
            return redirect(url_for('list_view'))
    else:
        return render_template('login.html')


@app.route("/logout")
def logout_view():
    """Logs a user out."""
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)

    return redirect(url_for('list_view'))


@app.route("/register")
def register_view():
    """Allows a user to register for membership."""
    return "<h1>Nope.</h1>"


def write_post(title=None, body=None, auth_id=None):
    """Create a new blog post."""
    if not title:
        title = None
    if not body:
        body = None
    if not auth_id:
        auth_id = None

    new_post = Post(title, body, auth_id)

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
        raise NotFoundError("There exists no post with the specified id.")
    return post


def add_user(username, password):
    """Add a new user to the database's 'user' table."""
    new_user = User(username, bcrypt.encrypt(password))

    db.session.add(new_user)
    db.session.commit()


def read_user(username):
    """Fetch the password associated with a username from the database."""
    user = User.query.filter_by(username=username).first()
    if user is None:
        raise NotFoundError("This user does not exist.")
    return user.password, user.id


def _login(username, password):
    """Allows a user to log in programmatically. For testing."""

    dbpass, user_id = read_user(username)
    if bcrypt.verify(password, dbpass):
        session['logged_in'] = True
        session['username'] = request.form['username']
        session['user_id'] = user_id
    else:
        raise KeyError("Incorrect password in _login.")


def _logout():
    """Allows a user to log out programmatically. For testing."""

    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)


class NotFoundError(SQLAlchemyError):
    """Exception raised when the expected item is not present in a table
    query response.
    """
    pass

if __name__ == '__main__':
    manager.run()
