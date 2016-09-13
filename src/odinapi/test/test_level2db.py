import os
import json
import unittest
import requests

from odinapi.utils import encrypt_util

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')


class TestLevel2db(unittest.TestCase):

    def setUp(self):
        self.base_url = 'http://localhost:5000/rest_api/v4/level2?d={}'

    def _get_test_data(self):
        with open(os.path.join(TEST_DATA_DIR, 'odin_result.json')) as inp:
            return json.load(inp)

    def test_post_and_delete(self):
        """Test post and delete of level2 data"""
        data = self._get_test_data()
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(scan_id, freq_mode)
        url = self.base_url.format(d)

        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)

        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 201)

        # Post of duplicate should not be possible
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)

        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 201)

    def test_bad_posts(self):
        """Test invalid posts of level2 data"""
        # No url parameter
        url = self.base_url.format('')
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        # Wrong url parameter
        url = self.base_url.format('bad')
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        data = self._get_test_data()
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(scan_id, freq_mode)
        url = self.base_url.format(d)

        # Missing data
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        data = self._get_test_data()
        data.pop('L2')
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        data = self._get_test_data()
        data['L2I'].pop('ScanID')
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        data = self._get_test_data()
        data['L2'][0].pop('ScanID')
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        # Freq mode missmatch
        data = self._get_test_data()
        data['L2I']['FreqMode'] = 2
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        # Scan id missmatch
        data = self._get_test_data()
        data['L2I']['ScanID'] = 2
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)
