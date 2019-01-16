import requests
import pytest


class TestApriori:
    def test_ozone_apriori_file_exists(self, odinapi_service):
        """Check that file exists"""
        url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
        data = requests.get(url).json()
        assert (
            data['data']['apriori-files']['ozone']['example-file']
            == '/var/lib/odindata/apriori/apriori_O3.mat'
        )

    def test_ozone_apriori_file_is_readable(self, odinapi_service):
        """Check that odin-api can read apriori file"""
        url = '{}/rest_api/v4/apriori/O3/2015-01-12/AC1/2/7014836770/'.format(
            odinapi_service,
        )
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        t0 = data['VMR'][0] * 1e8
        assert t0 == pytest.approx(1.621, abs=0.001)
