import os
import json
import unittest
import requests

from odinapi.utils import encrypt_util

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')
PROJECT_NAME = 'testproject'
WRITE_URL = 'http://localhost:5000/rest_api/v4/level2?d={}'
GET_URL = 'http://localhost:5000/rest_api/v4/level2/{}/{}/{}/'


def get_test_data():
    with open(os.path.join(TEST_DATA_DIR, 'odin_result.json')) as inp:
        return json.load(inp)


class TestWriteLevel2(unittest.TestCase):

    def test_post_and_delete(self):
        """Test post and delete of level2 data"""
        data = get_test_data()
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(
            scan_id, freq_mode, PROJECT_NAME)
        url = WRITE_URL.format(d)

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

        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)

    def test_bad_posts(self):
        """Test invalid posts of level2 data"""
        # No url parameter
        url = WRITE_URL.format('')
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        # Wrong url parameter
        url = WRITE_URL.format('bad')
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        data = get_test_data()
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(
            scan_id, freq_mode, PROJECT_NAME)
        url = WRITE_URL.format(d)

        # Missing data
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        data = get_test_data()
        data.pop('L2')
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        data = get_test_data()
        data['L2I'].pop('ScanID')
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        data = get_test_data()
        data['L2'][0].pop('ScanID')
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        # Freq mode missmatch
        data = get_test_data()
        data['L2I']['FreqMode'] = 2
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)

        # Scan id missmatch
        data = get_test_data()
        data['L2I']['ScanID'] = 2
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 400)


class TestReadLevel2(unittest.TestCase):
    def setUp(self):
        # Insert level2 data
        data = get_test_data()
        self.freq_mode = data['L2I']['FreqMode']
        self.scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(
            self.scan_id, self.freq_mode, PROJECT_NAME)
        self.wurl = WRITE_URL.format(d)

        r = requests.post(self.wurl, json=data)
        self.assertEqual(r.status_code, 201)

    def tearDown(self):
        # Delete level2 data
        r = requests.delete(self.wurl)
        self.assertEqual(r.status_code, 204)

    def test_get(self):
        """Test get level2 data"""
        rurl = GET_URL.format(PROJECT_NAME, self.freq_mode, self.scan_id)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        info = r.json()['Info']
        print info.keys()
        self.assertTrue('L2i' in info)

        # Test none existing
        rurl = GET_URL.format(PROJECT_NAME, 2, self.scan_id)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 404)
