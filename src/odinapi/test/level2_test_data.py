"""Provide functions for inserting level2 test data to api"""
import os
import json

import requests

from odinapi.utils import encrypt_util

# Use this version when posting test data:
VERSION = 'v5'
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')
WRITE_URL = 'http://localhost:5000/rest_api/{version}/level2?d={d}'


def get_test_data(file_name='odin_result.json'):
    with open(os.path.join(TEST_DATA_DIR, file_name)) as inp:
        return json.load(inp)


def get_write_url(data, project_name):
    freq_mode = data['L2I']['FreqMode']
    scan_id = data['L2I']['ScanID']
    data = encrypt_util.encode_level2_target_parameter(
        scan_id, freq_mode, project_name)
    return WRITE_URL.format(version=VERSION, d=data)


def insert_test_data(project_name, file_name='odin_result.json'):
    data = get_test_data(file_name)
    wurl = get_write_url(data, project_name)
    r = requests.post(wurl, json=data)
    return r


def insert_failed_scan(project_name, scanid=7123991206+1, freqmode=1,
                       message=u'Error: This scan failed'):
    data_failed = {'L2I': [], 'L2': [], 'L2C': message}
    data = encrypt_util.encode_level2_target_parameter(
        scanid, freqmode, project_name)
    wurl_failed = WRITE_URL.format(version=VERSION, d=data)
    r = requests.post(wurl_failed, json=data_failed)
    return r


def delete_test_data(project_name, file_name='odin_result.json'):
    data = get_test_data(file_name)
    wurl = get_write_url(data, project_name)
    r = requests.delete(wurl, json=data)
    return r
