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


@pytest.mark.parametrize("x,expect", (
    (-79, (0, 1, 0.95, 0.05)),
    (-70, (0, 1, 0.5, 0.5)),
    (-68, (0, 1, 0.4, 0.6)),
    (-60, (0, 1, 0.0, 1.0)),
    (-50, (1, 2, 0.5, 0.5)),
    (60, (3, 4, 0.0, 1.0)),
    (79, (4, 5, 0.05, 0.95)),
))
def test_get_interpolation_weights(x, expect):
    xs = np.array([-80, -60, -40, 40, 60, 80])
    id1, id2, w1, w2 = read_apriori.get_interpolation_weights(
        xs, x)
    np.testing.assert_allclose((id1, id2, w1, w2), expect, atol=1e-6)


@pytest.mark.parametrize("doy,expect", (
    (0, (0, 5, 0.5, 0.5)),  # equal weights to id1 and id2
    (3, (0, 5, 0.8, 0.2)),
    (5, (0, 5, 1.0, 0.0)),
    (360, (0, 5, 0.0, 1.0)),
    (362, (0, 5, 0.2, 0.8)),
    (365, (0, 5, 0.5, 0.5)),  # equal weights to id1 and id2
    (366, (0, 5, 0.5, 0.5)),  # doy 366 gives same result as doy 365
))
def test_get_interpolation_weights_for_doy(doy, expect):
    doys = np.array([5, 10, 15, 350, 355, 360])
    id1, id2, w1, w2 = read_apriori.get_interpolation_weights_for_doy(
        doys, doy)
    np.testing.assert_allclose((id1, id2, w1, w2), expect, atol=1e-6)


@pytest.mark.parametrize("lat,expect", (
    (-90, (0, 5, 1.0, 0.0)),  # all weight to id1
    (-80, (0, 5, 1.0, 0.0)),
    (-70, (0, 1, 0.5, 0.5)),
    (-68, (0, 1, 0.4, 0.6)),
    (-60, (0, 1, 0.0, 1.0)),
    (-50, (1, 2, 0.5, 0.5)),
    (60, (3, 4, 0.0, 1.0)),
    (80, (0, 5, 0.0, 1.0)),
    (90, (0, 5, 0.0, 1.0)),  # all weight to id
))
def test_get_interpolation_weights_for_lat(lat, expect):
    lats = np.array([-80, -60, -40, 40, 60, 80])
    id1, id2, w1, w2 = read_apriori.get_interpolation_weights_for_lat(
        lats, lat)
    np.testing.assert_allclose((id1, id2, w1, w2), expect, atol=1e-6)


@pytest.mark.parametrize("lat,expect", (
    (-85, 1),
    (-80, 1),
    (-40, 1.5),
    (80, 3),
))
def test_get_vmr_interpolated_for_lat(lat, expect):
    vmrs = np.zeros((1, 3))
    vmrs[0, 0] = 1.
    vmrs[0, 1] = 2.
    vmrs[0, 2] = 3.
    lats = np.array([-80, 0, 80])
    vmr = read_apriori.get_vmr_interpolated_for_lat(
        vmrs, lats, lat)
    assert vmr == expect


@pytest.mark.parametrize("doy,expect", (
    (1, 2.5),
    (15, 1),
    (30, 1.5),
))
def test_get_vmr_interpolated_for_doy(doy, expect):
    vmrs = np.zeros((1, 1, 1, 3))
    vmrs[0, 0, 0, 0] = 1.
    vmrs[0, 0, 0, 1] = 2.
    vmrs[0, 0, 0, 2] = 4.
    doys = np.array([15, 45, 352])
    vmr = read_apriori.get_vmr_interpolated_for_doy(
        vmrs, doys, doy)
    assert vmr.item() == expect


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


@pytest.mark.parametrize("species,doy,latitude,source,expect", (
    ('CO2', 1., -90., None, 0.0003626),
    ('CO2', 1., 35., None, 0.0003626),
    ('CO2', 15., 35., None, 0.0003626),
    ('CO2', 180., 35., None, 0.0003626),
    ('CO2', 350., 35., None, 0.0003626),
    ('CO2', 365., 35., None, 0.0003626),
    ('CO2', 365., 80., None, 0.0003626),
    ('CO2', 365., 90., None, 0.0003626),
    ('CO', 1., 80., 'mipas', 0.34654013),
    ('CO', 10., 80., 'mipas', 0.3749516),
    ('CO', 30., 80., 'mipas', 0.2280777),
    ('CO', 335., 80., 'mipas', 0.1782076),
    ('CO', 355., 80., 'mipas', 0.3118149),
    ('CO', 365., 80., 'mipas', 0.3433833),
))
def test_get_apriori_co2_vmr_does_not_vary(
    species, doy, latitude, source, expect
):
    # CO is constant for a given altitude in the used apriori data.
    # Check that returned data is constant for CO, but not constant
    # for all species.
    data = read_apriori.get_apriori(
        species, doy, latitude, source=source, datadir=DATADIR,
    )
    assert data['vmr'][20] == pytest.approx(expect, abs=1e-7)


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
