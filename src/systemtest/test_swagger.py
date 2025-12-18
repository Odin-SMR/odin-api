from http.client import OK

import pytest
from flask.testing import FlaskClient

pytestmark = pytest.mark.system


class TestSwaggerViews:
    def test_spec_v5(self, test_client: FlaskClient):
        """Test that the Swagger spec endpoint returns valid OpenAPI 3.0 JSON"""
        r = test_client.get("/rest_api/v5/spec")
        assert r.status_code == OK
        assert r.json
        spec = r.json
        # Now using OpenAPI 3.0
        assert "openapi" in spec
        assert spec["openapi"].startswith("3.0")
        assert "info" in spec
        assert "paths" in spec
        # Verify we have documented paths
        assert len(spec["paths"]) > 0

    def test_gui(self, test_client: FlaskClient):
        """Test that the Swagger UI is accessible"""
        r = test_client.get("/apidocs/")
        assert r.status_code == OK
