import unittest
import pytest
import requests
import numpy as np
from subprocess import check_output
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


@pytest.fixture(scope='session', autouse=True)
def zpt_data_directory():
    """
    Create dirs that are used in the tests. This ensure that they are owned by
    us so that we can clean them at the end. Otherwise, they'll be created by
    root inside the docker image.
    path = os.path.join(ROOT_PATH, 'data/ptz-data/ZPT/2015/01/')
    os.makedirs(path)
    yield path
    shutil.rmtree(path)
    """


@pytest.mark.slow
@pytest.mark.usefixtures('dockercompose')
class TestPTZ(unittest.TestCase):

    def test_erainterim_file_exists(self):
        """Check that file exists"""
        data = requests.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['ptz-files']['era-interim']['example-file'] ==
            '/var/lib/odindata/ECMWF/2015/01/ei_pl_2015-01-12-00.nc'
        )

    def test_solar_file_exists(self):
        """Check that file exists"""
        data = requests.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['ptz-files']['solardata']['example-file'] ==
            '/var/lib/odindata/Solardata2.db'
        )

    def test_can_return_ptz_data(self):
        """Check that odin-api can create ptz-file"""

        def test_version(url_string, key=None):
            response = requests.get(url_string)
            data = response.json()
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


@pytest.mark.usefixtures('dockercompose')
def test_latest_ecmf_file():
    """Test GET latest ecmf file"""
    data = requests.get(URL_LATEST_ECMF_FILE).json()
    assert data == {u'Date': u'2015-01-12', u'File': u'ei_pl_2015-01-12-18.nc'}
