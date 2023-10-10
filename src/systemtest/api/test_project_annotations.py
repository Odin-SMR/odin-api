from datetime import datetime, timedelta
import http.client
import uuid

import dateutil.parser
from flask.testing import FlaskClient
import pytest
import json

from ..level2_test_data import VERSION, get_test_data
from odinapi.utils import encrypt_util

pytestmark = pytest.mark.system
WRITE_URL = "/rest_api/{version}/level2?d={d}"


def make_project_url(project):
    return "/rest_api/v5/level2/{}".format(project)


@pytest.fixture
def project(test_client: FlaskClient):
    data = get_test_data()
    project = str(uuid.uuid1())
    freq_mode = data["L2I"]["FreqMode"]
    scan_id = data["L2I"]["ScanID"]
    payload = encrypt_util.encode_level2_target_parameter(scan_id, freq_mode, project)
    wurl = WRITE_URL.format(version=VERSION, d=payload)
    r = test_client.post(
        wurl,
        data=json.dumps(data, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == http.client.CREATED
    return make_project_url(project)


def test_get_empty_annotations(project, test_client: FlaskClient):
    response = test_client.get(project + "/annotations")
    assert response.json
    assert response.status_code == http.client.OK
    assert response.json["Data"] == []


def test_get_annotations_unknown_project(test_client: FlaskClient):
    project = make_project_url("unknown")
    response = test_client.get(project + "/annotations")
    assert response.status_code == http.client.NOT_FOUND


def test_post(test_client: FlaskClient, project):
    response = test_client.post(
        project + "/annotations",
        json={"Text": "This is a freqmode", "FreqMode": 13},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    now = datetime.utcnow()
    assert response.status_code == http.client.CREATED
    response = test_client.get(project + "/annotations")
    assert response.status_code == http.client.OK
    assert response.json
    assert len(response.json["Data"]) == 1
    annotation = response.json["Data"][0]
    assert annotation["Text"] == "This is a freqmode"
    assert annotation["FreqMode"] == 13
    assert dateutil.parser.parse(annotation["CreatedAt"]) - now < abs(
        timedelta(minutes=1)
    )


def test_post_multiple(test_client: FlaskClient, project):
    now = datetime.utcnow()
    r = test_client.post(
        project + "/annotations",
        json={"Text": "This is a project"},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert r.status_code == http.client.CREATED
    r = response = test_client.post(
        project + "/annotations",
        json={"Text": "This is a freqmode", "FreqMode": 13},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert r.status_code == http.client.CREATED
    response = test_client.get(project + "/annotations")
    assert response.status_code == http.client.OK
    assert response.json
    annotations = response.json["Data"]
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


def test_post_unknown_project(test_client: FlaskClient):
    project = make_project_url("unknown")
    response = test_client.post(
        project + "/annotations",
        json={"Text": "This is a project"},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.NOT_FOUND


def test_post_bad_text(test_client: FlaskClient, project):
    response = test_client.post(
        project + "/annotations",
        json={"Text": 0000},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_no_text(test_client: FlaskClient, project):
    response = test_client.post(
        project + "/annotations",
        json={},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_bad_freqmode(test_client: FlaskClient, project):
    response = test_client.post(
        project + "/annotations",
        json={"Text": "xxx", "FreqMode": "abcd"},
        auth=("bob", encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_no_credentials(test_client: FlaskClient, project):
    response = test_client.post(
        project + "/annotations",
        json={"Text": "This is a project"},
    )
    assert response.status_code == http.client.UNAUTHORIZED


def test_post_bad_credentials(test_client: FlaskClient, project):
    response = test_client.post(
        project + "/annotations",
        json={"Text": "This is a project"},
        auth=("bob", "password"),
    )
    assert response.status_code == http.client.UNAUTHORIZED
