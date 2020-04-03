import os

from pg import DB, InternalError
import pytest
from pymongo import MongoClient
import requests
from requests.exceptions import RequestException

WAIT_FOR_SERVICE_TIME = 60 * 5
PAUSE_TIME = 5


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
        str(pytestconfig.rootdir),
        'docker-compose.systemtest.yml',
    )


@pytest.fixture(scope='session')
def odin_postgresql(docker_ip, docker_services):
    port = docker_services.port_for('postgresql', 5432)
    docker_services.wait_until_responsive(
        timeout=WAIT_FOR_SERVICE_TIME,
        pause=PAUSE_TIME,
        check=lambda: odinapi_postgresq_responsive('localhost', port),
    )
    return 'localhost', port


@pytest.fixture(scope='session')
def odinapi_service(docker_ip, docker_services, docker_compose_file):
    print(docker_compose_file)
    port = docker_services.port_for('odin', 80)
    url = "http://{}:{}".format(docker_ip, port)
    docker_services.wait_until_responsive(
        timeout=WAIT_FOR_SERVICE_TIME,
        pause=PAUSE_TIME,
        check=lambda: odinapi_is_responsive(url),
    )
    yield url
    logs = docker_services._docker_compose.execute('logs webapi')
    for line in logs.decode().split('\n'):
        print(line)


@pytest.fixture(scope='session')
def docker_mongo(docker_db):
    return MongoClient()
