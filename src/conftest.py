import subprocess
from time import sleep

import pytest
import requests
from flask import Flask

from odinapi.api import create_app
from odinapi.odin_config import TestConfig

WAIT_FOR_SERVICE_TIME = 60 * 5
PAUSE_TIME = 5


@pytest.fixture
def db_app():
    config = TestConfig()
    app = create_app(config)
    yield app


@pytest.fixture(scope="session")
def selenium_app():
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
