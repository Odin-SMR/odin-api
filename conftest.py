from __future__ import print_function

from time import sleep, time
from subprocess import check_output, Popen
import sys

import pytest
import requests

__RESTARTDOCKER = True


def pytest_addoption(parser):
    """Adds the integrationtest option"""
    parser.addoption(
        "--runslow", action="store_true", help="run slow tests")
    parser.addoption(
        "--no-system-restart", action="store_true",
        help="do not restart the system")


def pytest_collection_modifyitems(config, items):
    if not config.getoption('--runslow'):
        skip_slow = pytest.mark.skip(reason='need --runslow option to run')
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_configure(config):
    global __RESTARTDOCKER
    if config.getoption('--no-system-restart'):
        __RESTARTDOCKER = False


def call_docker_compose(cmd, root_path, log, args=None, wait=True):
    cmd = ['docker-compose', cmd] + (args or [])
    popen = Popen(cmd, cwd=root_path, stdout=log)
    if wait:
        popen.wait()
    return popen


@pytest.fixture(scope='session')
def root_path():
    return check_output(['git', 'rev-parse', '--show-toplevel']).strip()


@pytest.yield_fixture(scope='session')
def dockercompose(tmpdir_factory, root_path):
    """Set up the full system"""
    logpath = tmpdir_factory.mktemp('docker').join('docker-compose.log')
    log = logpath.open('w')

    if __RESTARTDOCKER:
        print(
            'docker-compose logs available at {}'.format(logpath),
            file=sys.stderr
        )
        call_docker_compose('stop', root_path, log)
        call_docker_compose('pull', root_path, log)
        call_docker_compose('build', root_path, log)
        call_docker_compose('rm', root_path, log, args=['--force'])

    args = ['--abort-on-container-exit', '--remove-orphans']
    system = call_docker_compose('up', root_path, log, args=args, wait=False)

    # Wait for webapi and database
    max_wait = 60*5
    start_wait = time()
    while True:
        exit_code = system.poll()
        if exit_code is not None:
            call_docker_compose('stop', root_path, log)
            assert False, 'docker-compose exit code {}'.format(exit_code)
        try:
            r = requests.get(
                'http://localhost:5000/rest_api/v4/freqmode_info/2010-10-01/',
                timeout=5)
            if r.status_code == 200:
                break
        except:  # noqa
            sleep(1)
        if time() > start_wait + max_wait:
            call_docker_compose('stop', root_path, log)
            if system.poll() is None:
                system.kill()
                system.wait()
            assert False, 'Could not access webapi after %d seconds' % max_wait

    yield system.pid

    if __RESTARTDOCKER:
        call_docker_compose('stop', root_path, log)
        if system.poll() is None:
            system.kill()
            system.wait()
