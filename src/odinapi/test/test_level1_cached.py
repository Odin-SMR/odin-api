import unittest

import pytest
import requests

from odinapi.test.testdefs import system


@system
@pytest.mark.usefixtures('dockercompose')
class TestLevel1CachedViews(unittest.TestCase):

    def test_backend_info(self):
        """Test cached backend info"""
        # Only V4
        base_url = (
            'http://localhost:5000/rest_api/{version}/freqmode_info/{date}/'
            '{backend}/')
        r = requests.get(base_url.format(
            version='v4', date='2015-01-15', backend='AC2'))
        self.assertEqual(r.status_code, 200)

    def test_freqmode_info_hierarchy(self):
        """Test cached freqmode info hierarchy flow"""
        base_url = (
            'http://localhost:5000/rest_api/{version}/freqmode_info/{date}/')

        # V4
        r = requests.get(base_url.format(version='v4', date='2015-01-15'))
        self.assertEqual(r.status_code, 200)
        nr_freqmodes_v4 = len(r.json()['Info'])
        next_level_url = r.json()['Info'][0]['URL']
        self.assertTrue('/v4/' in next_level_url)
        r = requests.get(next_level_url)
        self.assertEqual(r.status_code, 200)
        nr_scans_v4 = len(r.json()['Info'])

        # V5
        r = requests.get(base_url.format(version='v5', date='2015-01-15'))
        self.assertEqual(r.status_code, 200)
        nr_freqmodes_v5 = r.json()['Count']
        next_level_url = r.json()['Data'][0]['URL']
        self.assertTrue('/v5/' in next_level_url)
        r = requests.get(next_level_url)
        self.assertEqual(r.status_code, 200)
        nr_scans_v5 = r.json()['Count']

        self.assertEqual(nr_freqmodes_v4, nr_freqmodes_v5)
        self.assertEqual(nr_scans_v4, nr_scans_v5)

    def test_scan_log(self):
        """Test get cached level1 log data for a scan"""
        # V4
        r = requests.get(
            'http://localhost:5000/rest_api/v4/l1_log/2/7019446353')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json()['Info']['URLS']['URL-ptz'],
            ('http://localhost:5000/rest_api/v4/ptz/'
             '2015-01-15/AC1/2/7019446353/')
        )

        # V5
        r = requests.get(
            'http://localhost:5000/rest_api/v5/level1/2/7019446353/Log')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['Type'], 'Log')
        self.assertEqual(
            r.json()['Data']['URLS']['URL-ptz'],
            'http://localhost:5000/rest_api/v5/level1/2/7019446353/ptz/'
        )

    def test_period_info(self):
        """Test get period info"""
        base_url = (
            'http://localhost:5000/rest_api/{version}/period_info/'
            '{year}/{month}/{day}')

        # V4
        r = requests.get(base_url.format(
            version='v4', year='2015', month='01', day='15'))
        self.assertEqual(r.status_code, 200)
        nr_freqmodes_v4 = len(r.json()['Info'])

        # V5
        r = requests.get(base_url.format(
            version='v5', year='2015', month='01', day='15'))
        self.assertEqual(r.status_code, 200)
        nr_freqmodes_v5 = r.json()['Count']
        self.assertEqual(r.json()['PeriodStart'], '2015-01-15')

        self.assertEqual(nr_freqmodes_v4, nr_freqmodes_v5)