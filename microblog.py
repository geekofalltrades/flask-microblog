from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+psycopg2:///microblog'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)


class Post(db.Model):
    """A blog post."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)

    def __init__(self, title, body):
        self.title = title
        self.body = body
        self.timestamp = datetime.now()


def write_post(title, body):
    """Create a new blog post."""
    new_post = Post(title, body)

    db.session.add(new_post)
    db.session.commit()


def read_posts():
    """Retrieve all blog posts in reverse chronological order."""
    posts = Post.query.all()
    posts.reverse()
    return posts
