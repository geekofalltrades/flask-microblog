from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from sqlalchemy import desc
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'postgresql+psycopg2:///microblog'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


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

    #Because the COMMIT_ON_TEARDOWN option doesn't appear to be working
    #(or possibly just doesn't work in the way I anticipated).
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


if __name__ == '__main__':
    manager.run()
