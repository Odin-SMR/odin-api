import unittest
import requests


class TestSwagger(unittest.TestCase):

    def test_spec(self):
        """Check that spec is generated without errors"""
        r = requests.get('http://localhost:5000/rest_api/v4/spec')
        self.assertEqual(r.status_code, 200)
        spec = r.json()
        self.assertTrue('paths' in spec)

    def test_gui(self):
        """Check that swagger ui renders without errors"""
        # TODO: Must run javascript to test this thoroughly.
        r = requests.get('http://localhost:5000/apidocs/index.html')
        self.assertEqual(r.status_code, 200)