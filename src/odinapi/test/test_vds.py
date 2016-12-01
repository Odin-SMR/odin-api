# pylint: skip-file
import unittest
import pytest
import requests as R
import json
import numpy as np


@pytest.mark.usefixtures('dockercompose')
class TestVds(unittest.TestCase):

    def test_vds_file4ace_exists(self):
        """Check that ace file exists"""
        url_base = 'http://localhost:5000/rest_api/v4/'
        url_string = url_base + 'config_data/data_files/'
        data = json.loads(R.get(url_string).text)
        test = (data['ace-data']['example-file'] ==
                'vds-data/ACE_Level2/v2/2004-03/ss2969.nc')
        self.assertTrue(test)

    def test_vds_file4ace_is_readable(self):
        """Check that odin-api can read ace-file"""
        url_base = 'http://localhost:5000/rest_api/v4/'
        url_string = url_base + 'vds_external/ace/T/2004-03-01/ss2969.nc/0/'
        data = json.loads(R.get(url_string).text)
        t0 = data['Data-L2_retreival_grid']['T'][0]
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 214.420)
