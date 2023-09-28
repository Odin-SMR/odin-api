from http.client import OK
import unittest

from flask import Flask

from odinapi.run import app
from mock import patch
import numpy as np
import pytest

from odinapi.views import views



class TestAPR:
    APRIORI = {
        'vmr': np.array([1, 2, 3], dtype=float),
        'pressure': np.array([10, 11, 12], dtype=float),
        'altitude': np.array([100, 101, 102], dtype=float),
        'species': 'CO2',
    }

    @pytest.fixture
    def apriori_and_get_apriori(self):
        app = Flask(__name__)
        app.add_url_rule(
            '/rest_api/<version>/level1/<int:freqmode>/<int:scanno>/apriori/<species>/',  # noqa
            view_func=views.ScanAPRNoBackend.as_view('apriorinobackend'),
        )

        with patch(
            'odinapi.views.views.get_geoloc_info',
            return_value=('x', 15, 16, 'y'),
        ):
            with patch('odinapi.views.views.DatabaseConnector'):
                with patch('odinapi.views.views.get_scan_log_data'):
                    with patch(
                        'odinapi.views.views.get_apriori',
                        return_value=self.APRIORI,
                    ) as get_apriori:
                        yield app.test_client(), get_apriori

    def test_requesting_apriori_defaults_to_none_source(
        self, apriori_and_get_apriori,
    ):
        apriori, get_apriori = apriori_and_get_apriori
        resp = apriori.get('/rest_api/v5/level1/11/72/apriori/CO2/')
        assert resp.status_code == OK, resp.json
        get_apriori.assert_called_with('CO2', 15, 16, source=None)

    def test_requesting_apriori_source(
        self, apriori_and_get_apriori,
    ):
        apriori, get_apriori = apriori_and_get_apriori
        resp = apriori.get(
            '/rest_api/v5/level1/11/72/apriori/CO2/?aprsource=mipas',
        )
        assert resp.status_code == OK, resp.json
        get_apriori.assert_called_with('CO2', 15, 16, source='mipas')


class TestFileInfo(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    @patch('odinapi.views.data_info.db.session.execute')
    def test_get_file_info(self, mock_execute):
        # mocks result = db.session.execute('query')
        mock_result = mock_execute.return_value
        # mocks result.first()
        mock_result.first.return_value = None
        resp = self.client.get('/rest_api/v4/file_info/')
        assert resp.status_code == OK
        assert resp.json == {
            'ac1': None, 'ac2': None, 'att': None, 'fba': None, 'shk': None,
        }
