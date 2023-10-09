import os
from pathlib import Path
import socket
from time import sleep
from flask import Flask

import pytest
from docker import from_env  # type: ignore
from docker.models.containers import Container  # type: ignore
from xprocess import ProcessStarter  # type: ignore

from odinapi.api import create_app
from odinapi.odin_config import LocalConfig, TestConfig

WAIT_FOR_SERVICE_TIME = 60 * 5
PAUSE_TIME = 5


@pytest.fixture(scope="session")
def docker_mongo():
    client = from_env()
    port = "27017/tcp"
    container = client.containers.run("mongo", detach=True, ports={port: None})
    if type(container) != Container:
        raise RuntimeError("Error while starting container")
    while container.status != "running":
        sleep(1)
        container.reload()
    exposed_port = int(container.ports[port][0]["HostPort"])
    yield f"mongodb://localhost:{exposed_port}/"
    container.stop()
    container.remove()


@pytest.fixture(scope="session")
def docker_postgresql():
    client = from_env()
    port = "5432/tcp"
    container = client.containers.run(
        "odinsmr/odin_db",
        detach=True,
        ports={port: None},
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
    yield f"postgresql+psycopg://odinop@localhost:{exposed_port}/odin"
    container.stop()
    container.remove()


@pytest.fixture
def db_app(docker_postgresql, docker_mongo):
    config = TestConfig()
    config.SQLALCHEMY_DATABASE_URI = docker_postgresql
    config.MONGO_DATABASE_URI = docker_mongo
    app = create_app(config)
    yield app


@pytest.fixture(scope="session")
def selenium_app(docker_postgresql, docker_mongo, xprocess):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()

    class Starter(ProcessStarter):
        pattern = ".*Restarting with stat.*"  # type: ignore
        args = ["python3", "-m", "odinapi.run", "--selenium"]  # type: ignore
        env = dict(
            PYTHONPATH=f"{Path(__file__).parent}",
            PYTHONUNBUFFERED="1",
            PATH=os.environ.get("PATH"),
            SQLALCHEMY_DATABASE_URI=docker_postgresql,
            MONGO_DATABASE_URI=docker_mongo,
            FLASK_PORT=str(port),
        )
        timeout = 5

    logfile = xprocess.ensure("flask", Starter)
    yield f"http://127.0.0.1:{port}"
    print(logfile)
    xprocess.getinfo("flask").terminate()


@pytest.fixture
def db_context(db_app):
    with db_app.app_context():
        yield


@pytest.fixture
def test_client(db_app: Flask):
    with db_app.app_context():
        yield db_app.test_client()


@pytest.fixture
def app_context():
    config = TestConfig()
    app = create_app(config)
    with app.app_context():
        yield
