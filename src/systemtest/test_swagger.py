import pytest
import requests


class TestSwaggerViews:
    @pytest.mark.slow
    def test_spec_v5(self, selenium_app):
        r = requests.get("{}/rest_api/v5/spec".format(selenium_app))
        r.raise_for_status()
        spec = r.json()
        assert "paths" in spec
        assert len(spec["paths"]) > 0

    def test_gui(self, selenium_app):
        r = requests.get("{}/apidocs/index.html".format(selenium_app))
        r.raise_for_status()
