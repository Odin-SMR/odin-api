# pylint: skip-file
"""Unitttests"""

from time import sleep, time
from subprocess import check_output, Popen
import pytest
import requests


def pytest_addoption(parser):
    """Adds the integrationtest option"""
    parser.addoption(
        "--runslow", action="store_true", help="run slow tests")
    parser.addoption(
        "--runsystem", action="store_true", help="run system tests")
    parser.addoption(
        "--rundisabled", action="store_true", help="run disabled tests")


@pytest.yield_fixture(scope='session')
def dockercompose():
    """Set up the full system"""
    root_path = check_output(['git', 'rev-parse', '--show-toplevel'])
    build = Popen(
        [
            'docker-compose',
            'build',
        ],
        cwd=root_path.strip()
    )
    build.wait()

    pull = Popen(
        [
            'docker-compose',
            'pull',
        ],
        cwd=root_path.strip()
    )
    pull.wait()

    system = Popen(
        [
            'docker-compose',
            'up',
            '--no-recreate',
            '--abort-on-container-exit',
            '--remove-orphans',
        ],
        cwd=root_path.strip()
    )
    # Wait for webapi and database
    max_wait = 60*5
    start_wait = time()
    while True:
        exit_code = system.poll()
        assert exit_code is None, 'docker-compose exited with code {}'.format(
            exit_code)
        try:
            r = requests.get(
                'http://localhost:5000/rest_api/v4/freqmode_info/2010-10-01/',
                timeout=1)
            if r.status_code == 200:
                break
        except:
            sleep(1)
        if time() > start_wait + max_wait:
            assert False, 'Could not access webapi after %d seconds' % max_wait

    yield system.pid

    system.terminate()
    system.wait()
