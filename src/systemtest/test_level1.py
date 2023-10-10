import http.client
from flask.testing import FlaskClient

import pytest

pytestmark = pytest.mark.system


class TestLevel1Views:
    def test_backend_info(self, test_client: FlaskClient):
        """Test raw backend info"""
        # Only V4
        base_url = "/rest_api/{version}/freqmode_raw/{date}/{backend}/"
        r = test_client.get(
            base_url.format(version="v4", date="2015-01-12", backend="AC2")
        )
        assert r.status_code == http.client.OK

    @pytest.mark.parametrize(
        "url",
        (
            "/rest_api/v5/freqmode_raw/2015-01-12/42/",
            "/rest_api/v5/level1/42/7015092840/L1b/",
            "/rest_api/v5/level1/42/7015092840/ptz/",
            "/rest_api/v5/level1/42/7015092840/apriori/O3/",
            "/rest_api/v5/level1/42/7015092840/collocations/",
        ),
    )
    def test_faulty_freqmode(self, test_client: FlaskClient, url):
        """Test calling API with non-existent freqmode"""
        r = test_client.get(url)
        assert r.status_code == http.client.NOT_FOUND

    @pytest.mark.slow
    def test_freqmode_raw_hierarchy(self, test_client: FlaskClient):
        """Test freqmode raw hierarchy flow"""
        base_url = "/rest_api/{version}/freqmode_raw/{date}/"

        # V4
        r = test_client.get(base_url.format(version="v4", date="2015-01-12"))
        assert r.status_code == http.client.OK
        assert r.json
        nr_freqmodes_v4 = len(r.json["Info"])
        next_level_url = r.json["Info"][0]["URL"]
        assert "/v4/" in next_level_url
        r = test_client.get(next_level_url)
        assert r.status_code == http.client.OK
        assert r.json
        nr_scans_v4 = len(r.json["Info"])

        # V5
        r = test_client.get(base_url.format(version="v5", date="2015-01-12"))
        assert r.status_code == http.client.OK
        assert r.json
        nr_freqmodes_v5 = r.json["Count"]
        next_level_url = r.json["Data"][0]["URL"]
        assert "/v5/" in next_level_url
        r = test_client.get(next_level_url)
        assert r.json
        assert r.status_code == http.client.OK
        nr_scans_v5 = r.json["Count"]

        assert nr_freqmodes_v4 == nr_freqmodes_v5
        assert nr_scans_v4 == nr_scans_v5

    def test_get_scan(self, test_client: FlaskClient):
        """Test get scan data"""
        # V4
        base_url = "/rest_api/{version}/scan/{backend}/{freqmode}/{scanid}/"
        r = test_client.get(
            base_url.format(version="v4", backend="AC2", freqmode=1, scanid=7015092840)
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert "Altitude" in r.json

        # V5
        base_url = "/rest_api/{version}/level1/{freqmode}/{scanid}/L1b/"
        r = test_client.get(
            base_url.format(version="v5", freqmode=1, scanid=7015092840)
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert r.json["Type"] == "L1b"
        assert r.json["Data"]["Tcal"][0] == 287.655
        assert r.json["Data"]["MJD"][0] == pytest.approx(57034.2339189)

    def test_get_scan_debug_false(self, test_client: FlaskClient):
        """Test that get scan data debug option works"""
        # Only V5
        base_url = "/rest_api/{version}/level1/{freqmode}/{scanid}/L1b/{debug}"
        r = test_client.get(
            base_url.format(
                version="v5", freqmode=2, scanid=7014771917, debug="?debug=false"
            )
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert r.json["Type"] == "L1b"
        # First two subbands should be discarded in production mode:
        assert r.json["Data"]["Frequency"]["SubBandIndex"][0][0] == -1
        assert r.json["Data"]["Frequency"]["SubBandIndex"][0][1] == -1

    def test_get_scan_debug_true(self, test_client: FlaskClient):
        base_url = "/rest_api/{version}/level1/{freqmode}/{scanid}/L1b/{debug}"
        r = test_client.get(
            base_url.format(
                version="v5", freqmode=2, scanid=7014771917, debug="?debug=true"
            )
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert r.json["Type"] == "L1b"
        # Only the first suband should be discarded in debug mode:
        assert r.json["Data"]["Frequency"]["SubBandIndex"][0][0] == -1
        assert r.json["Data"]["Frequency"]["SubBandIndex"][0][1] == 1

    def test_get_scan_debug_foo(self, test_client: FlaskClient):
        base_url = "/rest_api/{version}/level1/{freqmode}/{scanid}/L1b/{debug}"
        r = test_client.get(
            base_url.format(
                version="v5", freqmode=2, scanid=7014771917, debug="?debug=foo"
            )
        )
        assert r.status_code == http.client.BAD_REQUEST

    def test_get_apriori(self, test_client: FlaskClient):
        """Test get apriori data"""
        # V4
        base_url = (
            "/rest_api/{version}/apriori/O3/{date}/{backend}/{freqmode}/{scanid}/"
        )
        r = test_client.get(
            base_url.format(
                version="v4",
                date="2015-01-12",
                backend="AC2",
                freqmode=1,
                scanid=7015092840,
            )
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert "Pressure" in r.json

        # V5
        base_url = "/rest_api/{version}/level1/{freqmode}/{scanid}/apriori/O3/"
        r = test_client.get(
            base_url.format(version="v5", freqmode=1, scanid=7015092840)
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert r.json["Type"] == "apriori"

    def test_get_collocations(self, test_client):
        """Test get collocations for a scan"""
        # V5
        base_url = "/rest_api/{version}/level1/{freqmode}/{scanid}/collocations/"
        r = test_client.get(
            base_url.format(version="v5", freqmode=1, scanid=1930998606)
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert r.json["Type"] == "collocation"
        assert r.json["Count"] == 7
