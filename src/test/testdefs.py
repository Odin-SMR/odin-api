"""Definitions used by tests"""
import pytest


slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),
    reason="need --runslow option to run"
)

disable = pytest.mark.skipif(
    not pytest.config.getoption("--rundisabled"),
    reason="need --rundisabled option to run"
)
