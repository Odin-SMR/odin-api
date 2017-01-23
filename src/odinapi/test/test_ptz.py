# pylint: skip-file
import unittest
import pytest
import requests as R
import numpy as np
import os
from subprocess import check_output
from testdefs import system, slow
from scripts.ptz_util import PrecalcPTZ
from datetime import datetime

URL_ROOT = 'http://localhost:5000/'
URL_DATA_FILES = (
    URL_ROOT + 'rest_api/v4/config_data/data_files/'
)
URL_LATEST_ECMF_FILE = URL_ROOT + 'rest_api/v4/config_data/latest_ecmf_file/'
URL_PTZ = (
    URL_ROOT + 'rest_api/v4/ptz/'
)
URL_PTZ_V5 = (
    URL_ROOT + 'rest_api/v5/level1/{freqmode}/{scanid}/ptz/'
)
ROOT_PATH = check_output(['git', 'rev-parse', '--show-toplevel']).strip()
URL_BATCHCALC = (
   URL_ROOT + 'rest_api/v5'
)


@system
@slow
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

        def test_version(url_string, key=None):
            ptzfile = os.path.join(
                ROOT_PATH,
                'data/ptz-data/ZPT/2015/01/',
                'ZPT_7014836770.nc'
            )
            if os.path.isfile(ptzfile):
                os.remove(ptzfile)
            data = R.get(url_string).json()
            if key:
                data = data[key]
            t0 = data['Temperature'][0]
            t0 = np.around(t0, decimals=3).tolist()
            self.assertTrue(t0 == 275.781)

        url_string = (
            URL_PTZ + '2015-01-12/AC1/2/7014836770/'
        )
        test_version(url_string)
        url_string = (
            URL_PTZ_V5.format(freqmode='2', scanid='7014836770')
        )
        test_version(url_string, key='Data')

    def test_ptz_file_is_readable(self):
        """Check that odin-api can read ptz file"""

        def test_version(url_string, key=None):
            ptzfile = '/var/lib/odindata/ZPT/2015/01/ZPT_7014836770.nc'
            data = R.get(url_string).json()
            if key:
                data = data[key]
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

        url_string = (
            URL_PTZ + '2015-01-12/AC1/2/7014836770/'
        )
        test_version(url_string)
        url_string = (
            URL_PTZ_V5.format(freqmode='2', scanid='7014836770')
        )
        test_version(url_string, key='Data')

    def test_ptz_batchcalc(self):
        """Test that correct scans are selected to be processed"""
        date_start = datetime(2015, 1, 12)
        date_end = datetime(2015, 1, 13)
        fmode = 1
        scanid = 7014769645
        fptz = PrecalcPTZ(URL_BATCHCALC, fmode, date_start, date_end)
        fptz.get_date_range()
        fptz.get_scandata4dateandfreqmode(date_start, fmode)
        test1 = fptz.date_range[0] == date_start
        test2 = fptz.date_range[-1] == date_end
        test3 = fptz.scanlist[0][3] == scanid
        self.assertTrue(test1 and test2 and test3)


@system
@pytest.mark.usefixtures('dockercompose')
def test_latest_ecmf_file():
    """Test GET latest ecmf file"""
    data = R.get(URL_LATEST_ECMF_FILE).json()
    assert data == {u'Date': u'2015-01-12', u'File': u'ei_pl_2015-01-12-18.nc'}
