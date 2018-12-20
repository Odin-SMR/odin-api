import unittest

import pytest
import requests

from .testdefs import slow, system


@system
@pytest.mark.usefixtures('dockercompose')
class TestSwaggerViews(unittest.TestCase):

    @slow
    def test_spec_v5(self):
        """Check that v5 spec is generated without errors"""
        r = requests.get('http://localhost:5000/rest_api/v5/spec')
        self.assertEqual(r.status_code, 200)
        spec = r.json()
        self.assertTrue('paths' in spec)
        self.assertGreater(len(spec['paths']), 0)

    def test_gui(self):
        """Check that swagger ui renders without errors"""
        # TODO: Must run javascript to test this thoroughly.
        r = requests.get('http://localhost:5000/apidocs/index.html')
        self.assertEqual(r.status_code, 200)
