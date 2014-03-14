import unittest
import microblog
from sqlalchemy.exc import IntegrityError
import flask
import re


class TestWritePost(unittest.TestCase):
    """Test the write_post function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user('admin', 'password')
        password, self.auth_id = microblog.read_user('admin')
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
        microblog.add_user('admin', 'password')
        password, self.auth_id = microblog.read_user('admin')
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
        microblog.add_user('admin', 'password')
        password, self.auth_id = microblog.read_user('admin')
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


# class TestAddUser(unittest.TestCase):
#     """Test the add_user function of the microblog."""
#     def setUp(self):
#         microblog.db.create_all()
#         microblog.add_user('admin', 'password')
#         password, self.auth_id = microblog.read_user('admin')
#         self.users = {
#             'user1': 'pass1',
#             'user2': 'pass2',
#             'user3': 'pass3',
#         }

#     def tearDown(self):
#         microblog.db.session.remove()
#         microblog.db.drop_all()

#     def test_add_user(self):
#         """Add a user to the database and verify that that user has been
#         inserted into the database.
#         """
#         pass


class TestReadUser(unittest.TestCase):
    """Test the read_user function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user('admin', 'password')

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_fetch_existent_user(self):
        """Read a user from the database who is in the database."""
        pass

    def test_fetch_nonexistant_user(self):
        """Attempt to read a user from the database who is not in the
        database.
        """
        pass


class TestLoginView(unittest.TestCase):
    """Test the login view (login_view function) of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user('admin', 'password')
        password, self.user_id = microblog.read_user('admin')

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
        microblog.add_user('admin', 'password')
        password, self.user_id = microblog.read_user('admin')

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
        microblog.add_user('admin', 'password')
        password, self.user_id = microblog.read_user('admin')
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


# class TestAddView(unittest.TestCase):
#     """Test the add view (add_view function) of the microblog."""
#     def setUp(self):
#         microblog.db.create_all()
#         microblog.add_user('admin', 'password')
#         password, self.user_id = microblog.read_user('admin')

#     def tearDown(self):
#         microblog.db.session.remove()
#         microblog.db.drop_all()

#     def test_add_view_logged_in(self):
#         pass

#     def test_add_view_logged_out(self):
#         pass

#     def test_add_view_post(self):
#         pass

#     def test_add_view_no_body(self):
#         pass

#     def test_add_view_no_title(self):
#         pass


class TestPermalinkView(unittest.TestCase):
    """Test the permalink view (permalink_view function) of the microblog.
    """
    def setUp(self):
        microblog.db.create_all()
        microblog.add_user('admin', 'password')
        password, self.user_id = microblog.read_user('admin')
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


if __name__ == '__main__':
    unittest.main()
