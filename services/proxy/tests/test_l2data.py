# pylint: skip-file
import sys
import os
import pytest
import requests
MY_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MY_PATH + '/../../../src')
from odinapi.test.testdefs import system  # noqa


@system
@pytest.mark.usefixtures("dockercompose")
def test_get_l2_data():
    """Read a known file from the testdataset."""
    r = requests.get(
        "http://localhost:5000/level2_download/project/l2_test.txt")
    assert r.text == "1234\n"