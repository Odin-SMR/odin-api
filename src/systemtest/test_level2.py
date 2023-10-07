import http.client
import urllib.request
import urllib.parse
import urllib.error
import uuid
from flask import current_app
from flask.testing import FlaskClient
import numpy as np
import pytest
import simplejson
import link_header  # type: ignore
from odinapi.utils import encrypt_util
from .level2_test_data import (
    insert_test_data,
    insert_failed_scan,
    delete_test_data,
    WRITE_URL,
    get_test_data,
    get_write_url,
    insert_lot_of_test_data,
    insert_inf_test_data,
)

PROJECT_NAME = "testproject"


def make_dev_url(url):
    return url.replace("/level2/", "/level2/development/")


@pytest.fixture
def fake_data(test_client: FlaskClient):
    # Insert level2 data
    _, urlinfo = insert_test_data(PROJECT_NAME)
    _, urlinfo_failed = insert_failed_scan(PROJECT_NAME)

    yield urlinfo, urlinfo_failed

    assert (
        test_client.delete(urlinfo.url).status_code == http.client.NO_CONTENT
    ), f"failed deleting: {__name__}"
    assert (
        test_client.delete(urlinfo_failed.url).status_code == http.client.NO_CONTENT
    ), f"failed deleting: {__name__}"


@pytest.fixture
def fake_data_with_inf(test_client: FlaskClient):
    # Insert level2 data
    r, urlinfo = insert_inf_test_data(PROJECT_NAME)

    yield urlinfo
    assert test_client.delete(urlinfo.url).status_code == http.client.NO_CONTENT


@pytest.fixture
def lot_of_fake_data(test_client: FlaskClient):
    # Insert level2 data
    urlinfos = insert_lot_of_test_data(PROJECT_NAME)
    yield urlinfos
    for urlinfo in urlinfos:
        assert test_client.delete(urlinfo.url).status_code == http.client.NO_CONTENT


class TestProjects:
    def test_get_v4_projects(self, fake_data, test_client):
        """Test get list of projects"""
        url = "/rest_api/v4/level2/projects/"
        projecturl = f"http://localhost/rest_api/v4/level2/{PROJECT_NAME}/"
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        if r.json is not None:
            info = r.json["Info"]
            assert {
                "Name": PROJECT_NAME,
                "URLS": {"URL-project": projecturl},
            } in info["Projects"]

    def test_get_v5_projects(self, fake_data, test_client):
        url = "/rest_api/v5/level2/projects/"
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        if r.json is not None:
            assert len(r.json["Data"]) == 0
        else:
            assert False, "no json"

    def test_get_v5_dev_projects(self, fake_data, test_client):
        url = "/rest_api/v5/level2/projects/"
        projecturl = f"http://localhost/rest_api/v5/level2/{PROJECT_NAME}/"
        r = test_client.get(
            make_dev_url(url),
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        data = r.json["Data"]
        assert {
            "Name": PROJECT_NAME,
            "URLS": {"URL-project": make_dev_url(projecturl)},
        } in data

    @pytest.mark.parametrize("version", ("v4", "v5"))
    def test_get_project(self, fake_data, test_client, version):
        """Test get project info"""
        projinfo, _ = fake_data
        url = f"http://localhost/rest_api/{version}/level2/{PROJECT_NAME}/"
        freqmode_url = f"{url}{projinfo.freq_mode}"
        scans_url = f"{freqmode_url}/scans"

        failed_url = f"{freqmode_url}/failed"
        comments_url = f"{freqmode_url}/comments"

        if version == "v5":
            url = make_dev_url(url)

        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        if version == "v4":
            assert r.json["Info"] == {
                "Name": PROJECT_NAME,
                "FreqModes": [
                    {
                        "FreqMode": 1,
                        "URLS": {
                            "URL-scans": scans_url,
                            "URL-failed": failed_url,
                            "URL-comments": comments_url,
                        },
                    }
                ],
            }
        elif version == "v5":
            scans_url = make_dev_url(scans_url)
            failed_url = make_dev_url(failed_url)
            comments_url = make_dev_url(comments_url)
            assert r.json["Data"] == [
                {
                    "FreqMode": 1,
                    "URLS": {
                        "URL-scans": scans_url,
                        "URL-failed": failed_url,
                        "URL-comments": comments_url,
                    },
                }
            ]
        else:
            raise ValueError("{} not implemented".format(version))


class TestWriteLevel2:
    @pytest.fixture
    def cleanup(self):
        yield
        r, _ = delete_test_data(PROJECT_NAME)

    def test_post_and_delete(self, test_client, cleanup):
        """Test post and delete of level2 data"""
        r, urlinfo = insert_test_data(PROJECT_NAME)
        assert r.status_code == http.client.CREATED
        r = test_client.delete(urlinfo.url, follow_redirects=True)
        assert r.status_code == http.client.NO_CONTENT

    def test_update_data(self, test_client: FlaskClient, cleanup):
        # Post of duplicate should be possible
        # if someone wants to repost data we
        # think there is a good reason for this
        r, urlinfo = insert_test_data(PROJECT_NAME)
        data = urlinfo.data()
        mjd = round(data["L2"][0]["MJD"]) + 1
        data["L2"][0]["MJD"] = mjd
        data["L2"][1]["MJD"] = mjd
        data["L2"][2]["MJD"] = mjd
        r = test_client.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == http.client.CREATED

        # Check that the post above actually
        # updated data
        url = make_dev_url(
            "http://localhost/rest_api/v5/level2/{project}/{freqmode}/{scanid}/".format(
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
                scanid=urlinfo.scan_id,
            )
        )
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        assert r.json
        assert r.json["Data"]["L2"]["Data"][0]["MJD"] == mjd

    def test_posting_failed_scan(self, test_client, cleanup):
        r, urlinfo = insert_test_data(PROJECT_NAME)
        r = test_client.delete(
            urlinfo.url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.NO_CONTENT

        # When processing fails we only get comments
        data = urlinfo.data()
        data_failed = {"L2I": [], "L2": [], "L2C": data["L2C"]}
        r = test_client.post(
            urlinfo.url,
            json=data_failed,
            follow_redirects=True,
        )
        assert r.status_code == http.client.CREATED

    def test_single_product(self, test_client, cleanup):
        """Test post a single product"""
        r, urlinfo = insert_test_data(PROJECT_NAME)
        data = urlinfo.data()
        data["L2"] = data["L2"][0]
        r = test_client.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == http.client.CREATED

    @pytest.mark.parametrize("d", ("", "bad"))
    def test_post_bad_url_d(self, test_client, cleanup, d):
        """Test invalid posts of level2 data"""
        # No url parameter
        url = WRITE_URL.format(
            host="http://localhost",
            version="v5",
            d=d,
        )
        r = test_client.post(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.BAD_REQUEST

    def test_missing_post_data(self, test_client, cleanup):
        data = get_test_data()
        urlinfo = get_write_url(data, PROJECT_NAME)
        r = test_client.post(
            urlinfo.url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.UNSUPPORTED_MEDIA_TYPE

    def test_missing_l2_data(self, test_client, cleanup):
        data = get_test_data()
        urlinfo = get_write_url(data, PROJECT_NAME)
        data.pop("L2")
        r = test_client.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == http.client.BAD_REQUEST

    def test_missing_l2i_scanid_data(self, test_client, cleanup):
        data = get_test_data()
        urlinfo = get_write_url(data, PROJECT_NAME)
        data["L2I"].pop("ScanID")
        r = test_client.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == http.client.BAD_REQUEST

    def test_missing_l2_scanid_data(self, test_client, cleanup):
        data = get_test_data()
        urlinfo = get_write_url(data, PROJECT_NAME)
        data["L2"][0].pop("ScanID")
        r = test_client.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == http.client.BAD_REQUEST

    def test_freqmode_mismatch(self, test_client, cleanup):
        data = get_test_data()
        urlinfo = get_write_url(data, PROJECT_NAME)
        data["L2I"]["FreqMode"] = 2
        r = test_client.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == http.client.BAD_REQUEST

    def test_scanid_mismatch(self, test_client, cleanup):
        data = get_test_data()
        urlinfo = get_write_url(data, PROJECT_NAME)
        data["L2I"]["ScanID"] = 2
        r = test_client.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == http.client.BAD_REQUEST


class TestReadLevel2:
    def test_get_comments_v4(self, fake_data, test_client):
        """Test get list of comments"""
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/comments/".format(
            host="http://localhost",
            version="v4",
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
        )
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        comments = r.json["Info"]["Comments"]
        assert len(comments) == 6

    def test_get_comments_v5(self, fake_data, test_client):
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/comments/".format(
            host="http://localhost",
            version="v5",
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
        )
        r = test_client.get(
            make_dev_url(url),
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        assert r.json["Type"] == "level2_scan_comment"
        comments = r.json["Data"]
        assert len(comments) == 6

    def test_get_comments_v5_respects_limit(self, fake_data, test_client):
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/comments/?limit=1".format(  # noqa
            host="http://localhost",
            version="v5",
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
        )
        r = test_client.get(
            make_dev_url(url),
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        comments = r.json["Data"]
        assert len(comments) == 1
        assert comments[0]["Comment"] == "Error: This scan failed"

    def test_get_comments_v5_respects_offset(self, fake_data, test_client):
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/comments/?offset=5".format(  # noqa
            host="http://localhost",
            version="v5",
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
        )
        r = test_client.get(
            make_dev_url(url),
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        comments = r.json["Data"]
        assert len(comments) == 1
        expected = "Status: 9 spectra left after quality filtering"
        assert comments[0]["Comment"] == expected

    def test_get_comments_v5_empty_if_offset_gt_count(self, fake_data, test_client):
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/comments/?offset=10".format(  # noqa
            host="http://localhost",
            version="v5",
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
        )
        r = test_client.get(
            make_dev_url(url),
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        comments = r.json["Data"]
        assert len(comments) == 0

    def test_get_comments_v5_has_link_header(self, fake_data, test_client):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/comments/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
            )
        )
        r = test_client.get(
            url + "?offset=2&limit=2",
            follow_redirects=True,
        )
        links = link_header.parse(r.headers.get("link", ""))

        match = links.links_by_attr_pairs([("rel", "next")])
        href1 = match[0].href if match else None
        assert href1
        assert "limit=2" in href1
        assert "offset=4" in href1

        match = links.links_by_attr_pairs([("rel", "prev")])
        href2 = match[0].href if match else None
        assert href2
        assert "limit=2" in href2
        assert "offset=0" in href2

    @pytest.mark.parametrize(
        "version,params,expect_scans",
        (
            ("v4", None, 1),
            ("v5", None, 1),
            ("v4", "?start_time=2015-01-12", 1),
            ("v5", "?start_time=2015-01-12", 1),
            ("v4", "?start_time=2015-01-13", 0),
            ("v5", "?start_time=2015-01-13", 0),
            ("v4", "?end_time=2015-01-12", 0),
            ("v5", "?end_time=2015-01-12", 0),
            ("v4", "?end_time=2015-01-13", 1),
            ("v5", "?end_time=2015-01-13", 1),
        ),
    )
    def test_get_scans(
        self,
        fake_data,
        test_client,
        version,
        params,
        expect_scans,
    ):
        """Test get list of matching scans"""
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/scans/".format(
            host="http://localhost",
            version=version,
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
        )
        if version == "v5":
            url = make_dev_url(url)
        if params is not None:
            url += params
        r = test_client.get(
            url,
            follow_redirects=True,
        )

        assert r.status_code == http.client.OK

        if version == "v4":
            scans = r.json["Info"]["Scans"]
        elif version == "v5":
            scans = r.json["Data"]
        else:
            raise NotImplementedError()

        assert len(scans) == expect_scans

        if params is None:
            scan = scans[0]

            if version == "v4":
                assert set(scan["URLS"]) == set(
                    ["URL-level2", "URL-log", "URL-spectra"]
                )
            elif version == "v5":
                assert set(scan["URLS"]) == set(
                    [
                        "URL-level2",
                        "URL-log",
                        "URL-spectra",
                        "URL-ancillary",
                    ]
                )

            assert scan["ScanID"] == urlinfo.scan_id
            assert scan["Date"] == "2015-01-12T00:22:33.349085"

    @pytest.mark.parametrize(
        "version,comment,expected_scans",
        (
            (
                "v4",
                "Status: 9 spectra left after quality filtering",
                1,
            ),
            (
                "v5",
                "Status: 9 spectra left after quality filtering",
                1,
            ),
            (
                "v4",
                "Comment does not exist",
                0,
            ),
            (
                "v5",
                "Comment does not exist",
                0,
            ),
        ),
    )
    def test_get_scans_with_comments(
        self,
        fake_data,
        test_client,
        version,
        comment,
        expected_scans,
    ):
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/scans/".format(
            host="http://localhost",
            version=version,
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
        )
        if version == "v5":
            url = make_dev_url(url)
        r = test_client.get(
            "?".join(
                [
                    url,
                    urllib.parse.urlencode([("comment", comment)]),
                ]
            )
        )

        assert r.status_code == http.client.OK
        if version == "v4":
            scans = r.json["Info"]["Scans"]
        elif version == "v5":
            scans = r.json["Data"]
        else:
            raise NotImplementedError()

        assert len(scans) == expected_scans

    @pytest.fixture
    def extra_scans(self, fake_data, test_client: FlaskClient):
        urlinfo, _ = fake_data

        def insert_new(new_scan_id):
            data = urlinfo.data()
            data["L2I"]["ScanID"] = new_scan_id
            for l2 in data["L2"]:
                l2["ScanID"] = new_scan_id
            info = get_write_url(data, PROJECT_NAME)
            r = test_client.post(
                info.url,
                data=simplejson.dumps(data, allow_nan=True),
                headers={"Content-Type": "application/json"},
            )
            assert r.status_code == http.client.CREATED, f"inserting failed: {__name__}"
            return info

        extra1 = insert_new(urlinfo.scan_id + 42)
        extra2 = insert_new(urlinfo.scan_id + 43)
        yield extra1, extra2

        def delete_extra(info):
            r = test_client.delete(
                info.url,
                data=simplejson.dumps(info.data(), allow_nan=True),
                headers={"Content-Type": "application/json"},
            )
            assert (
                r.status_code == http.client.NO_CONTENT
            ), f"Deleting failed: {__name__}"

        delete_extra(extra1)
        delete_extra(extra2)

    def test_get_scans_respects_limit(
        self,
        test_client: FlaskClient,
        fake_data,
        extra_scans,
    ):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/{freqmode}/scans/?limit=1".format(
                host="http://localhost",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
            )
        )
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        assert r.json
        scans = r.json["Data"]
        assert len(scans) == 1
        assert scans[0]["ScanID"] == urlinfo.scan_id

    def test_get_scans_respects_offset(
        self,
        test_client,
        fake_data,
        extra_scans,
    ):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/{freqmode}/scans/?offset=1".format(
                host="http://localhost",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
            )
        )
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        scans = r.json["Data"]
        assert len(scans) == 2
        assert [s["ScanID"] for s in scans] == [s.scan_id for s in extra_scans]

    def test_get_scans_empty_if_offset_gt_count(
        self,
        test_client,
        fake_data,
        extra_scans,
    ):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/{freqmode}/scans/?offset=10".format(
                host="http://localhost",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
            )
        )
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        scans = r.json["Data"]
        assert len(scans) == 0

    def test_get_scans_has_link_header(
        self,
        test_client,
        fake_data,
        extra_scans,
    ):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/{freqmode}/scans/".format(
                host="http://localhost",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
            )
        )
        r = test_client.get(
            url + "?offset=1&limit=1",
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        links = link_header.parse(r.headers.get("link", ""))

        match = links.links_by_attr_pairs([("rel", "next")])
        href1 = match[0].href if match else None
        assert href1
        assert "limit=1" in href1
        assert "offset=2" in href1

        match = links.links_by_attr_pairs([("rel", "prev")])
        href2 = match[0].href if match else None
        assert href2
        assert "limit=1" in href2
        assert "offset=0" in href2

    def test_get_failed_scans_v4(self, fake_data, test_client):
        """Test get list of failed scans"""
        _, failed = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/failed/".format(
            host="http://localhost",
            version="v4",
            project=PROJECT_NAME,
            freqmode=failed.freq_mode,
        )
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        scans = r.json["Info"]["Scans"]
        assert len(scans) == 1
        scan = scans[0]
        assert scan["ScanID"] == failed.scan_id
        assert scan["Error"] == "Error: This scan failed"
        assert set(scan["URLS"]) == set(
            [
                "URL-level2",
                "URL-log",
                "URL-spectra",
            ]
        )

    def test_get_failed_scans_v5(self, fake_data, test_client):
        _, failed = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/failed/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=failed.freq_mode,
            )
        )
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        assert r.json["Type"] == "level2_failed_scan_info"
        scans = r.json["Data"]
        assert len(scans) == 1
        scan = scans[0]
        assert scan["ScanID"] == failed.scan_id
        assert scan["Error"] == "Error: This scan failed"
        assert set(scan["URLS"]) == set(
            [
                "URL-level2",
                "URL-log",
                "URL-spectra",
                "URL-ancillary",
            ]
        )

    @pytest.fixture
    def extra_failed(self, fake_data, test_client):
        _, failed = fake_data

        def insert_new(new_scan_id):
            r, info = insert_failed_scan(
                PROJECT_NAME,
                new_scan_id,
                freqmode=failed.freq_mode,
            )
            return info

        fail1 = insert_new(failed.scan_id + 42)
        fail2 = insert_new(failed.scan_id + 43)
        yield fail1, fail2

        def remove_inserted(urlinfo):
            r = test_client.delete(
                urlinfo.url,
                json=urlinfo.data(),
                follow_redirects=True,
            )
            assert r.status_code == http.client.NO_CONTENT

        remove_inserted(fail1)
        remove_inserted(fail2)

    def test_get_failed_scans_respsects_limimt_v5(
        self,
        fake_data,
        test_client,
        extra_failed,
    ):
        _, failed = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/failed/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=failed.freq_mode,
            )
        )
        r = test_client.get(
            url + "?limit=1",
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        scans = r.json["Data"]
        assert len(scans) == 1
        assert scans[0]["ScanID"] == failed.scan_id

    def test_get_failed_scans_respects_offset(
        self,
        fake_data,
        test_client,
        extra_failed,
    ):
        _, failed = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/failed/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=failed.freq_mode,
            )
        )
        r = test_client.get(
            url + "?offset=1",
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        scans = r.json["Data"]
        assert len(scans) == 2
        assert [s["ScanID"] for s in scans] == [s.scan_id for s in extra_failed]

    def test_get_failed_scans_empty_if_offset_gt_count(
        self,
        fake_data,
        test_client,
        extra_failed,
    ):
        _, failed = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/failed/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=failed.freq_mode,
            )
        )
        r = test_client.get(
            url + "?offset=10",
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        scans = r.json["Data"]
        assert len(scans) == 0

    def test_get_failed_scans_has_link_header(
        self,
        fake_data,
        test_client,
        extra_failed,
    ):
        _, failed = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/failed/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=failed.freq_mode,
            )
        )
        r = test_client.get(
            url + "?offset=1&limit=1",
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK
        links = link_header.parse(r.headers.get("link", ""))

        match = links.links_by_attr_pairs([("rel", "next")])
        href1 = match[0].href if match else None
        assert href1
        assert "limit=1" in href1
        assert "offset=2" in href1

        match = links.links_by_attr_pairs([("rel", "prev")])
        href2 = match[0].href if match else None
        assert href2
        assert "limit=1" in href2
        assert "offset=0" in href2

    def assert_scansproduct_eq(self, a, b):
        eqtests = ["InvMode", "ScanID", "FreqMode", "Product"]
        for key in eqtests:
            assert a[key] == b[key]

        approxtests = [
            "Altitude",
            "ErrorNoise",
            "AVK",
            "VMR",
            "MJD",
            "Temperature",
            "Pressure",
            "Lon1D",
            "Apriori",
            "ErrorTotal",
            "Longitude",
            "MeasResponse",
            "Lat1D",
            "Latitude",
        ]
        for key in approxtests:
            np.testing.assert_allclose(
                a[key],
                b[key],
                err_msg="Failed on {}".format(key),
            )

        # Dealing with that quality can be nono and nan in weird combos
        aquality = a["Quality"]
        bquality = b["Quality"]
        if aquality is None and bquality is None:
            # Everything good
            pass
        elif aquality is None:
            assert np.isnan(bquality)
        elif bquality is None:
            assert np.isnan(aquality)
        else:
            assert aquality == bquality

    def test_get_scan_v4(self, test_client, fake_data):
        """Test get level2 data for a scan"""
        urlinfo, _ = fake_data
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/{scanid}/".format(
            host="http://localhost",
            version="v4",
            project=PROJECT_NAME,
            freqmode=urlinfo.freq_mode,
            scanid=urlinfo.scan_id,
        )
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        info = r.json["Info"]
        assert set(["L2i", "L2", "L2c", "URLS"]).issubset(list(info.keys()))
        l2 = sorted(urlinfo.data()["L2"], key=lambda d: d["Product"])
        retl2 = sorted(info["L2"], key=lambda d: d["Product"])
        for a, b in zip(retl2, l2):
            self.assert_scansproduct_eq(a, b)

    @pytest.mark.parametrize(
        "freq_mode,scan_id",
        (
            (2, None),
            (0, None),
            (None, 0),
        ),
    )
    def test_get_non_existing_scan_v4(
        self,
        test_client,
        fake_data,
        freq_mode,
        scan_id,
    ):
        urlinfo, _ = fake_data
        if freq_mode is None:
            freq_mode = urlinfo.freq_mode
        if scan_id is None:
            scan_id = urlinfo.scan_id
        url = "{host}/rest_api/{version}/level2/{project}/{freqmode}/{scanid}/".format(
            host="http://localhost",
            version="v4",
            project=PROJECT_NAME,
            freqmode=freq_mode,
            scanid=scan_id,
        )
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.NOT_FOUND

    def test_get_scan_v5(self, test_client, fake_data):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/{scanid}/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
                scanid=urlinfo.scan_id,
            )
        )
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        mixed = r.json
        assert mixed["Type"] == "mixed"
        info = mixed["Data"]
        assert set(["L2i", "L2", "L2c"]).issubset(list(info.keys()))

        test_data = urlinfo.data()
        assert info["L2"]["Count"] == len(test_data["L2"]) == len(info["L2"]["Data"])
        l2 = sorted(test_data["L2"], key=lambda x: x["Product"])
        retl2 = sorted(info["L2"]["Data"], key=lambda x: x["Product"])
        for a, b in zip(retl2, l2):
            self.assert_scansproduct_eq(a, b)

    def test_get_scan_v5_failed_l2_processing(self, test_client):
        data = get_test_data()
        urlinfo = get_write_url(data, PROJECT_NAME)
        data["L2"] = []
        data["L2C"] = "processing failed."
        r = test_client.post(urlinfo.url, json=data, follow_redirects=True)
        assert r.status_code == http.client.CREATED

        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/{scanid}/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
                scanid=urlinfo.scan_id,
            )
        )
        r1 = test_client.get("{}L2c/".format(url), follow_redirects=True)
        r2 = test_client.get(url, follow_redirects=True)
        delete_test_data(PROJECT_NAME)
        assert (
            r1.json["Data"][0] == "processing failed."
            and r2.status_code == http.client.NOT_FOUND
        )

    @pytest.mark.parametrize("part", ("L2i", "L2c", "L2"))
    def test_get_scan_v5_parts(self, test_client, fake_data, part):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/{scanid}/".format(
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
                scanid=urlinfo.scan_id,
            )
        )
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        info = r.json["Data"]
        r = test_client.get(url + "{}/".format(part), follow_redirects=True)
        assert r.status_code == http.client.OK
        assert r.json["Data"] == info[part]["Data"]

    def test_get_scan_v5_part_by_product(self, test_client, fake_data):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/{scanid}/L2/".format(  # noqa
                host="http://localhost",
                version="v5",
                project=PROJECT_NAME,
                freqmode=urlinfo.freq_mode,
                scanid=urlinfo.scan_id,
            )
        )
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        info = r.json["Data"]

        product = "O3 / 501 GHz / 20 to 50 km"
        r = test_client.get(url + "?product={}".format(product), follow_redirects=True)
        assert r.status_code == http.client.OK
        data = r.json["Data"]
        assert data == [p for p in info if p["Product"] == product]

    @pytest.mark.parametrize("version", ("v4", "v5"))
    def test_get_products(self, test_client, fake_data, version):
        """Test get products"""
        url = "{host}/rest_api/{version}/level2/{project}/products/".format(
            host="http://localhost",
            version=version,
            project=PROJECT_NAME,
        )
        if version == "v5":
            url = make_dev_url(url)

        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK

        if version == "v4":
            products = r.json["Info"]["Products"]
        elif version == "v5":
            products = r.json["Data"]
        else:
            raise NotImplementedError()
        assert len(products) == 3

    @pytest.mark.parametrize("version", ("v4", "v5"))
    def test_get_products_for_freqmode(self, test_client, fake_data, version):
        urlinfo, _ = fake_data
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/products/".format(
                host="http://localhost",
                version=version,
                freqmode=urlinfo.freq_mode,
                project=PROJECT_NAME,
            )
        )
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        if version == "v4":
            products = r.json["Info"]["Products"]
        elif version == "v5":
            products = r.json["Data"]
        else:
            raise NotImplementedError()
        assert len(products) == 3

    @pytest.mark.parametrize("version", ("v4", "v5"))
    def test_get_products_for_missing_freqmode(self, version, test_client):
        url = make_dev_url(
            "{host}/rest_api/{version}/level2/{project}/{freqmode}/products/".format(
                host="http://localhost",
                version=version,
                freqmode=2,
                project=PROJECT_NAME,
            )
        )
        r = test_client.get(url, follow_redirects=True)
        assert r.status_code == http.client.OK
        if version == "v4":
            products = r.json["Info"]["Products"]
        elif version == "v5":
            products = r.json["Data"]
        else:
            raise NotImplementedError()
        assert len(products) == 0

    def validate_v4_results(self, url, nr_expected, expected_l2):
        r = current_app.test_client().get(url)
        assert r.status_code == http.client.OK
        assert r.json
        results = r.json["Info"]["Results"]
        assert len(results) == nr_expected
        assert (
            len(set((result["Product"], result["ScanID"]) for result in results))
            == expected_l2
        )

    def validate_v5_results(self, url, nr_expected, expected_l2):
        r = current_app.test_client().get(url)
        assert r.status_code == http.client.OK
        assert r.json
        results = r.json["Data"]
        # Results are grouped by scan and product
        assert len(results) == expected_l2
        inversions = sum((len(l2["VMR"]) for l2 in results), 0)
        assert inversions == nr_expected

    @pytest.mark.parametrize(
        "locations,radius,nr_expected,param",
        (
            (["-6.0,95.0"], 30, 5, dict(min_pressure=1, start_time="2015-01-01")),
            (
                ["-6.0,95.0"],
                30,
                2,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0"],
                100,
                7,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0"],
                100,
                3,
                dict(
                    max_altitude=55000,
                    product="O3 / 501 GHz / 20 to 50 km",
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0"],
                1000,
                25,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0", "-10,94.3"],
                30,
                4,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
        ),
    )
    def test_get_locations_v4(
        self,
        locations,
        radius,
        nr_expected,
        param,
        test_client,
        fake_data,
    ):
        """Test level2 get locations endpoint"""
        expected_l2 = 3 if nr_expected != 0 else 0
        if "product" in param:
            expected_l2 = 1
        url = "{host}/rest_api/v4/level2/{project}/locations".format(
            host="http://localhost", project=PROJECT_NAME
        )
        uparam = [("location", loc) for loc in locations]
        uparam += [("radius", radius)]
        if param:
            uparam += [(k, str(v)) for k, v in list(param.items())]
        url += "?%s" % urllib.parse.urlencode(uparam)
        self.validate_v4_results(url, nr_expected, expected_l2)

    @pytest.mark.parametrize(
        "locations,radius,nr_expected,param",
        (
            (["-6.0,95.0"], 30, 5, dict(min_pressure=1, start_time="2015-01-01")),
            (
                ["-6.0,95.0"],
                30,
                2,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0"],
                100,
                7,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0"],
                100,
                3,
                dict(
                    max_altitude=55000,
                    product="O3 / 501 GHz / 20 to 50 km",
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0"],
                1000,
                25,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                ["-6.0,95.0", "-10,94.3"],
                30,
                4,
                dict(
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
        ),
    )
    def test_get_locations_v5(
        self,
        locations,
        radius,
        nr_expected,
        param,
        test_client: FlaskClient,
        fake_data,
    ):
        """Test level2 get locations endpoint"""
        expected_l2 = 3 if nr_expected != 0 else 0
        if "product" in param:
            expected_l2 = 1
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/locations".format(
                host="http://localhost", project=PROJECT_NAME
            ),
        )
        uparam = [("location", loc) for loc in locations]
        uparam += [("radius", radius)]
        uparam += [(k, str(v)) for k, v in list(param.items())]
        url += "?%s" % urllib.parse.urlencode(uparam)
        self.validate_v5_results(url, nr_expected, expected_l2)

    @pytest.mark.parametrize(
        "date,nr_expected,param",
        (
            ("2016-10-06", 0, dict(min_pressure=1)),
            ("2015-04-01", 61, dict(min_pressure=1)),
            (
                "2015-04-01",
                1,
                dict(
                    min_pressure=1000,
                    max_pressure=1000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                11,
                dict(min_pressure=1000, product="O3 / 501 GHz / 20 to 50 km"),
            ),
            (
                "2015-04-01",
                15,
                dict(
                    max_pressure=1000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                6,
                dict(
                    min_altitude=20000,
                    max_altitude=30000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                21,
                dict(
                    min_altitude=20000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                4,
                dict(
                    max_altitude=20000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            ("2015-04-01", 15, dict(min_altitude=20000, max_altitude=30000)),
        ),
    )
    def test_get_date_v4(
        self,
        date,
        nr_expected,
        param,
        test_client,
        fake_data,
    ):
        expected_l2 = 3 if nr_expected != 0 else 0
        if "product" in param:
            expected_l2 = 1

        url = "{host}/rest_api/v4/level2/{project}/{date}/".format(
            host="http://localhost",
            project=PROJECT_NAME,
            date=date,
        )
        if param:
            url += "?%s" % urllib.parse.urlencode(param)
        self.validate_v4_results(url, nr_expected, expected_l2)

    @pytest.mark.parametrize(
        "date,nr_expected,param",
        (
            ("2016-10-06", 0, dict(min_pressure=1)),
            ("2015-04-01", 61, dict(min_pressure=1)),
            (
                "2015-04-01",
                1,
                dict(
                    min_pressure=1000,
                    max_pressure=1000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                11,
                dict(
                    min_pressure=1000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                15,
                dict(
                    max_pressure=1000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                6,
                dict(
                    min_altitude=20000,
                    max_altitude=30000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                21,
                dict(
                    min_altitude=20000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            (
                "2015-04-01",
                4,
                dict(
                    max_altitude=20000,
                    product="O3 / 501 GHz / 20 to 50 km",
                ),
            ),
            ("2015-04-01", 15, dict(min_altitude=20000, max_altitude=30000)),
        ),
    )
    def test_get_date_v5(
        self,
        date,
        nr_expected,
        param,
        test_client,
        fake_data,
    ):
        expected_l2 = 3 if nr_expected != 0 else 0
        if "product" in param:
            expected_l2 = 1

        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/{date}/".format(
                host="http://localhost",
                project=PROJECT_NAME,
                date=date,
            ),
        )
        url += "?%s" % urllib.parse.urlencode(param)
        self.validate_v5_results(url, nr_expected, expected_l2)

    @pytest.mark.parametrize(
        "nr_expected,param",
        (
            (61, dict(start_time="2015-03-02", min_pressure=1)),
            (0, dict(start_time="2015-04-02", min_pressure=1)),
            (61, dict(end_time="2015-04-02", min_pressure=1)),
            (0, dict(end_time="2015-03-02", min_pressure=1)),
            (
                6,
                dict(
                    min_lat=-7,
                    min_lon=95,
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                17,
                dict(
                    max_lat=-7,
                    max_lon=95,
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                2,
                dict(
                    min_lat=-7,
                    max_lat=-6,
                    min_lon=95,
                    max_lon=95.1,
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
        ),
    )
    def test_get_area_v4(
        self,
        nr_expected,
        param,
        test_client,
        fake_data,
    ):
        expected_l2 = 3 if nr_expected != 0 else 0
        if "product" in param:
            expected_l2 = 1

        url = "{host}/rest_api/v4/level2/{project}/area".format(
            host="http://localhost",
            project=PROJECT_NAME,
        )
        if param:
            url += "?%s" % urllib.parse.urlencode(param)
        self.validate_v4_results(url, nr_expected, expected_l2)

    @pytest.mark.parametrize(
        "nr_expected,param",
        (
            (61, dict(start_time="2015-03-02", min_pressure=1)),
            (0, dict(start_time="2015-04-02", min_pressure=1)),
            (61, dict(end_time="2015-04-02", min_pressure=1)),
            (0, dict(end_time="2015-03-02", min_pressure=1)),
            (
                6,
                dict(
                    min_lat=-7,
                    min_lon=95,
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                17,
                dict(
                    max_lat=-7,
                    max_lon=95,
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
            (
                2,
                dict(
                    min_lat=-7,
                    max_lat=-6,
                    min_lon=95,
                    max_lon=95.1,
                    product="O3 / 501 GHz / 20 to 50 km",
                    min_pressure=1,
                    start_time="2015-01-01",
                ),
            ),
        ),
    )
    def test_get_area_v5(
        self,
        nr_expected,
        param,
        test_client,
        fake_data,
    ):
        expected_l2 = 3 if nr_expected != 0 else 0
        if "product" in param:
            expected_l2 = 1

        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/area".format(
                host="http://localhost",
                project=PROJECT_NAME,
            )
        )
        if param:
            url += "?%s" % urllib.parse.urlencode(param)
        self.validate_v5_results(url, nr_expected, expected_l2)

    @pytest.mark.parametrize(
        "min_scanid,expect_scanids",
        (
            (0, range(7014791072, 7014791088)),
            (7014791088, range(7014791088, 7014791102)),
            (7014791101, [7014791101]),
        ),
    )
    def test_get_area_v5_paging_returns_ok_data(
        self, test_client, lot_of_fake_data, min_scanid, expect_scanids
    ):
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/area".format(
                host="http://localhost",
                project=PROJECT_NAME,
            )
        )
        param = dict(
            start_time="2015-03-02",
            min_pressure=1,
            document_limit=1000,
            min_scanid=min_scanid,
        )
        url += "?%s" % urllib.parse.urlencode(param)
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        products = r.json["Data"]
        assert set([product["ScanID"] for product in products]) == set(expect_scanids)

    @pytest.mark.parametrize(
        "min_scanid,expect_link,expect_url",
        (
            (0, True, "min_scanid=7014791088"),
            (7014791088, False, None),
        ),
    )
    def test_get_area_v5_paging_returns_ok_or_no_links(
        self,
        test_client: FlaskClient,
        lot_of_fake_data,
        min_scanid,
        expect_link,
        expect_url,
    ):
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/area".format(
                host="http://localhost",
                project=PROJECT_NAME,
            )
        )
        param = dict(
            start_time="2015-03-02",
            min_pressure=1,
            document_limit=1000,
            min_scanid=min_scanid,
            min_lat=-90,
        )
        url += "?%s" % urllib.parse.urlencode(param)
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        links = link_header.parse(r.headers.get("link", ""))
        match = links.links_by_attr_pairs([("rel", "next")])
        href = match[0].href if match else None
        if expect_link:
            assert href
            assert expect_url in href
            r = test_client.get(href, follow_redirects=True)
            assert r.status_code == http.client.OK
            assert "link" not in r.headers
        else:
            assert href is None

    @pytest.mark.parametrize(
        "min_scanid,expect_link,expect_url",
        (
            (0, True, "min_scanid=7014791088"),
            (7014791088, False, None),
        ),
    )
    def test_get_locations_v5_paging_returns_ok_or_no_links(
        self,
        test_client: FlaskClient,
        lot_of_fake_data,
        min_scanid,
        expect_link,
        expect_url,
    ):
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/locations".format(
                host="http://localhost", project=PROJECT_NAME
            )
        )
        param = dict(
            start_time="2015-03-02",
            min_pressure=1,
            document_limit=1000,
            min_scanid=min_scanid,
            radius=6371000,
            location="0,180",
        )
        r = test_client.get(
            url,
            query_string=param,
            follow_redirects=True,
        )
        links = link_header.parse(r.headers.get("link", ""))
        match = links.links_by_attr_pairs([("rel", "next")])
        href = match[0].href if match else None
        if expect_link:
            assert href
            assert expect_url in href
            r = test_client.get(href, follow_redirects=True)
            assert r.status_code == http.client.OK
            assert "link" not in r.headers
        else:
            assert href is None

    @pytest.mark.parametrize(
        "min_scanid,expect_link,expect_url",
        (
            (0, True, "min_scanid=7014791088"),
            (7014791088, False, None),
        ),
    )
    def test_get_date_v5_paging_returns_ok_or_no_links(
        self,
        test_client: FlaskClient,
        lot_of_fake_data,
        min_scanid,
        expect_link,
        expect_url,
    ):
        date = "2015-04-01"
        url = make_dev_url(
            "{host}/rest_api/v5/level2/{project}/{date}".format(
                host="http://localhost",
                project=PROJECT_NAME,
                date=date,
            ),
        )
        param = dict(min_pressure=1, document_limit=10, min_scanid=min_scanid)
        # url += "?%s" % urllib.parse.urlencode(param)
        r = test_client.get(
            url,
            query_string=param,
            follow_redirects=True,
        )
        links = link_header.parse(r.headers.get("link", ""))
        match = links.links_by_attr_pairs([("rel", "next")])
        href = match[0].href if match else None
        if expect_link:
            assert href
            assert expect_url in href
            r = test_client.get(href, follow_redirects=True)
            assert r.status_code == http.client.OK
            assert "link" not in r.headers
        else:
            assert href is None

    @pytest.mark.parametrize(
        "url,status,param",
        (
            # Not published
            (
                "/rest_api/v5/level2/{}/area".format(PROJECT_NAME),
                http.client.NOT_FOUND,
                None,
            ),
            (
                "/rest_api/v5/level2/{}/locations".format(PROJECT_NAME),
                http.client.NOT_FOUND,
                None,
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                None,
            ),
            (
                "/rest_api/v5/level2/development/{}/locations".format(
                    PROJECT_NAME,
                ),
                http.client.BAD_REQUEST,
                dict(location="-10,10"),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(radius=100, location="-91,100"),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(radius=100, location="91,100"),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(radius=100, location="-10,-1"),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(radius=100, location="-10,361"),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(min_pressure=1000, max_pressure=100),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(min_altitude=50000, max_altitude=10000),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(start_time="2015-01-01", end_time="2014-01-01"),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(min_lat=-5, max_lat=-10),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(min_lon=100, max_lon=90),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(min_pressure=1000, max_altitude=100000),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(max_altitude=20000),
            ),
            (
                "/rest_api/v5/level2/development/{}/area".format(PROJECT_NAME),
                http.client.BAD_REQUEST,
                dict(start_time="2015-01-01", end_time="2015-12-31"),
            ),
        ),
    )
    def test_bad_requests(
        self,
        url,
        status,
        param,
        test_client,
        fake_data,
    ):
        if param:
            url += "?%s" % urllib.parse.urlencode(param)
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == status

    def test_doesnt_return_infs(
        self,
        test_client,
        fake_data_with_inf,
    ):
        (scanid,) = (fake_data_with_inf.scan_id,)
        freqmode = fake_data_with_inf.freq_mode
        url = f"/rest_api/v5/level2/development/{PROJECT_NAME}/{freqmode}/{scanid}/"  # noqa
        r = test_client.get(
            url,
            follow_redirects=True,
        )
        assert r.status_code == http.client.OK, r.text
        assert "NaN" not in r.text
        assert '"MinLmFactor": null' in r.text


class TestPublishProject:
    @pytest.fixture
    def project(self, test_client):
        project = str(uuid.uuid1())
        insert_test_data(project)
        yield project
        delete_test_data(project)

    def test_publish(self, test_client, project):
        self.assert_not_published(project)
        response = test_client.post(
            self.development_url(project) + "publish",
            auth=("bob", encrypt_util.SECRET_KEY),
        )
        assert response.status_code == http.client.CREATED
        assert self.production_url(
            project,
        ).endswith(response.headers["location"])
        self.assert_published(project)

    def test_publish_unknown_project(self, test_client):
        response = test_client.post(
            self.development_url("unknown-project") + "publish",
            auth=("bob", encrypt_util.SECRET_KEY),
        )
        assert response.status_code == http.client.NOT_FOUND

    def test_no_credentials(self, test_client, project):
        self.assert_not_published(project)
        response = test_client.post(
            self.development_url(project) + "publish",
        )
        assert response.status_code == http.client.UNAUTHORIZED
        self.assert_not_published(project)

    def test_bad_credentials(self, test_client, project):
        self.assert_not_published(project)
        response = test_client.post(
            self.development_url(project) + "publish",
            auth=("bob", "password"),
        )
        assert response.status_code == http.client.UNAUTHORIZED
        self.assert_not_published(project)

    def assert_not_published(self, project):
        requests = current_app.test_client()
        assert requests.get(self.development_url(project)).status_code == http.client.OK
        assert (
            not requests.get(self.production_url(project)).status_code == http.client.OK
        )

    def assert_published(self, project):
        requests = current_app.test_client()
        assert requests.get(self.production_url(project)).status_code == http.client.OK
        assert (
            not requests.get(self.development_url(project)).status_code
            == http.client.OK
        )

    def development_url(self, project):
        return make_dev_url(self.production_url(project))

    def production_url(self, project):
        url = "{host}/rest_api/{version}/level2/{project}/"
        return url.format(host="http://localhost", version="v5", project=project)
