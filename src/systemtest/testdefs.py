"""Definitions used by tests"""
import pytest


slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),
    reason="need --runslow option to run"
)

system = pytest.mark.skipif(
    not pytest.config.getoption("--runsystem"),
    reason="need --runsystem option to run"
)

disable = pytest.mark.skipif(
    not pytest.config.getoption("--rundisabled"),
    reason="need --rundisabled option to run"
)
