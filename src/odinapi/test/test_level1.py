import unittest

import pytest
import requests

from odinapi.test.testdefs import system, slow


@system
@pytest.mark.usefixtures('dockercompose')
class TestLevel1Views(unittest.TestCase):

    def test_backend_info(self):
        """Test raw backend info"""
        # Only V4
        base_url = (
            'http://localhost:5000/rest_api/{version}/freqmode_raw/{date}/'
            '{backend}/')
        r = requests.get(base_url.format(
            version='v4', date='2015-01-12', backend='AC2'))
        self.assertEqual(r.status_code, 200)

    def test_faulty_freqmode(self):
        """Test calling API with non-existent freqmode"""
        # class FreqmodeInfoNoBackend(BaseView):
        r = requests.get(
            'http://localhost:5000/rest_api/v5/freqmode_raw/2015-01-12/0/')
        self.assertEqual(r.status_code, 404)

        # class ScanSpecNoBackend(ScanSpec):
        r = requests.get(
            'http://localhost:5000/rest_api/v5/level1/0/7015092840/L1b/')
        self.assertEqual(r.status_code, 404)

        # class ScanPTZNoBackend(ScanPTZ):
        r = requests.get(
            'http://localhost:5000/rest_api/v5/level1/0/7015092840/ptz/')
        self.assertEqual(r.status_code, 404)

        # class ScanAPRNoBackend(ScanAPR):
        r = requests.get(
            'http://localhost:5000/rest_api/v5/level1/0/7015092840/apriori/O3')
        self.assertEqual(r.status_code, 404)

        # class CollocationsView(BaseView):
        r = requests.get(
            ('http://localhost:5000/rest_api/v5/level1/0/7015092840/'
             'collocations/'))
        self.assertEqual(r.status_code, 404)

    @slow
    def test_freqmode_raw_hierarchy(self):
        """Test freqmode raw hierarchy flow"""
        base_url = (
            'http://localhost:5000/rest_api/{version}/freqmode_raw/{date}/')

        # V4
        r = requests.get(base_url.format(version='v4', date='2015-01-12'))
        self.assertEqual(r.status_code, 200)
        nr_freqmodes_v4 = len(r.json()['Info'])
        next_level_url = r.json()['Info'][0]['URL']
        self.assertTrue('/v4/' in next_level_url)
        r = requests.get(next_level_url)
        self.assertEqual(r.status_code, 200)
        nr_scans_v4 = len(r.json()['Info'])

        # V5
        r = requests.get(base_url.format(version='v5', date='2015-01-12'))
        self.assertEqual(r.status_code, 200)
        nr_freqmodes_v5 = r.json()['Count']
        next_level_url = r.json()['Data'][0]['URL']
        self.assertTrue('/v5/' in next_level_url)
        r = requests.get(next_level_url)
        self.assertEqual(r.status_code, 200)
        nr_scans_v5 = r.json()['Count']

        self.assertEqual(nr_freqmodes_v4, nr_freqmodes_v5)
        self.assertEqual(nr_scans_v4, nr_scans_v5)

    def test_get_scan(self):
        """Test get scan data"""
        # V4
        base_url = (
            'http://localhost:5000/rest_api/{version}/scan/{backend}'
            '/{freqmode}/{scanid}')
        r = requests.get(base_url.format(
            version='v4', backend='AC2', freqmode=1, scanid=7015092840))
        self.assertEqual(r.status_code, 200)
        self.assertTrue('Altitude' in r.json())

        # V5
        base_url = (
            'http://localhost:5000/rest_api/{version}/level1/{freqmode}'
            '/{scanid}/L1b/')
        r = requests.get(base_url.format(
            version='v5', freqmode=1, scanid=7015092840))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'L1b')

    def test_get_scan_debug(self):
        """Test that get scan data debug option works"""
        # Only V5
        base_url = (
            'http://localhost:5000/rest_api/{version}/level1/{freqmode}'
            '/{scanid}/L1b/{debug}')
        r = requests.get(base_url.format(
            version='v5', freqmode=2, scanid=7014771917, debug="?debug=false"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'L1b')
        # First two subbands should be discarded in production mode:
        self.assertEqual(
            r.json()['Data']["Frequency"]["SubBandIndex"][0][0], -1)
        self.assertEqual(
            r.json()['Data']["Frequency"]["SubBandIndex"][0][1], -1)

        r = requests.get(base_url.format(
            version='v5', freqmode=2, scanid=7014771917, debug="?debug=true"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'L1b')
        # Only the first suband should be discarded in debug mode:
        self.assertEqual(
            r.json()['Data']["Frequency"]["SubBandIndex"][0][0], -1)
        self.assertEqual(
            r.json()['Data']["Frequency"]["SubBandIndex"][0][1], 1)

        r = requests.get(base_url.format(
            version='v5', freqmode=2, scanid=7014771917, debug="?debug=foo"))
        self.assertEqual(r.status_code, 400)

    def test_get_apriori(self):
        """Test get apriori data"""
        # V4
        base_url = (
            'http://localhost:5000/rest_api/{version}/apriori/O3/{date}/'
            '{backend}/{freqmode}/{scanid}/'
        )
        r = requests.get(base_url.format(
            version='v4', date='2015-01-12', backend='AC2', freqmode=1,
            scanid=7015092840))
        self.assertEqual(r.status_code, 200)
        self.assertTrue('Pressure' in r.json())

        # V5
        base_url = (
            'http://localhost:5000/rest_api/{version}/level1/{freqmode}'
            '/{scanid}/apriori/O3/')
        r = requests.get(base_url.format(
            version='v5', freqmode=1, scanid=7015092840))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'apriori')

    def test_get_collocations(self):
        """Test get collocations for a scan"""
        # V5
        base_url = (
            'http://localhost:5000/rest_api/{version}/level1/{freqmode}'
            '/{scanid}/collocations/')
        r = requests.get(base_url.format(
            version='v5', freqmode=1, scanid=1930998606))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'collocation')
        self.assertEqual(r.json()['Count'], 7)
