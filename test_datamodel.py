import os
from datamodel import app
import unittest
import tempfile

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_empty_db(self):
        rv = self.app.get('/')
        self.assertEqual(b'Hello, World!', rv.data)

if __name__ == '__main__':
    unittest.main()
