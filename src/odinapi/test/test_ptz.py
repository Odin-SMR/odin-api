# pylint: skip-file
import unittest
import pytest
import requests as R
import numpy as np
import os
from subprocess import check_output
from testdefs import system

URL_ROOT = 'http://localhost:5000/'
URL_DATA_FILES = (
    URL_ROOT + 'rest_api/v4/config_data/data_files/'
)
URL_PTZ = (
    URL_ROOT + 'rest_api/v4/ptz/'
)
ROOT_PATH = check_output(['git', 'rev-parse', '--show-toplevel']).strip()


@system
@pytest.mark.usefixtures('dockercompose')
class TestPTZ(unittest.TestCase):

    def test_erainterim_file_exists(self):
        """Check that file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['ptz-files']['era-interim']['example-file'] ==
            '/var/lib/odindata/ECMWF/2015/01/ei_pl_2015-01-12-00.nc'
        )

    def test_solar_file_exists(self):
        """Check that file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['ptz-files']['solardata']['example-file'] ==
            '/var/lib/odindata/Solardata2.db'
        )

    def test_ptz_file_can_be_created(self):
        """Check that odin-api can create ptz-file"""
        url_string = (
            URL_PTZ + '2015-01-12/AC1/2/7014836770/'
        )
        ptzfile = os.path.join(
            ROOT_PATH,
            'data/ptz-data/ZPT/2015/01/',
            'ZPT_7014836770.nc'
        )
        if os.path.isfile(ptzfile):
            os.remove(ptzfile)
        data = R.get(url_string).json()
        t0 = data['Temperature'][0]
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 275.781)

    def test_ptz_file_is_readable(self):
        """Check that odin-api can read ptz file"""
        url_string = (
            URL_PTZ + '2015-01-12/AC1/2/7014836770/'
        )
        ptzfile = '/var/lib/odindata/ZPT/2015/01/ZPT_7014836770.nc'
        data = data = R.get(url_string).json()
        t0 = data['Temperature'][0]
        t0 = np.around(t0, decimals=3).tolist()
        ptzfile = os.path.join(
            ROOT_PATH,
            'data/ptz-data/ZPT/2015/01/',
            'ZPT_7014836770.nc'
        )
        if os.path.isfile(ptzfile):
            os.remove(ptzfile)
        self.assertTrue(t0 == 275.781)
