import os

import numpy as np
import pytest
import scipy.io as sio

from odinapi.views import read_apriori


DATADIR = os.path.join(
    os.path.dirname(__file__),
    os.path.pardir,
    'fixtures',
)


@pytest.fixture(scope='module')
def co_mipas():
    return sio.loadmat(os.path.join(DATADIR, 'apriori_CO_mipas.mat'))


@pytest.fixture(scope='module')
def co2():
    return sio.loadmat(os.path.join(DATADIR, 'apriori_CO2.mat'))


def test_returns_empty_altitude_for_co2(co2):
    assert read_apriori.get_datadict(co2, 'Bdx')['altitude'].size == 0


def test_returns_altitude_for_mipas(co_mipas):
    altitudes = (
        read_apriori.get_datadict(co_mipas, 'MIPAS')['altitude']
        .ravel()[:32].tolist()
    )
    assert altitudes == list(range(18000, 50000, 1000))


def test_returns_expected_data_keys():
    species = 'CO2'
    day_of_year = 14
    latitude = 35
    data = read_apriori.get_apriori(
        species, day_of_year, latitude, datadir=DATADIR,
    )
    assert set(data.keys()) == {
        'pressure', 'vmr', 'species', 'latitude', 'path',
        'altitude',
    }


@pytest.mark.parametrize("key,expect", (
    ('species', 'CO2'),
    ('latitude', 35),
    ('path', os.path.join(DATADIR, 'apriori_CO2.mat')),
))
def test_returns_expected_data(key, expect):
    species = 'CO2'
    day_of_year = 14
    latitude = 35
    data = read_apriori.get_apriori(
        species, day_of_year, latitude, datadir=DATADIR,
    )
    assert data[key] == expect


def test_returns_expected_pressure():
    species = 'CO2'
    day_of_year = 14
    latitude = 35
    data = read_apriori.get_apriori(
        species, day_of_year, latitude, datadir=DATADIR,
    )
    np.testing.assert_allclose(data['pressure'][:10].tolist(), [
        100000., 93057.204093, 86596.432336, 80584.218776, 74989.420933,
        69783.058486, 64938.163158, 60429.639024, 56234.132519, 52329.911468,
    ])


def test_returns_expected_vmr():
    species = 'CO2'
    day_of_year = 14
    latitude = 35
    data = read_apriori.get_apriori(
        species, day_of_year, latitude, datadir=DATADIR,
    )
    np.testing.assert_allclose(
        data['vmr'][:20].tolist(),
        [0.000365] * 16 + [0.000364, 0.000364, 0.000363, 0.000363],
        atol=0.0000005,
    )


@pytest.mark.parametrize('lat,expect', (
    (90, 85),
    (-90, -85),
    (3, 3),
))
def test_clip_lats_outside_range(lat, expect):
    species = 'CO2'
    day_of_year = 14
    data = read_apriori.get_apriori(
        species, day_of_year, lat, datadir=DATADIR,
    )
    assert data['latitude'] == expect


def test_using_alternative_source():
    species = 'CO'
    day_of_year = 14
    latitude = 35
    data = read_apriori.get_apriori(
        species, day_of_year, latitude, source='mipas', datadir=DATADIR,
    )
    assert (
        data['path']
        == os.path.join(os.path.join(DATADIR, 'apriori_CO_mipas.mat'))
    )
