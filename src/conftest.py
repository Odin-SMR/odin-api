import os
from time import sleep

import pytest
from docker import from_env  # type: ignore
from docker.models.containers import Container  # type: ignore
from pymongo import MongoClient

from odinapi.api import Config, create_app

WAIT_FOR_SERVICE_TIME = 60 * 5
PAUSE_TIME = 5


def pytest_addoption(parser):
    """Adds the integrationtest option"""
    parser.addoption("--runslow", action="store_true", help="run slow tests")
    parser.addoption(
        "--no-cleanup",
        action="store_true",
        default=False,
        help="Don't clean up after running tests",
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
    port = "27017/tcp"
    container = client.containers.run("mongo:6", detach=True, ports={port: None})
    if type(container) != Container:
        raise RuntimeError("Error while starting container")
    while container.status != "running":
        sleep(1)
        container.reload()
    exposed_port = int(container.ports[port][0]["HostPort"])
    yield MongoClient(port=exposed_port)
    container.stop()
    container.remove()


@pytest.fixture(scope="session")
def docker_postgresql():
    client = from_env()
    port = "5432/tcp"
    container = client.containers.run(
        "odinsmr/odin_db", detach=True, ports={port: None}
    )
    if type(container) != Container:
        raise RuntimeError("Error while starting container")
    while container.status != "running":
        sleep(1)
        container.reload()
    exposed_port = container.ports[port][0]["HostPort"]
    exec_code, _ = container.exec_run(["pg_isready", "-t1"])
    while exec_code != 0:
        sleep(1)
        exec_code, _ = container.exec_run(["pg_isready", "-t1"])
    yield f"postgresql://odinop@localhost:{exposed_port}/odin"
    container.stop()
    print(container.logs())
    container.remove()


@pytest.fixture
def db_context(docker_postgresql):
    class TestConfig(Config):
        SQLALCHEMY_DATABASE_URI = docker_postgresql

    app = create_app(TestConfig)
    with app.app_context():
        yield


@pytest.fixture
def db_app(docker_postgresql):
    class TestConfig(Config):
        SQLALCHEMY_DATABASE_URI = docker_postgresql

    app = create_app(TestConfig)
    yield app