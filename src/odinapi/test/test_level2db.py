# pylint: skip-file
import os
import json
import unittest
import urllib
import requests

from numpy.testing import assert_almost_equal
from numpy import isnan

from odinapi.utils import encrypt_util

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')
PROJECT_NAME = 'testproject'
PROJECTS_URL = 'http://localhost:5000/rest_api/v4/level2/projects/'
PROJECT_URL = 'http://localhost:5000/rest_api/v4/level2/{project}/'
COMMENTS_URL = (
    'http://localhost:5000/rest_api/v4/level2/{project}/{freqmode}/comments')
SCANS_URL = (
    'http://localhost:5000/rest_api/v4/level2/{project}/{freqmode}/scans')
WRITE_URL = 'http://localhost:5000/rest_api/v4/level2?d={}'
PRODUCTS_URL = 'http://localhost:5000/rest_api/v4/level2/{project}/products/'
SCAN_URL = ('http://localhost:5000/rest_api/v4/level2/'
            '{project}/{freqmode}/{scanid}/')
AREA_URL = 'http://localhost:5000/rest_api/v4/level2/{project}/area'
LOCATIONS_URL = 'http://localhost:5000/rest_api/v4/level2/{project}/locations'
DATE_URL = 'http://localhost:5000/rest_api/v4/level2/{project}/{date}'


def get_test_data():
    with open(os.path.join(TEST_DATA_DIR, 'odin_result.json')) as inp:
        return json.load(inp)


def get_write_url(data):
    freq_mode = data['L2I']['FreqMode']
    scan_id = data['L2I']['ScanID']
    d = encrypt_util.encode_level2_target_parameter(
        scan_id, freq_mode, PROJECT_NAME)
    return WRITE_URL.format(d)


def insert_test_data():
    data = get_test_data()
    wurl = get_write_url(data)
    r = requests.post(wurl, json=data)
    return r


def delete_test_data():
    data = get_test_data()
    wurl = get_write_url(data)
    r = requests.delete(wurl, json=data)
    return r


class BaseWithDataInsert(unittest.TestCase):

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


class TestProjects(BaseWithDataInsert):

    def test_get_projects(self):
        """Test get list of projects"""
        r = requests.get(PROJECTS_URL)
        self.assertEqual(r.status_code, 200)
        info = r.json()['Info']
        self.assertEqual(info['Projects'], [{
            'Name': PROJECT_NAME,
            'URLS': {
                'URL-project': PROJECT_URL.format(project=PROJECT_NAME)}}])

    def test_get_project(self):
        """Test get project info"""
        r = requests.get(PROJECT_URL.format(project=PROJECT_NAME))
        self.assertEqual(r.status_code, 200)
        info = r.json()['Info']
        self.assertEqual(info, {
            'Name': PROJECT_NAME,
            'FreqModes': [{
                'FreqMode': 1,
                'URLS': {
                    'URL-scans': SCANS_URL.format(
                        freqmode=self.freq_mode, project=PROJECT_NAME),
                    'URL-comments': COMMENTS_URL.format(
                        freqmode=self.freq_mode, project=PROJECT_NAME)
                }
            }]
        })


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


class TestReadLevel2(BaseWithDataInsert):

    def test_get_comments(self):
        """Test get list of comments"""
        rurl = COMMENTS_URL.format(
            project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        comments = r.json()['Info']['Comments']
        print comments
        self.assertEqual(len(comments), 5)

    def test_get_scans(self):
        """Test get list of matching scans"""
        rurl = SCANS_URL.format(project=PROJECT_NAME, freqmode=self.freq_mode)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        scans = r.json()['Info']['Scans']
        self.assertEqual(len(scans), 1)
        scan = scans[0]
        self.assertEqual(scan['ScanID'], self.scan_id)
        self.assertEqual(set(scan['URLS']), set([
            'URL-level2', 'URL-log', 'URL-spectra']))

        r = requests.get(rurl + '?start_time=2015-04-01')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['Info']['Scans']), 1)

        r = requests.get(rurl + '?start_time=2015-04-02')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['Info']['Scans']), 0)

        r = requests.get(rurl + '?end_time=2015-04-01')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['Info']['Scans']), 0)

        r = requests.get(rurl + '?end_time=2015-04-02')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['Info']['Scans']), 1)

        comment = u'Status: 9 spectra left after quality filtering'
        r = requests.get(rurl + '?' + urllib.urlencode([('comment', comment)]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['Info']['Scans']), 1)

        comment = u'Comment does not exist'
        r = requests.get(rurl + '?' + urllib.urlencode([('comment', comment)]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()['Info']['Scans']), 0)

    def test_get_scan(self):
        """Test get level2 data for a scan"""
        rurl = SCAN_URL.format(
            project=PROJECT_NAME, freqmode=self.freq_mode, scanid=self.scan_id)
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
            project=PROJECT_NAME, freqmode=2, scanid=self.scan_id)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 404)

    def test_get_products(self):
        """Test get products"""
        rurl = PRODUCTS_URL.format(project=PROJECT_NAME)
        r = requests.get(rurl)
        self.assertEqual(r.status_code, 200)
        res = r.json()['Info']['Products']
        self.assertEqual(len(res), 3)

    def test_get_locations(self):
        """Test level2 get locations endpoint"""
        def test_results(locations, radius, nr_expected, **param):
            rurl = LOCATIONS_URL.format(project=PROJECT_NAME)
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
        def test_results(date, nr_expected, **param):
            rurl = DATE_URL.format(project=PROJECT_NAME, date=date)
            if param:
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 200)
            res = r.json()['Info']['Results']
            self.assertEqual(len(res), nr_expected)

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
        def test_results(nr_expected, **param):
            rurl = AREA_URL.format(project=PROJECT_NAME)
            if param:
                rurl += '?%s' % urllib.urlencode(param)
            r = requests.get(rurl)
            self.assertEqual(r.status_code, 200)
            res = r.json()['Info']['Results']
            self.assertEqual(len(res), nr_expected)

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
