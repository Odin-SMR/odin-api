"""Provide functions for inserting level2 test data to api"""

import http.client
import os
import re
from collections import namedtuple
from copy import deepcopy

from flask import current_app
import pytest
import json

from odinapi.utils import encrypt_util

pytestmark = pytest.mark.system
UrlInfo = namedtuple("UrlInfo", "url,freq_mode,scan_id,data")
# Use this version when posting test data:
VERSION = "v5"
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "testdata")
WRITE_URL = "http://localhost/rest_api/{version}/level2?d={d}"


def get_test_data(file_name="odin_result.json"):
    with open(os.path.join(TEST_DATA_DIR, file_name)) as inp:
        return json.load(inp)


def get_write_url(data, project_name):
    freq_mode = data["L2I"]["FreqMode"]
    scan_id = data["L2I"]["ScanID"]
    encdata = encrypt_util.encode_level2_target_parameter(
        scan_id, freq_mode, project_name
    )
    return UrlInfo(
        WRITE_URL.format(version=VERSION, d=encdata),
        freq_mode,
        scan_id,
        data=lambda: deepcopy(data),
    )


def insert_test_data(project_name, file_name="odin_result.json"):
    client = current_app.test_client()
    data = get_test_data(file_name)
    urlinfo = get_write_url(
        data,
        project_name,
    )
    r = client.post(
        urlinfo.url,
        json=data,
    )
    assert r.status_code == http.client.CREATED, f"insert test-data failed: {__name__}"
    return r, urlinfo


def insert_inf_test_data(
    project_name: str,
    file_name: str = "odin_result.json",
):
    with open(os.path.join(TEST_DATA_DIR, file_name)) as inp:
        text = re.sub(r'"MinLmFactor": 1,', '"MinLmFactor": NaN,', inp.read())
    data = json.loads(text)
    urlinfo = get_write_url(
        data,
        project_name,
    )
    requests = current_app.test_client()
    r = requests.post(
        urlinfo.url,
        json=data,
    )
    assert (
        r.status_code == http.client.CREATED
    ), f"insert test-data with inf failed: {__name__}"
    return r, urlinfo


def insert_lot_of_test_data(project_name, file_name="odin_result.json"):
    requests = current_app.test_client()
    data = get_test_data(file_name)
    urlinfos = []
    for _ in range(30):
        for product in data["L2"]:
            product["ScanID"] += 1
        data["L2I"]["ScanID"] += 1
        urlinfo = get_write_url(
            data,
            project_name,
        )
        r = requests.post(
            urlinfo.url,
            json=data,
        )
        assert (
            r.status_code == http.client.CREATED
        ), f"insert while inserting a lot of testada failed: {__name__}"
        urlinfos.append(urlinfo)
    return urlinfos


def insert_failed_scan(
    project_name,
    scanid=7123991206 + 1,
    freqmode=1,
    message="Error: This scan failed",
):
    requests = current_app.test_client()
    data_failed = {"L2I": [], "L2": [], "L2C": message}
    data = encrypt_util.encode_level2_target_parameter(scanid, freqmode, project_name)
    wurl_failed = WRITE_URL.format(version=VERSION, d=data)
    requests = current_app.test_client()
    r = requests.post(
        wurl_failed,
        json=data_failed,
    )
    assert (
        r.status_code == http.client.CREATED
    ), f"insert failed scan failed: {__name__}"
    return r, UrlInfo(
        wurl_failed,
        freqmode,
        scanid,
        data=lambda: deepcopy(data_failed),
    )


def delete_test_data(project_name, file_name="odin_result.json"):
    requests = current_app.test_client()
    data = get_test_data(file_name)
    urlinfo = get_write_url(
        data,
        project_name,
    )
    r = requests.delete(
        urlinfo.url,
        json=data,
    )
    assert (
        r.status_code == http.client.NO_CONTENT
    ), f"deleting testdata failed: {__name__}"
    return r, urlinfo
