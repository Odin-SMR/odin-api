import os
from pathlib import Path
from datetime import datetime
import pytest
import numpy as np

from odinapi.views.newdonalettyERANC import run_donaletty
from odinapi.views.msis90 import Msis90


@pytest.fixture
def inputdatapath():
    p = Path(__file__)
    for p in p.parents:
        if p.name == 'src':
            p = p.parent
            break
    return p / 'data' / 'ptz-data'


@pytest.fixture(scope='session')
def outputdatapath(tmpdir_factory):
    return tmpdir_factory.mktemp('data')


@pytest.fixture
def ptz_data(inputdatapath, outputdatapath):
    latitude = 11.1
    longitude = 82.0
    scanid = 7014821387
    mjd = 57034.1
    data = run_donaletty(
        mjd,
        latitude,
        longitude,
        scanid,
        ecmwfpath=os.path.join(inputdatapath, 'ERA-Interim'),
        solardatafile=os.path.join(inputdatapath, 'Solardata2.db'),
        zptpath=outputdatapath)
    assert os.path.isfile(
        os.path.join(
            outputdatapath,
            '2015',
            '01',
            'ZPT_{}.nc'.format(scanid)
        )
    )
    return data


@pytest.mark.parametrize('parameter,index,expect', (
    ('z', 0, 75.),
    ('z', 75, 150.),
    ('p', 0, 0.02448),
    ('p', 75, 4.2824e-6),
    ('t', 0, 212.93),
    ('t', 75, 706.19),
))
def test_msis90_values(inputdatapath, parameter, index, expect):
    msis90 = Msis90(
        solardatafile=os.path.join(inputdatapath, 'Solardata2.db'))
    latitude = 11.1
    longitude = 82.0
    altitudes = np.arange(75, 151, 1)
    p, t, z = msis90.extractPTZprofilevarsolar(
        datetime(2015, 1, 12, 1), latitude, longitude, altitudes
    )
    data = {'p': p, 't': t, 'z': z}
    assert (
        data[parameter].shape == (76,)
        and data[parameter][index] == pytest.approx(expect, rel=1e-3)
    )


def test_donaletty_returns_expected_parameters(ptz_data):
    assert set(ptz_data) == set([
        'ScanID', 'Z', 'P', 'T', 'latitude', 'longitude', 'datetime'])


@pytest.mark.parametrize('parameter,expect', (
    ('ScanID', 7014821387),
    ('latitude', 11.1),
    ('longitude', 82.0),
))
def test_donaletty_returns_expected_scalars(ptz_data, parameter, expect):
    assert ptz_data[parameter] == pytest.approx(expect, rel=1e-6)


@pytest.mark.parametrize('parameter,expect', (
    ('Z', (151,)),
    ('P', (151,)),
    ('T', (151,)),
))
def test_donaletty_returns_expected_array_shapes(ptz_data, parameter, expect):
    assert ptz_data[parameter].shape == expect


@pytest.mark.parametrize('parameter,index,expect', (
    ('Z', 0, 0),
    ('Z', 75, 75.),
    ('Z', 150, 150.),
    ('P', 0, 1048.),
    ('P', 75, 0.02384),
    ('P', 150, 4.258e-6),
    ('T', 0, 297.8),
    ('T', 75, 216.0),
    ('T', 150, 672.3),
))
def test_donaletty_returns_expected_array_values(
        ptz_data, parameter, index, expect):
    assert ptz_data[parameter][index] == pytest.approx(expect, rel=1e-3)
