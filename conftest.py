from __future__ import print_function
import os

from pg import DB, InternalError
import pytest
import requests
from requests.exceptions import RequestException

WAIT_FOR_SERVICE_TIME = 60 * 5
PAUSE_TIME = 0.1


def pytest_addoption(parser):
    """Adds the integrationtest option"""
    parser.addoption(
        "--runslow", action="store_true", help="run slow tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption('--runslow'):
        skip_slow = pytest.mark.skip(reason='need --runslow option to run')
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def odinapi_is_responsive(baseurl):
    try:
        r = requests.get(
            '{}/rest_api/v4/freqmode_info/2010-10-01/'.format(baseurl),
        )
        r.raise_for_status()
    except RequestException:
        return False
    return True


class DatabaseConnector(DB):
    def __init__(self, host, port):
        DB.__init__(self, dbname='odin', user='odinop', host=host, port=port)


def odinapi_postgresq_responsive(host, port):
    try:
        DatabaseConnector(host, port)
    except InternalError:
        return False
    return True


@pytest.fixture(scope='session')
def docker_compose_file(pytestconfig):
    return os.path.join(
        os.path.dirname(__file__),
        'docker-compose.systemtest.yml',
    )


@pytest.fixture(scope='session')
def odin_postgresql(docker_ip, docker_services):
    port = docker_services.port_for('postgresql', 5432)
    docker_services.wait_until_responsive(
        timeout=WAIT_FOR_SERVICE_TIME,
        pause=PAUSE_TIME,
        check=lambda: odinapi_postgresq_responsive(docker_ip, port),
    )
    return docker_ip, port


@pytest.fixture(scope='session')
def odinapi_service(docker_ip, docker_services):
    port = docker_services.port_for('odin', 80)
    url = "http://localhost:{}".format(port)
    docker_services.wait_until_responsive(
        timeout=WAIT_FOR_SERVICE_TIME,
        pause=PAUSE_TIME,
        check=lambda: odinapi_is_responsive(url),
    )
    return url
