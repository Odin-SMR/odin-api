import sys
import os
import requests

MY_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MY_PATH + '/../../../src')


def test_get_l2_data(odinapi_service):
    """Read a known file from the testdataset."""
    r = requests.get(
        "{}/level2_download/project/l2_test.txt".format(odinapi_service),
    )
    assert r.text == "1234\n"
