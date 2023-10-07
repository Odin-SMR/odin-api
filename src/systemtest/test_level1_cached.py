import http.client
import pytest
import requests
from datetime import datetime
from odinapi.views.views_cached import (
    get_scan_logdata_cached,
    get_scan_logdata_uncached,
)

pytestmark = pytest.mark.system


class TestLevel1CachedViews:
    def test_backend_info(self, selenium_app):
        """Test cached backend info"""
        # Only V4
        base_url = "{host}/rest_api/{version}/freqmode_info/{date}/" "{backend}/"
        r = requests.get(
            base_url.format(
                host=selenium_app,
                version="v4",
                date="2015-01-15",
                backend="AC2",
            )
        )
        assert r.status_code == http.client.OK

    @pytest.mark.parametrize(
        "url",
        (
            "{}/rest_api/v4/l1_log/42/7019446353",
            "{}/rest_api/v4/freqmode_info/2015-01-15/AC1/42",
            "{}/rest_api/v5/level1/42/7019446353/Log",
            "{}/rest_api/v5/freqmode_info/2015-01-15/42",
            "{}/rest_api/v5/level1/42/scans/?start_time=2015-01-11&end_time=2015-01-13",  # noqa,
        ),
    )
    def test_faulty_freqmode(self, selenium_app, url):
        """Test calling API with non-existent freqmode"""
        # V4
        r = requests.get(url.format(selenium_app))
        assert r.status_code == http.client.NOT_FOUND

    def test_freqmode_info_hierarchy(self, selenium_app):
        """Test cached freqmode info hierarchy flow"""
        base_url = "/".join(
            (
                selenium_app,
                "rest_api/{version}/freqmode_info/{date}/",
            )
        )

        # V4
        r = requests.get(base_url.format(version="v4", date="2015-01-15"))
        assert r.status_code == http.client.OK
        nr_freqmodes_v4 = len(r.json()["Info"])
        next_level_url = r.json()["Info"][0]["URL"]
        assert "/v4/" in next_level_url
        r = requests.get(next_level_url)
        assert r.status_code == http.client.OK
        nr_scans_v4 = len(r.json()["Info"])

        # V5
        r = requests.get(base_url.format(version="v5", date="2015-01-15"))
        assert r.status_code == http.client.OK
        nr_freqmodes_v5 = r.json()["Count"]
        next_level_url = r.json()["Data"][0]["URL"]
        assert "/v5/" in next_level_url
        r = requests.get(next_level_url)
        assert r.status_code == http.client.OK
        nr_scans_v5 = r.json()["Count"]
        assert nr_freqmodes_v4 == nr_freqmodes_v5
        assert nr_scans_v4 == nr_scans_v5

    def test_scan_log(self, selenium_app):
        """Test get cached level1 log data for a scan"""
        # V4
        r = requests.get(
            "{}/rest_api/v4/l1_log/2/7019446353".format(selenium_app),
        )
        assert r.status_code == http.client.OK
        assert r.json()["Info"]["URLS"][
            "URL-ptz"
        ] == "{}/rest_api/v4/ptz/2015-01-15/AC1/2/7019446353/".format(selenium_app)

        # V5
        r = requests.get(
            "{}/rest_api/v5/level1/2/7019446353/Log".format(selenium_app),
        )
        assert r.status_code == http.client.OK
        assert r.json()["Type"] == "Log"
        assert r.json()["Data"]["URLS"][
            "URL-ptz"
        ] == "{}/rest_api/v5/level1/2/7019446353/ptz/".format(selenium_app)

    def test_period_info(self, selenium_app):
        """Test get period info"""
        base_url = "/".join(
            (
                selenium_app,
                "/rest_api/{version}/period_info/{year}/{month}/{day}",
            )
        )

        # V4
        r = requests.get(
            base_url.format(version="v4", year="2015", month="01", day="15")
        )
        assert r.status_code == http.client.OK
        nr_freqmodes_v4 = len(r.json()["Info"])

        # V5
        r = requests.get(
            base_url.format(version="v5", year="2015", month="01", day="15")
        )
        assert r.status_code == http.client.OK
        nr_freqmodes_v5 = r.json()["Count"]
        assert r.json()["PeriodStart"] == "2015-01-15"
        assert nr_freqmodes_v4 == nr_freqmodes_v5

    @pytest.mark.parametrize(
        "start_time,end_time,apriori,expect_status,expect_count, expect_url_count",  # noqa
        (
            ("2015-01-11", "2015-01-12", "", http.client.OK, 489, 3),
            ("2015-01-11", "2015-01-13", "", http.client.OK, 805, 3),
            (
                "2015-01-13",
                "2015-01-11",
                "",
                http.client.BAD_REQUEST,
                None,
                None,
            ),
            (
                "2015-01-11",
                "2015-01-12",
                "&apriori=BrO&apriori=O3",
                http.client.OK,
                489,
                5,
            ),
            (
                "2015-01-11",
                "2015-01-12",
                "&apriori=all",
                http.client.OK,
                489,
                43,
            ),
        ),
    )
    def test_scan_list(
        self,
        selenium_app,
        start_time,
        end_time,
        apriori,
        expect_status,
        expect_count,
        expect_url_count,
    ):
        """Test getting list of scans for period"""
        base_url = "/".join(
            (
                selenium_app,
                "/rest_api/v5/level1/1/scans/?start_time={start_time}&end_time={end_time}{apriori}",  # noqa
            )
        )

        r = requests.get(
            base_url.format(
                start_time=start_time,
                end_time=end_time,
                apriori=apriori,
            )
        )
        assert r.status_code == expect_status
        if r.status_code == http.client.OK:
            assert r.json()["Count"] == expect_count
            assert len(r.json()["Data"][0]["URLS"]) == expect_url_count


def test_get_scan_logdata_cached_returns_consistent_datetime(db_context):
    date = None
    freqmode = 2
    scanid = 7014785316
    data1 = get_scan_logdata_uncached(freqmode, scanid)
    data2 = get_scan_logdata_cached(date, freqmode, scanid=scanid)
    assert isinstance(data1["DateTime"][0], datetime)
    assert data1["DateTime"] == data2["DateTime"]
