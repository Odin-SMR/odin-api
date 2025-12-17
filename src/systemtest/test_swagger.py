from http.client import OK

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.system


class TestSwaggerViews:
    def test_spec_v5(self, test_client: FlaskClient):
        """Test that the Swagger spec endpoint returns valid JSON"""
        r = test_client.get("/rest_api/v5/spec")
        assert r.status_code == OK
        assert r.json
        spec = r.json
        assert "swagger" in spec or "openapi" in spec
        assert "info" in spec
        assert "paths" in spec

    def test_gui(self, test_client: FlaskClient):
        """Test that the Swagger UI is accessible"""
        r = test_client.get("/apidocs/")
        assert r.status_code == OK
