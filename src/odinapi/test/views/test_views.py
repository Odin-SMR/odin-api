from httplib import OK

from flask import Flask
from mock import patch, MagicMock
import numpy as np
import pytest

from odinapi.views.views import ScanAPRNoBackend


class TestAPR(object):
    APRIORI = {
        'vmr': np.array([1, 2, 3], dtype=float),
        'pressure': np.array([10, 11, 12], dtype=float),
        'altitude': np.array([100, 101, 102], dtype=float),
        'species': 'CO2',
    }

    @pytest.fixture
    def apriori(self):
        app = Flask(__name__)
        app.add_url_rule(
            '/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/'
            'apriori/<species>/',
            view_func=ScanAPRNoBackend.as_view('apriorinobackend'),
        )
        return app.test_client()

    @patch(
        'odinapi.views.views.get_geoloc_info', return_value=('x', 15, 16, 'y'),
    )
    @patch('odinapi.views.views.get_scan_log_data')
    @patch('odinapi.views.views.DatabaseConnector', return_value=MagicMock())
    @patch('odinapi.views.views.get_apriori', return_value=APRIORI)
    def test_requesting_apriori_defaults_to_none_source(
        self, get_apriori, dbconnector, get_scan_log_data, get_geoloc_info,
        apriori,
    ):
        resp = apriori.get('/rest_api/v5/level1/11/72/apriori/CO2/')
        assert resp.status_code == OK
        get_apriori.assert_called_with('CO2', 15, 16, source=None)

    @patch(
        'odinapi.views.views.get_geoloc_info', return_value=('x', 15, 16, 'y'),
    )
    @patch('odinapi.views.views.get_scan_log_data')
    @patch('odinapi.views.views.DatabaseConnector', return_value=MagicMock())
    @patch('odinapi.views.views.get_apriori', return_value=APRIORI)
    def test_requesting_apriori_source(
        self, get_apriori, dbconnector, get_scan_log_data, get_geoloc_info,
        apriori,
    ):
        resp = apriori.get(
            '/rest_api/v5/level1/11/72/apriori/CO2/?aprsource=mipas',
        )
        assert resp.status_code == OK
        get_apriori.assert_called_with('CO2', 15, 16, source='mipas')
