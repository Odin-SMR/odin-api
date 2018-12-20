"""Definitions used by tests"""
import pytest

system = pytest.mark.skipif(  # pylint: disable=invalid-name
    not pytest.config.getoption("--runsystem"),  # pylint: disable=no-member
    reason="need --runsystem option to run"
)
