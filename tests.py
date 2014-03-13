import unittest
import microblog


class TestWritePost(unittest.TestCase):
    """Test the write_post function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        self.title = "A Blog Title"
        self.body = "A Blog Body"

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_write_post(self):
        """Write a post and then verify that it appeared at the top of
        the microblog.
        """
        posts = microblog.read_posts()
        self.assertEqual(len(posts), 0)
        microblog.write_post(self.title, self.body)
        posts = microblog.read_posts()
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].title, self.title)
        self.assertEqual(posts[0].body, self.body)

    # def test_write_malformed_post(self):
    #     """Attempt to submit a post that does not have a title and verify
    #     that it did NOT appear at the top of the microblog.
    #     """
    #     try:
    #         microblog.write_post(None, self.malformed_body)
    #     except:
    #         #Discard any exceptions that were raised by this operation
    #         pass
    #     posts = microblog.read_posts()
    #     self.assertNotEqual(posts[0].body, self.malformed_body)


class TestReadPosts(unittest.TestCase):
    """Test the read_posts function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        self.title = "A Blog Title"
        self.body = "A Blog Body"

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_read_posts(self):
        """Read the number of posts we have. Then write a new post, and
        make sure that our newest post has been added and appears at the
        top of the returned list of posts.
        """
        posts = microblog.read_posts()
        length = len(posts)
        microblog.write_post(self.title, self.body)
        posts = microblog.read_posts()
        self.assertEqual(len(posts), length + 1)
        self.assertEqual(posts[0].title, self.title)
        self.assertEqual(posts[0].body, self.body)


class TestReadPost(unittest.TestCase):
    """Test the read_post function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        self.title1 = "A Blog Title"
        self.title2 = "Another Blog Title"
        self.title3 = "A Third Blog Title"
        self.body1 = "A Blog Body"
        self.body2 = "Another Blog Body"
        self.body3 = "A Third Blog Body"

        microblog.write_post(self.title1, self.body1)
        microblog.write_post(self.title2, self.body2)
        microblog.write_post(self.title3, self.body3)

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_read_post(self):
        """Add several posts and attempt to fetch one by its id."""
        post = microblog.read_post(2)
        self.assertEqual(post.title, self.title2)
        self.assertEqual(post.body, self.body2)

    def test_read_nonexistant_post(self):
        """Add several posts, then attempt to fetch a post by an id that
        shouldn't exist."""
        self.assertRaises(IndexError, microblog.read_post, 4)


class TestAddUser(unittest.TestCase):
    """Test the add_user function of the microblog."""
    def setUp(self):
        microblog.db.create_all()
        self.users = {
            'user1': 'pass1',
            'user2': 'pass2',
            'user3': 'pass3',
        }

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

    def test_add_user(self):
        """Add a user to the database and verify that that user has been
        inserted into the database.
        """
        pass


class TestReadUser(unittest.TestCase):
    """Test the read_user function of the microblog."""
    def setUp(self):
        microblog.db.create_all()

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


#Start testing views

if __name__ == '__main__':
    unittest.main()
