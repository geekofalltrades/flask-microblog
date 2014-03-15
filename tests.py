import unittest
import microblog
from sqlalchemy.exc import IntegrityError
import flask
import re


class TestWritePost(unittest.TestCase):
    """Test the write_post function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.auth_id = \
            microblog.User.query.filter_by(username='admin').first().id
        self.title = "A Blog Title"
        self.body = "A Blog Body"

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_write_post(self):
        """Write a post and then verify that it appeared at the top of
        the microblog.
        """
        microblog.write_post(self.title, self.body, self.auth_id)
        posts = microblog.read_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, self.title)
        self.assertEqual(posts[0].body, self.body)
        self.assertEqual(posts[0].auth_id, self.auth_id)

    def test_write_post_no_title(self):
        """Attempt to submit a post that does not have a title and assert
        that the operation raises the proper IntegrityError and didn't
        add any data to the database.
        """
        self.assertRaises(IntegrityError, microblog.write_post,
            ('', self.body, self.auth_id))

    def test_write_post_no_body(self):
        """Attempt to submit a post that does not have a body and assert
        that the operation raises the proper IntegrityError and didn't
        add any data to the database.
        """
        self.assertRaises(IntegrityError, microblog.write_post,
            (self.title, '', self.auth_id))

    def test_write_post_no_author(self):
        """Attempt to submit a post that does not have an auth_id and
        assert that the operation raises the proper IntegrityError and
        didn't add any data to the database.
        """
        self.assertRaises(IntegrityError, microblog.write_post,
            (self.title, self.body, ''))

    def test_write_post_nonexistant_author(self):
        """Attempt to submit a post that does not has an auth_id not
        corresponding to an existing user. Assert that the operation
        raises the proper IntegrityError and didn't add any data to the
        database.
        """
        self.assertRaises(IntegrityError, microblog.write_post,
            (self.title, self.body, '4'))


class TestReadPosts(unittest.TestCase):
    """Test the read_posts function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.auth_id = \
            microblog.User.query.filter_by(username='admin').first().id
        self.posts = {
            'A Blog Title': 'A Blog Body',
            'Eye-Catching Headline': 'Earth-Shattering Content',
        }
        for key, val in self.posts.items():
            microblog.write_post(key, val, self.auth_id)

        self.title = "Another Blog Title"
        self.body = "Another Blog Body"

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_read_posts(self):
        """Read the number of posts we have and verify that they contain
        the expected content.
        """
        posts = microblog.read_posts()
        self.assertEqual(len(posts), 2)
        for post in posts:
            self.assertIn(post.title, self.posts)
            self.assertEqual(post.body, self.posts[post.title])

    def test_read_posts_order(self):
        """Add a new post, then verify that calling read_posts() places
        it at the top of the list of posts it returns.
        """
        microblog.write_post(self.title, self.body, self.auth_id)
        posts = microblog.read_posts()
        self.assertEqual(len(posts), 3)
        self.assertEqual(posts[0].title, self.title)
        self.assertEqual(posts[0].body, self.body)
        self.assertEqual(posts[0].auth_id, self.auth_id)


class TestReadPost(unittest.TestCase):
    """Test the read_post function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.auth_id = \
            microblog.User.query.filter_by(username='admin').first().id
        self.posts = {
            "Blog 1": "A Blog Body",
            "Blog 2": "Another Blog Body",
            "Blog 3": "A Third Blog Body",
        }

        for title, body in sorted(self.posts.items(), key=lambda x: x[0]):
            microblog.write_post(title, body, self.auth_id)

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_read_post(self):
        """Add several posts and attempt to fetch one by its id."""
        post = microblog.read_post(2)
        self.assertIn(post.title, self.posts)
        self.assertEqual(post.body, self.posts[post.title])

    def test_read_nonexistant_post(self):
        """Add several posts, then attempt to fetch a post by an id that
        shouldn't exist."""
        self.assertRaises(microblog.NotFoundError, microblog.read_post, 4)


class TestAddUser(unittest.TestCase):
    """Test the add_user function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        self.good_users = {
            'user1': ('user1', 'password', 'email1@email.com'),
            'user2': ('user2', 'password', 'email2@email.com'),
            'user3': ('user3', 'password', 'email3@email.com'),
        }
        self.bad_users = {
            'username_collision': ('user1', 'password', 'email@email.com'),
            'email_collision': ('user', 'password', 'email1@email.com'),
            'no_username': ('', 'password', 'email@email.com'),
            'no_password': ('user', '', 'email@email.com'),
            'no_email': ('user', 'password', '')
        }

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_add_with_confirm(self):
        """Add several valid users to the database with the confirm flag
        set to true and verify that they appear in the temp_users table
        as expected.
        """
        for key, val in self.good_users.iteritems():
            microblog.add_user(*val)

        users = microblog.TempUser.query.all()
        self.assertEqual(len(users), len(self.good_users))

    def test_add_with_confirm_key_collision(self):
        """Add several valid users to the database with the confirm
        flag set. Ensure that a collision between regkeys in the temp_users
        table is correctly handled.
        """
        regkey = ''.join('f' for i in range(32))
        for key, val in self.good_users.iteritems():
            microblog.add_user(*val, key=regkey)

        users = microblog.TempUser.query.all()
        self.assertEqual(len(users), len(self.good_users))
        regkeys = set()
        for user in users:
            regkeys.add(user.regkey)

        self.assertIn(regkey, regkeys)
        self.assertEqual(len(users), len(regkeys))

    def test_add_without_confirm(self):
        """Add several valid users to the database without the confirm
        flag and verify that they appear in the users table as expected.
        """
        for key, val in self.good_users.iteritems():
            microblog.add_user(*val, confirm=False)

        users = microblog.User.query.all()
        self.assertEqual(len(users), len(self.good_users))

    def test_add_non_unique_username(self):
        """Add several valid users, then add a user whose username collides
        with one already in the database.
        """
        for key, val in self.good_users.iteritems():
            microblog.add_user(*val)

        self.assertRaisesRegexp(
            ValueError,
            r'This username is taken.',
            microblog.add_user,
            *self.bad_users['username_collision']
        )

    def test_add_non_unique_email(self):
        """Add several valid users, then add a user whose email address
        collides with one already in the database.
        """
        for key, val in self.good_users.iteritems():
            microblog.add_user(*val)

        self.assertRaisesRegexp(
            ValueError,
            r'This email address is already registered to another user.',
            microblog.add_user,
            *self.bad_users['email_collision']
        )

    def test_add_no_username(self):
        """Attempt to add a user who has no username."""
        self.assertRaisesRegexp(
            ValueError,
            r'Username is a required field.',
            microblog.add_user,
            *self.bad_users['no_username']
        )

    def test_add_no_password(self):
        """Attempt to add a user who has no password."""
        self.assertRaisesRegexp(
            ValueError,
            r'Password is a required field.',
            microblog.add_user,
            *self.bad_users['no_password']
        )

    def test_add_no_email(self):
        """Attempt to add a user who has no email address."""
        self.assertRaisesRegexp(
            ValueError,
            r'Email address is a required field.',
            microblog.add_user,
            *self.bad_users['no_email']
        )


class TestLoginView(unittest.TestCase):
    """Test the login view (login_view function) of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.user_id = \
            microblog.User.query.filter_by(username='admin').first().id

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_login_get(self):
        """Assure that the proper HTML elements are present on the page
        returned by a GET request to the login view.
        """
        with microblog.app.test_client() as c:
            request = c.get('/login')
            self.assertIn('_csrf_token', request.data)
            self.assertIn('username', request.data)
            self.assertIn('password', request.data)
            self.assertIn('Log In', request.data)

    def test_login_post(self):
        """Assure that a POST request to the login page logs the user in.
        """
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            self.assertTrue(flask.session['logged_in'])
            self.assertEqual(flask.session['username'], data['username'])
            self.assertEqual(flask.session['user_id'], self.user_id)

    def test_login_not_confirmed(self):
        """Verify that attempting to log in as a user who has registered,
        but not verified their registration, displays the appropriate
        error message.
        """
        microblog.add_user('user', 'password', 'email2@email.com')
        self.unconfirmed_id = \
            microblog.TempUser.query.filter_by(username='user').first().id
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'user',
                'password': 'password',
            }
            request = c.post('/login', data=data, follow_redirects=True)
            self.assertIn(
                "This username is registered, but not confirmed.",
                request.data
            )
            self.assertIn('_csrf_token', request.data)
            self.assertIn('username', request.data)
            self.assertIn('password', request.data)
            self.assertIn('Log In', request.data)

    def test_login_bad_username(self):
        """Verify that a POST to the login page with a nonexistant
        username flashes the appropriate on-screen message.
        """
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'fff',
                'password': 'password',
            }
            request = c.post('/login', data=data, follow_redirects=True)
            self.assertIn("This user does not exist.", request.data)
            self.assertIn('_csrf_token', request.data)
            self.assertIn('username', request.data)
            self.assertIn('password', request.data)
            self.assertIn('Log In', request.data)

    def test_login_bad_password(self):
        """Verify that a POST to the login page with an incorrect password
        flashes the appropriate on-screen message.
        """
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'wrongpass',
            }
            request = c.post('/login', data=data, follow_redirects=True)
            self.assertIn("Incorrect password.", request.data)
            self.assertIn('_csrf_token', request.data)
            self.assertIn('username', request.data)
            self.assertIn('password', request.data)
            self.assertIn('Log In', request.data)


class TestLogoutView(unittest.TestCase):
    """Test the logout view (logout_view function) of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.user_id = \
            microblog.User.query.filter_by(username='admin').first().id

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_logout(self):
        """Assure that a call to the logout page logs the user out."""
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            c.get('/logout')
            self.assertFalse(flask.session.get('logged_in', None))
            self.assertNotEqual(
                flask.session.get('username', None), data['username'])
            self.assertNotEqual(
                flask.session.get('user_id', None), self.user_id)


class TestListView(unittest.TestCase):
    """Test the list view (list_view function) of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.user_id = \
            microblog.User.query.filter_by(username='admin').first().id
        self.posts = {
            "Blog 1": "A Blog Body",
            "Blog 2": "Another Blog Body",
            "Blog 3": "A Third Blog Body",
        }
        for title, body in sorted(self.posts.items(), key=lambda x: x[0]):
            microblog.write_post(title, body, self.user_id)

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_list_view(self):
        """Test that the list view contains inserted posts and that they
        are in the correct order (most recently inserted post at the top
        of the list).
        """
        with microblog.app.test_client() as c:
            request = c.get('/')

            match = re.search(
                r'by admin on.+?by admin on.+?by admin on',
                request.data,

                #Ha. Ha. Ha. The regex metacharacter that literally and
                #unambiguously means "any character" does not match newlines
                #by default in Python. What a delightful and not at all
                #dumb or infuriating convention.
                re.DOTALL
            )
            self.assertTrue(match)

            search_string = \
                r'({2}).*?({1}).*?({0})'.format(*sorted(list(self.posts)))
            match = re.search(search_string, request.data, re.DOTALL)
            self.assertTrue(match)

            search_string = \
                r'({Blog 3}).*?({Blog 2}).*?({Blog 1})'.format(**self.posts)
            match = re.search(search_string, request.data, re.DOTALL)
            self.assertTrue(match)

    def test_list_view_logged_in(self):
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            request = c.get('/')
            self.assertIn('Logged in as admin', request.data)

    def test_list_view_logged_out(self):
        with microblog.app.test_client() as c:
            request = c.get('/')
            self.assertIn('Not logged in', request.data)


class TestAddView(unittest.TestCase):
    """Test the add view (add_view function) of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.user_id = \
            microblog.User.query.filter_by(username='admin').first().id
        self.post = {
            'title': 'Blog 1',
            'body': 'O Blarghag',
            'auth_id': self.user_id,
        }

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_add_view_logged_in(self):
        """Asser that the version of the add page delivered when logged
        in presents the user with form options that allow them to create
        a new post.
        """
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            request = c.get('/add')
            self.assertIn('_csrf_token', request.data)
            self.assertIn('title', request.data)
            self.assertIn('body', request.data)
            self.assertIn('submit', request.data)

    def test_add_view_logged_out(self):
        """Assert that the version of the add page we get when logged out
        is the version that does not include a form.
        """
        with microblog.app.test_client() as c:
            request = c.get('/add')
            self.assertIn('Sorry.', request.data)
            self.assertIn(
                'You must be logged in to create new posts.', request.data)

    def test_add_view_post(self):
        """Post a request to the view page (when logged in) and verify
        that we're redirected to the home page and that our new post
        appears on the home page.
        """
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            request = c.post(
                '/add', data=self.post, follow_redirects=True)
            self.assertIn('Blog 1', request.data)
            self.assertIn('by admin on', request.data)
            self.assertIn('O Blarghag', request.data)

    def test_add_view_post_not_logged_in(self):
        """Verify that attempting to send a post request to the add view
        while not logged in returns us to the logged out version of the
        add view.
        """
        with microblog.app.test_client() as c:
            request = c.post('/add', data=self.post, follow_redirects=True)
            self.assertIn('Sorry.', request.data)
            self.assertIn(
                'You must be logged in to create new posts.', request.data)

    def test_add_view_no_body(self):
        """Verify that attempting to submit a post with no body returns
        us to the add view with an error message.
        """
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            self.post['body'] = ''
            request = c.post(
                '/add', data=self.post, follow_redirects=True)
            self.assertIn('Posts must have a title and a body.', request.data)
            self.assertIn('_csrf_token', request.data)
            self.assertIn('title', request.data)
            self.assertIn('body', request.data)
            self.assertIn('submit', request.data)

    def test_add_view_no_title(self):
        """Verify that attempting to submit a post with no title returns
        us to the add view with an error message.
        """
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            self.post['title'] = ''
            request = c.post(
                '/add', data=self.post, follow_redirects=True)
            self.assertIn('Posts must have a title and a body.', request.data)
            self.assertIn('_csrf_token', request.data)
            self.assertIn('title', request.data)
            self.assertIn('body', request.data)
            self.assertIn('submit', request.data)


class TestPermalinkView(unittest.TestCase):
    """Test the permalink view (permalink_view function) of the microblog.
    """
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com', confirm=False)
        self.user_id = \
            microblog.User.query.filter_by(username='admin').first().id
        self.posts = {
            "Blog 1": "A Blog Body",
            "Blog 2": "Another Blog Body",
            "Blog 3": "A Third Blog Body",
        }
        for title, body in sorted(self.posts.items(), key=lambda x: x[0]):
            microblog.write_post(title, body, self.user_id)

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_permalink_view(self):
        with microblog.app.test_client() as c:
            request = c.get('/posts/1')
            self.assertIn('Blog 1', request.data)
            self.assertIn('by admin on', request.data)
            self.assertIn(self.posts['Blog 1'], request.data)

    def test_permalink_view_logged_in(self):
        with microblog.app.test_client() as c:
            data = {
               # '_csrf_token': flask.session['_csrf_token'],
                'username': 'admin',
                'password': 'password',
            }
            c.post('/login', data=data)
            request = c.get('/posts/1')
            self.assertIn('Logged in as admin', request.data)

    def test_permalink_view_logged_out(self):
        with microblog.app.test_client() as c:
            request = c.get('/posts/1')
            self.assertIn('Not logged in', request.data)


class TestRegisterView(unittest.TestCase):
    """Test the register view (register_view function) of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        self.user = {
            'username': 'admin',
            'password': 'password',
            'email': 'email@email.com',
        }
        self.bad_users = {
            'username_collision':
            {
                'username': 'admin',
                'password': 'password',
                'email': 'email2@email.com',
            },
            'blank_fields':
            {
                'username': '',
                'password': '',
                'email': '',
            },
        }

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_register_get(self):
        """Verify that a get request to the register view displays the
        registration form.
        """
        pass

    def test_register_post(self):
        """Verify that a post request to the register form (with valid
        credentials) registers a new user.
        """
        pass

    def test_flash_one_message(self):
        """Attempt to register an account invalid in one way (a username
        that is already taken) and verify that the error message returned
        is flashed on the screen.
        """
        pass

    def test_flash_multiple_messages(self):
        """Attempt to register an account that is invalid in multiple
        ways (all fields left blank) and verify that the error messages
        returned are all flashed on the screen.
        """
        pass


class TestConfirmView(unittest.TestCase):
    """Test the confirm view (confirm_view function) of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user(
            'admin', 'password', 'email@email.com')
        self.user_key = \
            microblog.TempUser.query.filter_by(username='admin').first().regkey

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_confirm_user(self):
        """Confirm a user and verify that they are moved from the temp_users
        table to the users table.
        """
        pass

    def test_confirm_user_invalid_key(self):
        """Attempt to confirm a user with an invalid key and verify that
        the appropriate error message is displayed.
        """
        pass


if __name__ == '__main__':
    unittest.main()
