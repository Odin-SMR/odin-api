from datetime import datetime, timedelta
import http.client
import uuid

import dateutil.parser
from dateutil.tz import tzutc
import pytest
import requests
import simplejson

from ..level2_test_data import VERSION, get_test_data
from odinapi.utils import encrypt_util

WRITE_URL = "{host}/rest_api/{version}/level2?d={d}"


def make_project_url(baseurl, project):
    return "{}/rest_api/v5/level2/{}".format(baseurl, project)


@pytest.fixture
def project(selenium_app):
    data = get_test_data()
    project = str(uuid.uuid1())
    freq_mode = data["L2I"]["FreqMode"]
    scan_id = data["L2I"]["ScanID"]
    payload = encrypt_util.encode_level2_target_parameter(scan_id, freq_mode, project)
    wurl = WRITE_URL.format(host=selenium_app, version=VERSION, d=payload)
    requests.post(
        wurl,
        data=simplejson.dumps(data, allow_nan=True),
        headers={"Content-Type": "application/json"},
    ).raise_for_status()
    return make_project_url(selenium_app, project)


def test_get_empty_annotations(project, selenium_app):
    response = requests.get(project + "/annotations")
    assert response.status_code == http.client.OK
    assert response.json()["Data"] == []


def test_get_annotations_unknown_project(selenium_app):
    project = make_project_url(selenium_app, "unknown")
    response = requests.get(project + "/annotations")
    assert response.status_code == http.client.NOT_FOUND


def test_post(selenium_app, project):
    response = requests.post(
        project + "/annotations",
        json={"Text": "This is a freqmode", "FreqMode": 13},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    now = datetime.utcnow().replace(tzinfo=tzutc())
    assert response.status_code == http.client.CREATED
    response = requests.get(project + "/annotations")
    assert response.status_code == http.client.OK
    assert len(response.json()["Data"]) == 1
    annotation = response.json()["Data"][0]
    assert annotation["Text"] == "This is a freqmode"
    assert annotation["FreqMode"] == 13
    assert dateutil.parser.parse(annotation["CreatedAt"]) - now < abs(
        timedelta(minutes=1)
    )


def test_post_multiple(selenium_app, project):
    now = datetime.utcnow().replace(tzinfo=tzutc())
    requests.post(
        project + "/annotations",
        json={"Text": "This is a project"},
        auth=("bob", encrypt_util.SECRET_KEY),
    ).raise_for_status()
    response = requests.post(
        project + "/annotations",
        json={"Text": "This is a freqmode", "FreqMode": 13},
        auth=("bob", encrypt_util.SECRET_KEY),
    ).raise_for_status()
    response = requests.get(project + "/annotations")
    assert response.status_code == http.client.OK
    annotations = response.json()["Data"]
    assert len(annotations) == 2
    assert annotations[0]["Text"] == "This is a project"
    assert annotations[0].get("FreqMode") is None
    assert dateutil.parser.parse(annotations[0]["CreatedAt"]) - now < abs(
        timedelta(minutes=1)
    )
    assert annotations[1]["Text"] == "This is a freqmode"
    assert annotations[1].get("FreqMode") == 13
    assert dateutil.parser.parse(annotations[1]["CreatedAt"]) - now < abs(
        timedelta(minutes=1)
    )


def test_post_unknown_project(selenium_app):
    project = make_project_url(selenium_app, "unknown")
    response = requests.post(
        project + "/annotations",
        json={"Text": "This is a project"},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.NOT_FOUND


def test_post_bad_text(selenium_app, project):
    response = requests.post(
        project + "/annotations",
        json={"Text": 0000},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_no_text(selenium_app, project):
    response = requests.post(
        project + "/annotations",
        json={},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_bad_freqmode(selenium_app, project):
    response = requests.post(
        project + "/annotations",
        json={"Text": "xxx", "FreqMode": "abcd"},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_no_credentials(selenium_app, project):
    response = requests.post(
        project + "/annotations",
        json={"Text": "This is a project"},
    )
    assert response.status_code == http.client.UNAUTHORIZED


def test_post_bad_credentials(selenium_app, project):
    response = requests.post(
        project + "/annotations",
        json={"Text": "This is a project"},
        auth=("bob", "password"),
    )
    assert response.status_code == http.client.UNAUTHORIZED
