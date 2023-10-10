from http.client import OK
from flask.testing import FlaskClient
import pytest
import requests

pytestmark = pytest.mark.system


class TestSwaggerViews:
    def test_spec_v5(self, test_client: FlaskClient):
        r = test_client.get("/rest_api/v5/spec")
        r.status_code = OK
        assert r.json
        spec = r.json
        assert "paths" in spec
        assert len(spec["paths"]) > 0

    def test_gui(self, test_client: FlaskClient):
        r = test_client.get("/apidocs/index.html")
        assert r.status_code == OK
