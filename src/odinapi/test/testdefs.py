"""Definitions used by tests"""
import os

import pytest


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')


slow = pytest.mark.skipif(  # pylint: disable=invalid-name
    not pytest.config.getoption("--runslow"),  # pylint: disable=no-member
    reason="need --runslow option to run"
)

system = pytest.mark.skipif(  # pylint: disable=invalid-name
    not pytest.config.getoption("--runsystem"),  # pylint: disable=no-member
    reason="need --runsystem option to run"
)

disable = pytest.mark.skipif(  # pylint: disable=invalid-name
    not pytest.config.getoption("--rundisabled"),  # pylint: disable=no-member
    reason="need --rundisabled option to run"
)
