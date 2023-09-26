"""Provide functions for inserting level2 test data to api"""
from collections import namedtuple
from copy import deepcopy
import simplejson
import json
import os
import re

import requests
from odinapi.custom_json import CustomJSONProvider

from odinapi.utils import encrypt_util

UrlInfo = namedtuple("UrlInfo", "url,freq_mode,scan_id,data")
# Use this version when posting test data:
VERSION = "v5"
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "testdata")
WRITE_URL = "{host}/rest_api/{version}/level2?d={d}"


def get_test_data(file_name="odin_result.json"):
    with open(os.path.join(TEST_DATA_DIR, file_name)) as inp:
        return simplejson.load(inp, allow_nan=True)


def get_write_url(data, project_name, host):
    freq_mode = data["L2I"]["FreqMode"]
    scan_id = data["L2I"]["ScanID"]
    encdata = encrypt_util.encode_level2_target_parameter(
        scan_id, freq_mode, project_name
    )
    return UrlInfo(
        WRITE_URL.format(host=host, version=VERSION, d=encdata),
        freq_mode,
        scan_id,
        data=lambda: deepcopy(data),
    )


def insert_test_data(project_name, host, file_name="odin_result.json"):
    data = get_test_data(file_name)
    urlinfo = get_write_url(data, project_name, host)
    r = requests.post(
        urlinfo.url,
        data=simplejson.dumps(data, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    return r, urlinfo


def insert_inf_test_data(
    project_name: str,
    host: str,
    file_name: str = "odin_result.json",
):
    with open(os.path.join(TEST_DATA_DIR, file_name)) as inp:
        text = re.sub(r'"MinLmFactor": 1,', '"MinLmFactor": NaN,', inp.read())
    data = simplejson.loads(text, allow_nan=True)
    urlinfo = get_write_url(data, project_name, host)
    r = requests.post(
        urlinfo.url,
        data=simplejson.dumps(data, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    return r, urlinfo


def insert_lot_of_test_data(project_name, host, file_name="odin_result.json"):
    data = get_test_data(file_name)
    urlinfos = []
    for _ in range(30):
        for product in data["L2"]:
            product["ScanID"] += 1
        data["L2I"]["ScanID"] += 1
        urlinfo = get_write_url(data, project_name, host)
        requests.post(
            urlinfo.url,
            data=simplejson.dumps(data, allow_nan=True),
            headers={"Content-Type": "application/json"},
        )
        urlinfos.append(urlinfo)
    return urlinfos


def insert_failed_scan(
    project_name,
    host,
    scanid=7123991206 + 1,
    freqmode=1,
    message="Error: This scan failed",
):
    data_failed = {"L2I": [], "L2": [], "L2C": message}
    data = encrypt_util.encode_level2_target_parameter(scanid, freqmode, project_name)
    wurl_failed = WRITE_URL.format(host=host, version=VERSION, d=data)
    r = requests.post(
        wurl_failed,
        data=simplejson.dumps(data_failed, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    return r, UrlInfo(
        wurl_failed,
        freqmode,
        scanid,
        data=lambda: deepcopy(data_failed),
    )


def delete_test_data(project_name, host, file_name="odin_result.json"):
    data = get_test_data(file_name)
    urlinfo = get_write_url(data, project_name, host)
    r = requests.delete(
        urlinfo.url,
        data=simplejson.dumps(data, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    return r, urlinfo
