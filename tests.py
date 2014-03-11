import unittest
import microblog


class TestWritePost(unittest.TestCase):
    """Test the write_post function of the microblog."""
    def setUp(self):
        posts = microblog.read_posts()
        self.title = "A Blog Title %s" % (int(posts[0].id) + 1)
        self.body = "A Blog Body"
        self.malformed_body = "The body section of a malformed post."

    def test_write_post(self):
        """Write a post and then verify that it appeared at the top of
        the microblog.
        """
        microblog.write_post(self.title, self.body)
        posts = microblog.read_posts()
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
        posts = microblog.read_posts()
        self.title = "A Blog Title %s" % (int(posts[0].id) + 1)
        self.body = "A Blog Body"

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


if __name__ == '__main__':
    unittest.main()
