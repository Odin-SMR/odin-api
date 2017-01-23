# pylint: skip-file
import unittest

import pytest
import requests as R
import numpy as np

from odinapi.test.testdefs import system


URL_ROOT = 'http://localhost:5000/'
URL_DATA_FILES = (
    URL_ROOT + 'rest_api/v4/config_data/data_files/'
)
URL_APRIORI = (
    URL_ROOT + 'rest_api/v4/apriori/'
)


@system
@pytest.mark.usefixtures('dockercompose')
class TestApriori(unittest.TestCase):

    def test_ozone_apriori_file_exists(self):
        """Check that file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['apriori-files']['ozone']['example-file'] ==
            '/var/lib/odindata/apriori/apriori_O3.mat'
        )

    def test_ozone_apriori_file_is_readable(self):
        """Check that odin-api can read apriori file"""
        url_string = (
            URL_APRIORI + 'O3/2015-01-12/AC1/2/7014836770/'
        )
        data = R.get(url_string).json()
        t0 = data['VMR'][0] * 1e8
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 1.621)
