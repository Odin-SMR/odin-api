from http.client import OK
import unittest

from odinapi.run import app
from mock import patch
import numpy as np


class TestAPR:
    APRIORI = {
        "vmr": np.array([1, 2, 3], dtype=float),
        "pressure": np.array([10, 11, 12], dtype=float),
        "altitude": np.array([100, 101, 102], dtype=float),
        "species": "CO2",
    }

    @patch("odinapi.views.views.get_geoloc_info")
    @patch("odinapi.views.views.get_apriori")
    @patch("odinapi.views.views.get_scan_log_data")
    def test_requesting_apriori_defaults_to_none_source(
        self, get_scan_log_data, get_apriori, get_geoloc_info, db_app
    ):
        apriori = db_app.test_client()
        get_apriori.return_value = self.APRIORI
        get_geoloc_info.return_value = ("x", 15, 16, "y")
        resp = apriori.get("/rest_api/v5/level1/11/72/apriori/CO2/")
        assert resp.status_code == OK, resp.json
        get_apriori.assert_called_with("CO2", 15, 16, source=None)

    @patch("odinapi.views.views.get_geoloc_info")
    @patch("odinapi.views.views.get_apriori")
    @patch("odinapi.views.views.get_scan_log_data")
    def test_requesting_apriori_source(
        self, get_scan_log_data, get_apriori, get_geoloc_info, db_app
    ):
        apriori = db_app.test_client()
        get_apriori.return_value = self.APRIORI
        get_geoloc_info.return_value = ("x", 15, 16, "y")
        resp = apriori.get(
            "/rest_api/v5/level1/11/72/apriori/CO2/?aprsource=mipas",
        )
        assert resp.status_code == OK, resp.json
        get_apriori.assert_called_with("CO2", 15, 16, source="mipas")


class TestFileInfo(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("odinapi.views.data_info.db.session.execute")
    def test_get_file_info(self, mock_execute):
        # mocks result = db.session.execute('query')
        mock_result = mock_execute.return_value
        # mocks result.first()
        mock_result.first.return_value = None
        resp = self.client.get("/rest_api/v4/file_info/")
        assert resp.status_code == OK
        assert resp.json == {
            "ac1": None,
            "ac2": None,
            "att": None,
            "fba": None,
            "shk": None,
        }
