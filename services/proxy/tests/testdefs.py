"""Definitions used by tests"""
import pytest

system = pytest.mark.skipif(
    not pytest.config.getoption("--runsystem"),
    reason="need --runsystem option to run"
)
