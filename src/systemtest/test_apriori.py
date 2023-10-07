from http.client import OK

import pytest
from flask.testing import FlaskClient


class TestApriori:
    def test_ozone_apriori_file_exists(self, test_client: FlaskClient):
        """Check that file exists"""
        url = "/rest_api/v4/config_data/data_files/"
        r = test_client.get(url)
        assert r.status_code == OK
        assert r.json
        assert (
            r.json["data"]["apriori-files"]["ozone"]["example-file"]
            == "s3://odin-apriori/apriori_O3.mat"
        )

    def test_ozone_apriori_file_is_readable(self, test_client: FlaskClient):
        """Check that odin-api can read apriori file"""
        url = "/rest_api/v4/apriori/O3/2015-01-12/AC1/2/7014836770/"
        r = test_client.get(url)
        assert r.status_code == OK
        assert r.json
        data = r.json
        t0 = data["VMR"][0] * 1e8
        assert t0 == pytest.approx(1.621, abs=0.001)
