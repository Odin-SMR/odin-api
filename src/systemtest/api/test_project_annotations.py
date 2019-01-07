from datetime import datetime, timedelta
import httplib
import uuid

import dateutil.parser
from dateutil.tz import tzutc
import pytest
import requests

from ..level2_test_data import WRITE_URL, VERSION, get_test_data
from odinapi.utils import encrypt_util


def make_project_url(project):
    return (
        'http://localhost:5000/rest_api/v5/level2/{}'
        .format(project)
    )


@pytest.fixture
def project():
    data = get_test_data()
    project = str(uuid.uuid1())
    freq_mode = data['L2I']['FreqMode']
    scan_id = data['L2I']['ScanID']
    payload = encrypt_util.encode_level2_target_parameter(
        scan_id, freq_mode, project
    )
    wurl = WRITE_URL.format(version=VERSION, d=payload)
    requests.post(wurl, json=data).raise_for_status()
    return make_project_url(project)


@pytest.mark.usefixtures('dockercompose')
def test_get_empty_annotations(project):
    response = requests.get(project + '/annotations')
    assert response.status_code == httplib.OK
    assert response.json()['Data'] == []


@pytest.mark.usefixtures('dockercompose')
def test_get_annotations_unknown_project():
    project = make_project_url('unknown')
    response = requests.get(project + '/annotations')
    assert response.status_code == httplib.NOT_FOUND


@pytest.mark.usefixtures('dockercompose')
def test_post(project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a freqmode', 'FreqMode': 13},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    now = datetime.utcnow().replace(tzinfo=tzutc())
    assert response.status_code == httplib.CREATED
    response = requests.get(project + '/annotations')
    assert response.status_code == httplib.OK
    assert len(response.json()['Data']) == 1
    annotation = response.json()['Data'][0]
    assert annotation['Text'] == 'This is a freqmode'
    assert annotation['FreqMode'] == 13
    assert (
        dateutil.parser.parse(annotation['CreatedAt']) - now
        < abs(timedelta(minutes=1))
    )


@pytest.mark.usefixtures('dockercompose')
def test_post_multiple(project):
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
    assert response.status_code == httplib.OK
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


@pytest.mark.usefixtures('dockercompose')
def test_post_unknown_project():
    project = make_project_url('unknown')
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a project'},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == httplib.NOT_FOUND


@pytest.mark.usefixtures('dockercompose')
def test_post_bad_text(project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 0000},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == httplib.BAD_REQUEST


@pytest.mark.usefixtures('dockercompose')
def test_post_no_text(project):
    response = requests.post(
        project + '/annotations',
        json={},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == httplib.BAD_REQUEST


@pytest.mark.usefixtures('dockercompose')
def test_post_bad_freqmode(project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'xxx', 'FreqMode': 'abcd'},
        auth=('bob', encrypt_util.SECRET_KEY),
    )
    assert response.status_code == httplib.BAD_REQUEST


@pytest.mark.usefixtures('dockercompose')
def test_post_no_credentials(project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a project'},
    )
    assert response.status_code == httplib.UNAUTHORIZED


@pytest.mark.usefixtures('dockercompose')
def test_post_bad_credentials(project):
    response = requests.post(
        project + '/annotations',
        json={'Text': 'This is a project'},
        auth=('bob', 'password'),
    )
    assert response.status_code == httplib.UNAUTHORIZED
