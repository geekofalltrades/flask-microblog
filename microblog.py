from flask import Flask, render_template, request, \
    redirect, url_for, flash, session
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.seasurf import SeaSurf
from flask.ext.mail import Mail, Message
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from passlib.hash import bcrypt
from sqlalchemy import desc
from datetime import datetime
from random import choice
import string
from gevent.wsgi import WSGIServer

app = Flask(__name__)
app.config.from_pyfile('default_config.py')
app.config.from_envvar('MICROBLOG_CONFIG', silent=True)

db = SQLAlchemy(app)

csrf = SeaSurf(app)

migrate = Migrate(app, db)

mail = Mail(app)

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
    email = db.Column(db.String(255), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    posts = db.relationship('Post', backref="author")

    def __init__(self, username=None, password=None, email=None):
        self.username = username
        self.password = password
        self.email = email
        self.timestamp = datetime.utcnow()


class TempUser(db.Model):
    """A temporary user. These are created when a new user registers, but
    hasn't yet confirmed their registration.
    """
    __tablename__ = 'temp_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    regkey = db.Column(db.String(32), unique=True, nullable=False)

    def __init__(self, username=None, password=None, email=None):
        self.username = username
        self.password = password
        self.email = email
        self.timestamp = datetime.utcnow()
        self.regkey = \
            ''.join(choice(string.letters + string.digits) for i in range(32))


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
            try:
                write_post(
                    request.form['title'],
                    request.form['body'],
                    session.get('user_id', None),
                )
            except IntegrityError:
                flash(
                    "Posts must have a title and a body.",
                    category="error"
                )
                return redirect(url_for('add_view'))
            return redirect(url_for('list_view'))
        else:
            return redirect(url_for('add_view'))
    else:
        return render_template('add.html')


@app.route("/login", methods=['GET', 'POST'])
def login_view():
    """Allows a user to log in."""
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if not user:
            user = TempUser.query.filter_by(
                username=request.form['username']).first()
            if not user:
                flash("This user does not exist.", category="error")
            else:
                message = "This username is registered, but not confirmed. "
                message += "Please check the email address you registered with "
                message += "for a confirmation message. You must confirm your "
                message += "registration before you can use your account."
                flash(message, category='error')
            return redirect(url_for('login_view'))
        elif bcrypt.verify(request.form['password'], user.password):
            session['logged_in'] = True
            session['username'] = user.username
            session['user_id'] = user.id
            return redirect(url_for('list_view'))
        else:
            flash("Incorrect password.", category='error')
            return redirect(url_for('login_view'))
    else:
        return render_template('login.html')


@app.route("/logout")
def logout_view():
    """Logs a user out."""
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)

    return redirect(url_for('list_view'))


@app.route("/register", methods=['GET', 'POST'])
def register_view():
    """Allows a user to register for membership."""
    if request.method == 'POST':
        try:
            #request.form is an ImmutableMultiDict: it does not unpack
            #as expected (which is why **request.form is not used below)
            add_user(
                username=request.form['username'],
                password=request.form['password'],
                email=request.form['email']
            )
        except ValueError as e:
            for message in e.message:
                flash(message)
            return redirect(url_for('register_view'))
        else:
            msg = Message(
                "Confirm your account at Flask Microblog",
                sender=('Flask Microblog', 'mattscrapmail@gmail.com'),
                recipients=[request.form['email']]
            )
            msg.body = """
You're almost ready to start using your Flask Microblog account.
Simply click the following link within the next thirty minutes to confirm your registration:

%s

If you did not register for a Flask Microblog account, you can safely ignore this message.
""" % url_for(
    'confirm_view',
    regkey=TempUser.query.filter_by(username=request.form['username']).
                                    first().regkey,
    _external=True)
            mail.send(msg)
            return render_template(
                'confirmation_instructions.html',
                email=request.form['email']
            )
        return render_template('register.html')
    else:
        return render_template('register.html')


@app.route("/confirm/<regkey>")
def confirm_view(regkey):
    """Allows a user to confirm their registration after registering for
    registration.
    """
    temp_user = TempUser.query.filter_by(regkey=regkey).first()

    if temp_user:
        db.session.delete(temp_user)
        db.session.commit()
        add_user(
            username=temp_user.username,
            password=temp_user.password,
            email=temp_user.email,
            confirm=False
        )

    return render_template('confirm.html', user=temp_user)


@app.errorhandler(404)
def page_not_found(error):
    return 'Attempted to access %s' % format(request.url), 404


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


def add_user(username=None, password=None, email=None, confirm=True, key=None):
    """Add a new user to the database's 'user' table. If confirm is
    specified as false, we skip the confirmation step for this user and
    add them directly as an active user. If key is provided, any TempUser
    added is forced to have that regkey. (For testing purposes.)"""
    #Pre-checking has become necessary because SQLAlchemy's IntegrityError
    #doesn't convey enough information by itself about the nature of the
    #error.
    messages = []

    #First, validate the form input.
    if not username:
        messages.append("Username is a required field.")
    if not password:
        messages.append("Password is a required field.")
    if not email:
        messages.append("Email address is a required field.")
    if messages:
        raise ValueError(messages)

    #If form input was good, assure that the necessary fields are unique
    #Check the users table...
    for user in [User.query.filter_by(username=username).first(),
                 TempUser.query.filter_by(username=username).first()]:
        if user:
            messages.append("This username is taken.")
            break

    for user in [User.query.filter_by(email=email).first(),
                 TempUser.query.filter_by(email=email).first()]:
        if user:
            messages.append(
                "This email address is already registered to another user.")
            break

    if messages:
        raise ValueError(messages)

    if confirm:
        new_user = TempUser(username, bcrypt.encrypt(password), email)
        if key:
            new_user.regkey = key
        #The only field left unvalidated is the reg_key field. We'll attempt
        #to insert until we succeed in generating a unique one.
        while True:
            try:
                db.session.add(new_user)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                new_user = TempUser(username, bcrypt.encrypt(password), email)
                #new_user.generate_reg_key()
                continue
            else:
                break
    else:
        if not bcrypt.identify(password):
            password = bcrypt.encrypt(password)
        new_user = User(username, password, email)
        db.session.add(new_user)
        db.session.commit()


class NotFoundError(SQLAlchemyError):
    """Exception raised when the expected item is not present in a table
    query response.
    """
    pass


if __name__ == '__main__':
    #manager.run()
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
