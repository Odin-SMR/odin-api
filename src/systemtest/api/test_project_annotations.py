from datetime import datetime, timedelta
import http.client
import uuid

import dateutil.parser
from dateutil.tz import tzutc
import pytest
import requests

from ..level2_test_data import WRITE_URL, VERSION, get_test_data
from odinapi.utils import encrypt_util


def make_project_url(baseurl, project):
    return '{}/rest_api/v5/level2/{}'.format(baseurl, project)


@pytest.fixture
def project(odinapi_service):
    data = get_test_data()
    project = str(uuid.uuid1())
    freq_mode = data['L2I']['FreqMode']
    scan_id = data['L2I']['ScanID']
    payload = encrypt_util.encode_level2_target_parameter(
        scan_id, freq_mode, project
    )
    wurl = WRITE_URL.format(host=odinapi_service, version=VERSION, d=payload)
    requests.post(wurl, json=data).raise_for_status()
    return make_project_url(odinapi_service, project)


def test_get_empty_annotations(project, odinapi_service):
    response = requests.get(project + '/annotations')
    assert response.status_code == http.client.OK
    assert response.json()['Data'] == []


def test_get_annotations_unknown_project(odinapi_service):
    project = make_project_url(odinapi_service, 'unknown')
    response = requests.get(project + '/annotations')
    assert response.status_code == http.client.NOT_FOUND


def test_post(odinapi_service, project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a freqmode', 'FreqMode': 13},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    now = datetime.utcnow().replace(tzinfo=tzutc())
    assert response.status_code == http.client.CREATED
    response = requests.get(project + '/annotations')
    assert response.status_code == http.client.OK
    assert len(response.json()['Data']) == 1
    annotation = response.json()['Data'][0]
    assert annotation['Text'] == 'This is a freqmode'
    assert annotation['FreqMode'] == 13
    assert (
        dateutil.parser.parse(annotation['CreatedAt']) - now
        < abs(timedelta(minutes=1))
    )


def test_post_multiple(odinapi_service, project):
    now = datetime.utcnow().replace(tzinfo=tzutc())
    requests.post(
        project + '/annotations',
        json={'Text': 'This is a project'},
        auth=('bob', encrypt_util.SECRET_KEY),
    ).raise_for_status()
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a freqmode', 'FreqMode': 13},
        auth=('bob', encrypt_util.SECRET_KEY),
    ).raise_for_status()
    response = requests.get(project + '/annotations')
    assert response.status_code == http.client.OK
    annotations = response.json()['Data']
    assert len(annotations) == 2
    assert annotations[0]['Text'] == 'This is a project'
    assert annotations[0].get('FreqMode') is None
    assert (
        dateutil.parser.parse(annotations[0]['CreatedAt']) - now
        < abs(timedelta(minutes=1))
    )
    assert annotations[1]['Text'] == 'This is a freqmode'
    assert annotations[1].get('FreqMode') == 13
    assert (
        dateutil.parser.parse(annotations[1]['CreatedAt']) - now
        < abs(timedelta(minutes=1))
    )


def test_post_unknown_project(odinapi_service):
    project = make_project_url(odinapi_service,  'unknown')
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a project'},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.NOT_FOUND


def test_post_bad_text(odinapi_service, project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 0000},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_no_text(odinapi_service, project):
    response = requests.post(
        project + '/annotations',
        json={},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_bad_freqmode(odinapi_service, project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'xxx', 'FreqMode': 'abcd'},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == http.client.BAD_REQUEST


def test_post_no_credentials(odinapi_service, project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a project'},
    )
    assert response.status_code == http.client.UNAUTHORIZED


def test_post_bad_credentials(odinapi_service, project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a project'},
        auth=('bob', 'password'),
    )
    assert response.status_code == http.client.UNAUTHORIZED
