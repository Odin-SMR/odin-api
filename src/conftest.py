import os
from pathlib import Path
import socket
import subprocess
from time import sleep
from flask import Flask

import pytest
from docker import from_env  # type: ignore
from docker.models.containers import Container  # type: ignore
import requests
from xprocess import ProcessStarter  # type: ignore

from odinapi.api import create_app
from odinapi.odin_config import LocalConfig, SeleniumConfig, TestConfig
from odinapi.odin_config import LocalConfig, TestConfig

WAIT_FOR_SERVICE_TIME = 60 * 5
PAUSE_TIME = 5


@pytest.fixture
def db_app():
    config = TestConfig()
    app = create_app(config)
    yield app


@pytest.fixture(scope="session")
def selenium_app(xprocess):
    p = subprocess.Popen(["flask", "--app", "odinapi.api:run", "run"])
    for _ in range(20):
        try:
            requests.get("http://127.0.0.1:5000")
            break
        except Exception:
            sleep(0.5)

    yield "http://127.0.0.1:5000"
    p.terminate()


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
