# pylint: disable=no-self-use,invalid-name
import httplib
import unittest
import urllib
import uuid

import requests
import pytest

from numpy.testing import assert_almost_equal
from numpy import isnan

from odinapi.utils import encrypt_util
from odinapi.test.level2_test_data import WRITE_URL, VERSION, get_test_data
from odinapi.test.testdefs import system


PROJECT_NAME = 'testproject'

PROJECTS_URL = 'http://localhost:5000/rest_api/{version}/level2/projects/'
PROJECT_URL = 'http://localhost:5000/rest_api/{version}/level2/{project}/'
COMMENTS_URL = (
    'http://localhost:5000/rest_api/{version}/level2/{project}/{freqmode}/'
    'comments')
SCANS_URL = (
    'http://localhost:5000/rest_api/{version}/level2/{project}/{freqmode}/'
    'scans')
FAILED_URL = (
    'http://localhost:5000/rest_api/{version}/level2/{project}/{freqmode}/'
    'failed')
PRODUCTS_URL = (
    'http://localhost:5000/rest_api/{version}/level2/{project}/products/')
PRODUCTS_FREQMODE_URL = (
    'http://localhost:5000/rest_api/{version}/level2/{project}/'
    '{freqmode}/products/')
SCAN_URL = ('http://localhost:5000/rest_api/{version}/level2/'
            '{project}/{freqmode}/{scanid}/')
AREA_URL = 'http://localhost:5000/rest_api/{version}/level2/{project}/area'
LOCATIONS_URL = (
    'http://localhost:5000/rest_api/{version}/level2/{project}/locations')
DATE_URL = 'http://localhost:5000/rest_api/{version}/level2/{project}/{date}'


def make_dev_url(url):
    return url.replace('/level2/', '/level2/development/')


PROJECTS_URL_DEV = make_dev_url(PROJECTS_URL)
PROJECT_URL_DEV = make_dev_url(PROJECT_URL)
COMMENTS_URL_DEV = make_dev_url(COMMENTS_URL)
SCANS_URL_DEV = make_dev_url(SCANS_URL)
FAILED_URL_DEV = make_dev_url(FAILED_URL)
PRODUCTS_URL_DEV = make_dev_url(PRODUCTS_URL)
PRODUCTS_FREQMODE_URL_DEV = make_dev_url(PRODUCTS_FREQMODE_URL)
SCAN_URL_DEV = make_dev_url(SCAN_URL)
AREA_URL_DEV = make_dev_url(AREA_URL)
LOCATIONS_URL_DEV = make_dev_url(LOCATIONS_URL)
DATE_URL_DEV = make_dev_url(DATE_URL)


@system
@pytest.mark.usefixtures('dockercompose')
class BaseWithDataInsert(unittest.TestCase):

    def setUp(self):
        # Insert level2 data
        self.scans_to_delete = []
        data = get_test_data()
        self.freq_mode = data['L2I']['FreqMode']
        self.scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(
            self.scan_id, self.freq_mode, PROJECT_NAME)
        wurl = WRITE_URL.format(version=VERSION, d=d)

        r = requests.post(wurl, json=data)
        self.assertEqual(r.status_code, 201)
        self.scans_to_delete.append(wurl)

        # Insert failed level2 scan
        self.failed_scan_id = self.scan_id + 1
        self.error_message = u'Error: This scan failed'
        data_failed = {'L2I': [], 'L2': [],
                       'L2C': data['L2C'] + '\n' + self.error_message}
        d = encrypt_util.encode_level2_target_parameter(
            self.failed_scan_id, self.freq_mode, PROJECT_NAME)
        wurl_failed = WRITE_URL.format(version=VERSION, d=d)

        r = requests.post(wurl_failed, json=data_failed)
        self.assertEqual(r.status_code, 201)
        self.scans_to_delete.append(wurl_failed)

    def tearDown(self):
        for url in self.scans_to_delete:
            requests.delete(url).raise_for_status()


@system
@pytest.mark.usefixtures('dockercompose')
class TestProjects(BaseWithDataInsert):

    def test_get_projects(self):
        """Test get list of projects"""
        # V4
        r = requests.get(PROJECTS_URL.format(version='v4'))
        self.assertEqual(r.status_code, 200)
        info = r.json()['Info']
        self.assertEqual(info['Projects'], [{
            'Name': PROJECT_NAME,
            'URLS': {
                'URL-project': PROJECT_URL.format(
                    version='v4', project=PROJECT_NAME)}}])

        # V5
        # No production projects added
        r = requests.get(PROJECTS_URL.format(version='v5'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['Data']), 0)

        r = requests.get(PROJECTS_URL_DEV.format(version='v5'))
        self.assertEqual(r.status_code, 200)
        data = r.json()['Data']
        self.assertEqual(data, [{
            'Name': PROJECT_NAME,
            'URLS': {
                'URL-project': PROJECT_URL_DEV.format(
                    version='v5', project=PROJECT_NAME)}}])

    def test_get_project(self):
        """Test get project info"""
        def test_version(version, get_data):
            url = PROJECT_URL if version <= 'v4' else PROJECT_URL_DEV
            r = requests.get(url.format(version=version, project=PROJECT_NAME))
            self.assertEqual(r.status_code, 200)
            info = get_data(r)
            scans_url = SCANS_URL if version <= 'v4' else SCANS_URL_DEV
            failed_url = FAILED_URL if version <= 'v4' else FAILED_URL_DEV
            comments_url = (
                COMMENTS_URL if version <= 'v4' else COMMENTS_URL_DEV)
            if version <= 'v4':
                self.assertEqual(info, {
                    'Name': PROJECT_NAME,
                    'FreqModes': [{
                        'FreqMode': 1,
                        'URLS': {
                            'URL-scans': scans_url.format(
                                version=version, freqmode=self.freq_mode,
                                project=PROJECT_NAME),
                            'URL-failed': failed_url.format(
                                version=version, freqmode=self.freq_mode,
                                project=PROJECT_NAME),
                            'URL-comments': comments_url.format(
                                version=version, freqmode=self.freq_mode,
                                project=PROJECT_NAME)
                        }
                    }]
                })
            else:
                self.assertEqual(info, [{
                    'FreqMode': 1,
                    'URLS': {
                        'URL-scans': scans_url.format(
                            version=version, freqmode=self.freq_mode,
                            project=PROJECT_NAME),
                        'URL-failed': failed_url.format(
                            version=version, freqmode=self.freq_mode,
                            project=PROJECT_NAME),
                        'URL-comments': comments_url.format(
                            version=version, freqmode=self.freq_mode,
                            project=PROJECT_NAME)
                    }
                }])

        def get_data_v4(resp):
            return resp.json()['Info']

        def get_data_v5(resp):
            return resp.json()['Data']

        test_version('v4', get_data_v4)
        test_version('v5', get_data_v5)


@system
@pytest.mark.usefixtures('dockercompose')
class TestWriteLevel2(unittest.TestCase):

    def test_post_and_delete(self):
        """Test post and delete of level2 data"""
        data = get_test_data()
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(
            scan_id, freq_mode, PROJECT_NAME)
        url = WRITE_URL.format(version=VERSION, d=d)

        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)

        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 201)

        # Post of duplicate should be possible
        # if someone wants to repost data we
        # think there is a good reason for this
        mjd = round(data['L2'][0]['MJD']) + 1
        data['L2'][0]['MJD'] = mjd
        data['L2'][1]['MJD'] = mjd
        data['L2'][2]['MJD'] = mjd
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 201)

        # Check that the post above actually
        # updated data
        rurl = SCAN_URL_DEV.format(
            version=VERSION,
            project=PROJECT_NAME,
            freqmode=freq_mode,
            scanid=scan_id)
        r = requests.get(rurl)
        self.assertEqual(
            r.json()['Data']['L2']['Data'][0]['MJD'], mjd)

        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)

        # When processing fails we only get comments
        data_failed = {'L2I': [], 'L2': [], 'L2C': data['L2C']}
        r = requests.post(url, json=data_failed)
        self.assertEqual(r.status_code, 201)

        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)

    def test_single_product(self):
        """Test post a single product"""
        data = get_test_data()
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        data['L2'] = data['L2'][0]
        d = encrypt_util.encode_level2_target_parameter(
            scan_id, freq_mode, PROJECT_NAME)
        url = WRITE_URL.format(version=VERSION, d=d)
        r = requests.post(url, json=data)
        self.assertEqual(r.status_code, 201)

    def test_bad_posts(self):
        """Test invalid posts of level2 data"""
        # No url parameter
        url = WRITE_URL.format(version=VERSION, d='')
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        # Wrong url parameter
        url = WRITE_URL.format(version=VERSION, d='bad')
        r = requests.post(url)
        self.assertEqual(r.status_code, 400)

        data = get_test_data()
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        d = encrypt_util.encode_level2_target_parameter(
            scan_id, freq_mode, PROJECT_NAME)
        url = WRITE_URL.format(version=VERSION, d=d)

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


@system
@pytest.mark.usefixtures('dockercompose')
class TestReadLevel2(BaseWithDataInsert):

    def test_get_comments_v4(self):
        """Test get list of comments"""
        # V4
        rurl = COMMENTS_URL.format(
            version='v4', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        comments = r.json()['Info']['Comments']
        assert len(comments) == 6

    def test_get_comments_v5(self):
        # V5
        rurl = COMMENTS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'level2_scan_comment')
        comments = r.json()['Data']
        assert len(comments) == 6

    def test_get_comments_v5_respects_limit(self):
        rurl = COMMENTS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl + '?limit=1')
        self.assertEqual(r.status_code, 200)
        comments = r.json()['Data']
        assert len(comments) == 1
        assert comments[0]['Comment'] == 'Error: This scan failed'

    def test_get_comments_v5_respects_offset(self):
        rurl = COMMENTS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl + '?offset=5')
        self.assertEqual(r.status_code, 200)
        comments = r.json()['Data']
        assert len(comments) == 1
        expected = 'Status: 9 spectra left after quality filtering'
        assert comments[0]['Comment'] == expected

    def test_get_comments_v5_empty_if_offset_gt_count(self):
        rurl = COMMENTS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl + '?offset=10')
        r.raise_for_status()
        comments = r.json()['Data']
        assert len(comments) == 0

    def test_get_comments_v5_has_link_header(self):
        url = COMMENTS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?offset=2&limit=2')
        assert r.links['prev']['url'] == url + '/?limit=2&offset=0'
        assert r.links['next']['url'] == url + '/?limit=2&offset=4'

    def test_get_scans(self):
        """Test get list of matching scans"""

        def test_version(version, get_scans):
            url = SCANS_URL if version <= 'v4' else SCANS_URL_DEV
            rurl = url.format(
                version=version, project=PROJECT_NAME, freqmode=self.freq_mode)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 200)
            scans = get_scans(r)
            self.assertEqual(len(scans), 1)
            scan = scans[0]
            self.assertEqual(scan['ScanID'], self.scan_id)
            if version <= 'v4':
                self.assertEqual(set(scan['URLS']), set([
                    'URL-level2', 'URL-log', 'URL-spectra']))
            else:
                self.assertEqual(set(scan['URLS']), set([
                    'URL-level2', 'URL-log', 'URL-spectra', 'URL-ancillary']))

            r = requests.get(rurl + '?start_time=2015-01-12')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(get_scans(r)), 1)

            r = requests.get(rurl + '?start_time=2015-01-13')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(get_scans(r)), 0)

            r = requests.get(rurl + '?end_time=2015-01-12')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(get_scans(r)), 0)

            r = requests.get(rurl + '?end_time=2015-01-13')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(get_scans(r)), 1)

            comment = u'Status: 9 spectra left after quality filtering'
            r = requests.get(
                rurl + '?' + urllib.urlencode([('comment', comment)]))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(get_scans(r)), 1)

            comment = u'Comment does not exist'
            r = requests.get(
                rurl + '?' + urllib.urlencode([('comment', comment)]))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(get_scans(r)), 0)

        def get_scans_v4(resp):
            return resp.json()['Info']['Scans']

        def get_scans_v5(resp):
            return resp.json()['Data']

        test_version('v4', get_scans_v4)
        test_version('v5', get_scans_v5)

    def test_get_scans_respects_limit(self):
        self.add_additional_scan(self.scan_id + 42)
        url = SCANS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?limit=1')
        r.raise_for_status()
        scans = r.json()['Data']
        assert len(scans) == 1
        assert scans[0]['ScanID'] == self.scan_id

    def test_get_scans_respects_offset(self):
        self.add_additional_scan(self.scan_id + 42)
        url = SCANS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?offset=1')
        r.raise_for_status()
        scans = r.json()['Data']
        assert len(scans) == 1
        assert scans[0]['ScanID'] == self.scan_id + 42

    def test_get_scans_empty_if_offset_gt_count(self):
        self.add_additional_scan(self.scan_id + 42)
        url = SCANS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?offset=10')
        r.raise_for_status()
        scans = r.json()['Data']
        assert len(scans) == 0

    def test_get_scans_has_link_header(self):
        self.add_additional_scan(self.scan_id + 42)
        self.add_additional_scan(self.scan_id + 43)
        url = SCANS_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?offset=1&limit=1')
        r.raise_for_status()
        assert r.links['prev']['url'] == url + '/?limit=1&offset=0'
        assert r.links['next']['url'] == url + '/?limit=1&offset=2'

    def add_additional_scan(self, scan_id):
        data = get_test_data()
        freq_mode = data['L2I']['FreqMode']
        data['L2I']['ScanID'] = scan_id
        d = encrypt_util.encode_level2_target_parameter(
            scan_id, freq_mode, PROJECT_NAME)
        wurl = WRITE_URL.format(version=VERSION, d=d)
        requests.post(wurl, json=data).raise_for_status()
        self.scans_to_delete.append(wurl)

    def test_get_failed_scans(self):
        """Test get list of failed scans"""
        # V4
        rurl = FAILED_URL.format(
            version='v4', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        scans = r.json()['Info']['Scans']
        self.assertEqual(len(scans), 1)
        scan = scans[0]
        self.assertEqual(scan['ScanID'], self.failed_scan_id)
        self.assertEqual(scan['Error'], self.error_message)
        self.assertEqual(set(scan['URLS']), set([
            'URL-level2', 'URL-log', 'URL-spectra']))

        # V5
        rurl = FAILED_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'level2_failed_scan_info')
        scans = r.json()['Data']
        self.assertEqual(len(scans), 1)
        scan = scans[0]
        self.assertEqual(scan['ScanID'], self.failed_scan_id)
        self.assertEqual(scan['Error'], self.error_message)
        self.assertEqual(set(scan['URLS']), set([
            'URL-level2', 'URL-log', 'URL-spectra', 'URL-ancillary']))

    def test_get_failed_scans_respects_limit(self):
        self.add_additional_failed_scan(self.failed_scan_id + 42)
        url = FAILED_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?limit=1')
        r.raise_for_status()
        scans = r.json()['Data']
        assert len(scans) == 1
        assert scans[0]['ScanID'] == self.failed_scan_id

    def test_get_failed_scans_respects_offset(self):
        self.add_additional_failed_scan(self.failed_scan_id + 42)
        url = FAILED_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?offset=1')
        r.raise_for_status()
        scans = r.json()['Data']
        assert len(scans) == 1
        assert scans[0]['ScanID'] == self.failed_scan_id + 42

    def test_get_failed_scans_empty_if_offset_gt_count(self):
        self.add_additional_failed_scan(self.failed_scan_id + 42)
        url = FAILED_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?offset=10')
        r.raise_for_status()
        scans = r.json()['Data']
        assert len(scans) == 0

    def test_get_failed_scans_has_link_header(self):
        self.add_additional_failed_scan(self.failed_scan_id + 42)
        self.add_additional_failed_scan(self.failed_scan_id + 43)
        url = FAILED_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(url + '?offset=1&limit=1')
        r.raise_for_status()
        assert r.links['prev']['url'] == url + '/?limit=1&offset=0'
        assert r.links['next']['url'] == url + '/?limit=1&offset=2'

    def add_additional_failed_scan(self, scan_id):
        self.error_message = u'Error: This scan failed'
        data = get_test_data()
        data_failed = {'L2I': [], 'L2': [],
                       'L2C': data['L2C'] + '\n' + self.error_message}
        d = encrypt_util.encode_level2_target_parameter(
            scan_id, self.freq_mode, PROJECT_NAME)
        wurl_failed = WRITE_URL.format(version=VERSION, d=d)
        requests.post(wurl_failed, json=data_failed).raise_for_status()
        self.scans_to_delete.append(wurl_failed)

    def test_get_scan(self):
        """Test get level2 data for a scan"""
        rurl = SCAN_URL.format(
            version='v4', project=PROJECT_NAME, freqmode=self.freq_mode,
            scanid=self.scan_id)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        info = r.json()['Info']
        self.assertTrue('L2i' in info)
        self.assertTrue('L2' in info)
        self.assertTrue('L2c' in info)
        self.assertTrue('URLS' in info)

        test_data = get_test_data()
        # Should return the data on the same format as from the qsmr processing
        self.assertEqual(len(info['L2']), len(test_data['L2']))
        expected = {}
        for p in test_data['L2']:
            expected[p['Product']] = p
        from_api = {}
        for p in info['L2']:
            from_api[p['Product']] = p
        self.assertEqual(set(from_api.keys()), set(expected.keys()))
        for p in from_api:
            api = from_api[p]
            expect = expected[p]
            for k, v in api.items():
                print k
                if isinstance(v, (list, float)):
                    assert_almost_equal(v, expect[k])
                elif isinstance(expect[k], float) and isnan(expect[k]):
                    self.assertEqual(v, None)
                else:
                    self.assertEqual(v, expect[k])

        # Test none existing
        rurl = SCAN_URL.format(
            version='v4', project=PROJECT_NAME, freqmode=2,
            scanid=self.scan_id)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 404)
        rurl = SCAN_URL.format(
            version='v4', project=PROJECT_NAME, freqmode=0,
            scanid=self.scan_id)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 404)

    def test_get_scan_v5(self):
        """Test v5 get level2 data for a scan"""
        rurl = SCAN_URL_DEV.format(
            version='v5', project=PROJECT_NAME, freqmode=self.freq_mode,
            scanid=self.scan_id)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        mixed = r.json()
        self.assertEqual(mixed['Type'], 'mixed')
        info = mixed['Data']
        self.assertTrue('L2i' in info)
        self.assertTrue('L2' in info)
        self.assertTrue('L2c' in info)

        test_data = get_test_data()
        # Should return the data on the same format as from the qsmr processing
        self.assertEqual(info['L2']['Count'], len(test_data['L2']))
        expected = {}
        for p in test_data['L2']:
            expected[p['Product']] = p
        from_api = {}
        for p in info['L2']['Data']:
            from_api[p['Product']] = p
        self.assertEqual(set(from_api.keys()), set(expected.keys()))
        for p in from_api:
            api = from_api[p]
            expect = expected[p]
            for k, v in api.items():
                print k
                if isinstance(v, (list, float)):
                    assert_almost_equal(v, expect[k])
                elif isinstance(expect[k], float) and isnan(expect[k]):
                    self.assertEqual(v, None)
                else:
                    self.assertEqual(v, expect[k])

        l2i_url = rurl + 'L2i/'
        r = requests.get(l2i_url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Data'], info['L2i']['Data'])

        l2c_url = rurl + 'L2c/'
        r = requests.get(l2c_url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Data'], info['L2c']['Data'])

        l2_url = rurl + 'L2/'
        r = requests.get(l2_url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Data'], info['L2']['Data'])

        l2_product_url = l2_url + '?product=O3 / 501 GHz / 20 to 50 km'
        r = requests.get(l2_product_url)
        l2_data = r.json()['Data']
        self.assertEqual(r.status_code, 200)
        for prod in info['L2']['Data']:
            if prod['Product'] == 'O3 / 501 GHz / 20 to 50 km':
                for k, v in l2_data[0].items():
                    print k
                    if isinstance(v, (list, float)):
                        assert_almost_equal(v, prod[k])
                    else:
                        self.assertEqual(v, prod[k])

    def test_get_products(self):
        """Test get products"""
        # V4
        rurl = PRODUCTS_URL.format(version='v4', project=PROJECT_NAME)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        res = r.json()['Info']['Products']
        self.assertEqual(len(res), 3)

        # V5
        rurl = PRODUCTS_URL_DEV.format(version='v5', project=PROJECT_NAME)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        res = r.json()['Data']
        self.assertEqual(len(res), 3)

    def test_get_products_for_freqmode(self):
        """Test get products for a freqmode"""
        # V4
        rurl = PRODUCTS_FREQMODE_URL_DEV.format(
            version='v4', freqmode=1, project=PROJECT_NAME)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        res = r.json()['Info']['Products']
        self.assertEqual(len(res), 3)

        # V5
        rurl = PRODUCTS_FREQMODE_URL_DEV.format(
            version='v5', freqmode=1, project=PROJECT_NAME)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        res = r.json()['Data']
        self.assertEqual(len(res), 3)

    def test_get_products_for_missing_freqmode(self):
        """Test get products for a missing freqmode"""
        # V4
        rurl = PRODUCTS_FREQMODE_URL_DEV.format(
            version='v4', freqmode=2, project=PROJECT_NAME)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        res = r.json()['Info']['Products']
        self.assertEqual(len(res), 0)

        # V5
        rurl = PRODUCTS_FREQMODE_URL_DEV.format(
            version='v5', freqmode=2, project=PROJECT_NAME)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        res = r.json()['Data']
        self.assertEqual(len(res), 0)

    def test_get_locations(self):
        """Test level2 get locations endpoint"""
        def test_results_v4(locations, radius, nr_expected, **param):
            rurl = LOCATIONS_URL.format(version='v4', project=PROJECT_NAME)
            uparam = [('location', loc) for loc in locations]
            uparam += [('radius', radius)]
            if param:
                uparam += [(k, str(v)) for k, v in param.items()]
            rurl += '?%s' % urllib.urlencode(uparam)
            r = requests.get(rurl)
            if r.status_code != 200:
                print r.json()
            self.assertEqual(r.status_code, 200)
            res = r.json()['Info']['Results']
            self.assertEqual(len(res), nr_expected)

        def test_results_v5(locations, radius, nr_expected, **param):
            rurl = LOCATIONS_URL_DEV.format(version='v5', project=PROJECT_NAME)
            uparam = [('location', loc) for loc in locations]
            uparam += [('radius', radius)]
            nr_expected_L2 = 3  # Nr products in the test scan
            if not nr_expected:
                nr_expected_L2 = 0
            if param:
                if 'product' in param:
                    nr_expected_L2 = 1
                uparam += [(k, str(v)) for k, v in param.items()]
            rurl += '?%s' % urllib.urlencode(uparam)
            r = requests.get(rurl)
            if r.status_code != 200:
                print r.json()
            self.assertEqual(r.status_code, 200)
            res = r.json()['Data']
            # Results are grouped by scan and product
            self.assertEqual(len(res), nr_expected_L2)
            inversions = sum([L2['VMR'] for L2 in res], [])
            self.assertEqual(len(inversions), nr_expected)

        def test_results(locations, radius, nr_expected, **param):
            test_results_v4(locations, radius, nr_expected, **param)
            test_results_v5(locations, radius, nr_expected, **param)

        test_results(['-6.0,95.0'], 30, 5, min_pressure=1,
                     start_time='2015-01-01')

        # Increase radius
        test_results(['-6.0,95.0'], 30, 2,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     min_pressure=1, start_time='2015-01-01')
        test_results(['-6.0,95.0'], 100, 7,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     min_pressure=1, start_time='2015-01-01')
        test_results(['-6.0,95.0'], 100, 3, max_altitude=55000,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     start_time='2015-01-01')
        test_results(['-6.0,95.0'], 1000, 25,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     min_pressure=1, start_time='2015-01-01')

        # Two locations
        test_results(['-6.0,95.0', '-10,94.3'], 30, 4,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     min_pressure=1, start_time='2015-01-01')

    def test_get_date(self):
        """Test level2 get date endpoint"""
        def test_results_v4(date, nr_expected, **param):
            rurl = DATE_URL.format(
                version='v4', project=PROJECT_NAME, date=date)
            if param:
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 200)
            res = r.json()['Info']['Results']
            self.assertEqual(len(res), nr_expected)

        def test_results_v5(date, nr_expected, **param):
            rurl = DATE_URL_DEV.format(
                version='v5', project=PROJECT_NAME, date=date)
            nr_expected_L2 = 3  # Nr products in the test scan
            if not nr_expected:
                nr_expected_L2 = 0
            if param:
                if 'product' in param:
                    nr_expected_L2 = 1
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 200)
            res = r.json()['Data']
            # Results are grouped by scan and product
            self.assertEqual(len(res), nr_expected_L2)
            inversions = sum([L2['VMR'] for L2 in res], [])
            self.assertEqual(len(inversions), nr_expected)

        def test_results(date, nr_expected, **param):
            test_results_v4(date, nr_expected, **param)
            test_results_v5(date, nr_expected, **param)

        test_results('2016-10-06', 0, min_pressure=1)
        test_results('2015-04-01', 61, min_pressure=1)

        # Pressure
        test_results('2015-04-01', 1, min_pressure=1000, max_pressure=1000,
                     product=u'O3 / 501 GHz / 20 to 50 km')
        test_results('2015-04-01', 11, min_pressure=1000,
                     product=u'O3 / 501 GHz / 20 to 50 km')
        test_results('2015-04-01', 15, max_pressure=1000,
                     product=u'O3 / 501 GHz / 20 to 50 km')
        # Altitude
        test_results('2015-04-01', 6, min_altitude=20000, max_altitude=30000,
                     product=u'O3 / 501 GHz / 20 to 50 km')
        test_results('2015-04-01', 21, min_altitude=20000,
                     product=u'O3 / 501 GHz / 20 to 50 km')
        test_results('2015-04-01', 4, max_altitude=20000,
                     product=u'O3 / 501 GHz / 20 to 50 km')

        # All products
        test_results('2015-04-01', 15, min_altitude=20000, max_altitude=30000)

    def test_get_area(self):
        """Test level2 get area endpoint"""
        def test_results_v4(nr_expected, **param):
            rurl = AREA_URL.format(version='v4', project=PROJECT_NAME)
            if param:
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 200)
            res = r.json()['Info']['Results']
            self.assertEqual(len(res), nr_expected)

        def test_results_v5(nr_expected, **param):
            rurl = AREA_URL_DEV.format(version='v5', project=PROJECT_NAME)
            nr_expected_L2 = 3  # Nr products in the test scan
            if not nr_expected:
                nr_expected_L2 = 0
            if param:
                if 'product' in param:
                    nr_expected_L2 = 1
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 200)
            res = r.json()['Data']
            # Results are grouped by scan and product
            self.assertEqual(len(res), nr_expected_L2)
            inversions = sum([L2['VMR'] for L2 in res], [])
            self.assertEqual(len(inversions), nr_expected)

        def test_results(nr_expected, **param):
            test_results_v4(nr_expected, **param)
            test_results_v5(nr_expected, **param)

        # Start and end time
        test_results(61, start_time='2015-03-02', min_pressure=1)
        test_results(0, start_time='2015-04-02', min_pressure=1)
        test_results(61, end_time='2015-04-02', min_pressure=1)
        test_results(0, end_time='2015-03-02', min_pressure=1)

        # Area
        test_results(6, min_lat=-7, min_lon=95,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     min_pressure=1, start_time='2015-01-01')
        test_results(17, max_lat=-7, max_lon=95,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     min_pressure=1, start_time='2015-01-01')
        test_results(2, min_lat=-7, max_lat=-6, min_lon=95, max_lon=95.1,
                     product=u'O3 / 501 GHz / 20 to 50 km',
                     min_pressure=1, start_time='2015-01-01')

    def test_bad_requests(self):
        """Test level2 bad get requests"""
        def test_bad(rurl, **param):
            if param:
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 400)

        def test_not_found(rurl, **param):
            if param:
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 404)

        AREA_URL = 'http://localhost:5000/rest_api/v5/level2/{project}/area'
        LOCATIONS_URL = (
            'http://localhost:5000/rest_api/v5/level2/{project}/locations')

        # No production projects added
        test_not_found(LOCATIONS_URL.format(project=PROJECT_NAME))
        test_not_found(AREA_URL.format(project=PROJECT_NAME))

        AREA_URL = (
            'http://localhost:5000/rest_api/v5/level2/development/{project}'
            '/area')
        LOCATIONS_URL = (
            'http://localhost:5000/rest_api/v5/level2/development/{project}'
            '/locations')

        # No locations
        test_bad(LOCATIONS_URL.format(project=PROJECT_NAME))

        # No radius
        test_bad(LOCATIONS_URL.format(project=PROJECT_NAME), location='-10,10')

        # Bad locations
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 radius=100, location='-91,100')
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 radius=100, location='91,100')
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 radius=100, location='-10,-1')
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 radius=100, location='-10,361')

        # Bad limits
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 min_pressure=1000, max_pressure=100)
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 min_altitude=50000, max_altitude=10000)
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 start_time='2015-01-01', end_time='2014-01-01')
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 min_lat=-5, max_lat=-10)
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 min_lon=100, max_lon=90)

        # Pressure and altitude not supported at the same time
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 min_pressure=1000, max_altitude=100000)

        # Too broad query
        test_bad(AREA_URL.format(project=PROJECT_NAME))
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 max_altitude=20000)
        test_bad(AREA_URL.format(project=PROJECT_NAME),
                 start_time='2015-01-01', end_time='2015-12-31')


@system
@pytest.mark.usefixtures('dockercompose')
class TestPublishProject(unittest.TestCase):

    def test_publish(self):
        project = self.create_project()
        self.assert_not_published(project)
        response = requests.post(
            self.development_url(project) + 'publish',
            auth=('bob', encrypt_util.SECRET_KEY),
        )
        assert response.status_code == httplib.CREATED
        assert response.headers['location'] == self.production_url(project)
        self.assert_published(project)

    def test_publish_unknown_project(self):
        response = requests.post(
            self.development_url('unknown-project') + 'publish',
            auth=('bob', encrypt_util.SECRET_KEY),
        )
        assert response.status_code == httplib.NOT_FOUND

    def test_no_credentials(self):
        project = self.create_project()
        self.assert_not_published(project)
        response = requests.post(self.development_url(project) + 'publish')
        assert response.status_code == httplib.UNAUTHORIZED
        self.assert_not_published(project)

    def test_bad_credentials(self):
        project = self.create_project()
        self.assert_not_published(project)
        response = requests.post(
            self.development_url(project) + 'publish',
            auth=('bob', 'password'),
        )
        assert response.status_code == httplib.UNAUTHORIZED
        self.assert_not_published(project)

    def create_project(self):
        data = get_test_data()
        project = str(uuid.uuid1())
        freq_mode = data['L2I']['FreqMode']
        scan_id = data['L2I']['ScanID']
        payload = encrypt_util.encode_level2_target_parameter(
            scan_id, freq_mode, project
        )
        wurl = WRITE_URL.format(version=VERSION, d=payload)
        requests.post(wurl, json=data).raise_for_status()
        return project

    def assert_not_published(self, project):
        assert requests.get(self.development_url(project)).ok
        assert not requests.get(self.production_url(project)).ok

    def assert_published(self, project):
        assert requests.get(self.production_url(project)).ok
        assert not requests.get(self.development_url(project)).ok

    def development_url(self, project):
        return PROJECT_URL_DEV.format(version='v5', project=project)

    def production_url(self, project):
        return PROJECT_URL.format(version='v5', project=project)
