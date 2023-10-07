import pytest

from odinapi.views.newdonalettyERANC import run_donaletty


@pytest.fixture
def ptz_data(app_context):
    latitude = 11.1
    longitude = 82.0
    scanid = 7014821387
    mjd = 57034.1
    data = run_donaletty(
        mjd,
        latitude,
        longitude,
        scanid,
    )
    assert data
    return data


def test_donaletty_returns_expected_parameters(ptz_data):
    assert set(ptz_data) == set(
        ["ScanID", "Z", "P", "T", "latitude", "longitude", "mjd"]
    )


@pytest.mark.parametrize(
    "parameter,expect",
    (
        ("ScanID", 7014821387),
        ("latitude", 11.66165),
        ("longitude", 82.395362),
    ),
)
def test_donaletty_returns_expected_scalars(ptz_data, parameter, expect):
    assert ptz_data[parameter] == pytest.approx(expect, rel=1e-6)


@pytest.mark.parametrize(
    "parameter,expect",
    (
        ("Z", (151,)),
        ("P", (151,)),
        ("T", (151,)),
    ),
)
def test_donaletty_returns_expected_array_shapes(
    ptz_data, parameter, expect
):
    assert ptz_data[parameter].shape == expect


@pytest.mark.parametrize(
    "parameter,index,expect",
    (
        ("Z", 0, 0),
        ("Z", 75, 75.0),
        ("Z", 150, 150.0),
        ("P", 0, 1048.0),
        ("P", 75, 0.02222),
        ("P", 150, 4.172e-6),
        ("T", 0, 297.4),
        ("T", 75, 208.7),
        ("T", 150, 731.6),
    ),
)
def test_donaletty_returns_expected_array_values(ptz_data, parameter, index, expect):
    assert ptz_data[parameter][index] == pytest.approx(expect, rel=1e-3)
