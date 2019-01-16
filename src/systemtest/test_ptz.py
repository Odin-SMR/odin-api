import pytest
import requests
from scripts.ptz_util import PrecalcPTZ
from datetime import datetime


@pytest.mark.slow
class TestPTZ:

    def test_erainterim_file_exists(self, odinapi_service):
        url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
        data = requests.get(url).json()
        assert (
            data['data']['ptz-files']['era-interim']['example-file']
            == '/var/lib/odindata/ECMWF/2015/01/ei_pl_2015-01-12-00.nc'
        )

    def test_solar_file_exists(self, odinapi_service):
        url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
        data = requests.get(url).json()
        assert (
            data['data']['ptz-files']['solardata']['example-file']
            == '/var/lib/odindata/Solardata2.db'
        )

    @pytest.mark.parametrize('url,key', (
        ('{}/rest_api/v4/ptz/2015-01-12/AC1/2/7014836770/', None),
        ('{}/rest_api/v5/level1/2/7014836770/ptz/', 'Data'),
    ))
    def test_can_return_ptz_data(self, odinapi_service, url, key):
        response = requests.get(url.format(odinapi_service))
        response.raise_for_status()
        data = response.json()
        if key:
            data = data[key]
        t0 = data['Temperature'][0]
        assert t0 == pytest.approx(275.781, abs=0.001)

    def test_ptz_batchcalc(self, odinapi_service):
        """Test that correct scans are selected to be processed"""
        date_start = datetime(2015, 1, 12)
        date_end = datetime(2015, 1, 13)
        fmode = 1
        scanid = 7014769645
        url = '{}/rest_api/v5'.format(odinapi_service)
        fptz = PrecalcPTZ(url, fmode, date_start, date_end)
        fptz.get_date_range()
        fptz.get_scandata4dateandfreqmode(date_start, fmode)
        assert fptz.date_range[0] == date_start
        assert fptz.date_range[-1] == date_end
        assert fptz.scanlist[0][3] == scanid


def test_latest_ecmf_file(odinapi_service):
    url = '{}/rest_api/v4/config_data/latest_ecmf_file/'.format(
        odinapi_service,
    )
    data = requests.get(url).json()
    assert data == {u'Date': u'2015-01-12', u'File': u'ei_pl_2015-01-12-18.nc'}
