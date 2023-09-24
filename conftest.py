import os

from docker import from_env
import pytest
from pymongo import MongoClient

WAIT_FOR_SERVICE_TIME = 60 * 5
PAUSE_TIME = 5


def pytest_addoption(parser):
    """Adds the integrationtest option"""
    parser.addoption("--runslow", action="store_true", help="run slow tests")
    parser.addoption(
        "--no-cleanup", action="store_true", default=False, help="Don't clean up after running tests"
    )

@pytest.fixture(scope="session")
def no_cleanup(request):
    return request.config.getoption("--no-cleanup")



def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def docker_cleanup(no_cleanup):
    if no_cleanup:
        return False
    return "down -v"

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "compose.yaml")


@pytest.fixture(scope="session")
def odin_postgresql(docker_ip, docker_services):
    port = docker_services.port_for("postgresql", 5432)
    return "localhost", port


@pytest.fixture(scope="session")
def odinapi_service(docker_ip, docker_services):
    port = docker_services.port_for("odin", 80)
    url = "http://{}:{}".format(docker_ip, port)
    yield url


@pytest.fixture(scope="session")
def docker_mongo():
    client = from_env()
    container = client.containers.run(
        "mongo:6", detach=True, ports={"27017/tcp": ("127.0.0.1", 27017)}
    )
    yield MongoClient()
    container.stop()  # type: ignore
    container.remove()  # type: ignore
