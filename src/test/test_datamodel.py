import pytest  # type: ignore
import datetime as dt

from odinapi.utils import datamodel


@pytest.fixture(scope="session")
def l2anc():
    return {
        "LST": 0.,
        "Orbit": 1,
        "SZA1D": 2.,
        "SZA": [3., 4.],
        "Theta": [5., 6.],
    }


@pytest.fixture(scope="session")
def l2i():
    return {
        "GenerationTime": "2000-01-02T03:04:05Z",
        "Residual": 7.,
        "MinLmFactor": 8.,
        "FreqMode": 9,
    }


@pytest.fixture(scope="session")
def l2():
    return {
        "InvMode": "10",
        "ScanID": 11,
        "MJD": 12.,
        "Lat1D": 13.,
        "Lon1D": 14.,
        "Quality": 15,
        "Altitude": [16., 17.],
        "Pressure": [18., 19.],
        "Latitude": [20., 21.],
        "Longitude": [22., 23.],
        "Temperature": [24., 25.],
        "ErrorTotal": [26., 27.],
        "ErrorNoise": [28., 29.],
        "MeasResponse": [30., 31.],
        "Apriori": [32., 33.],
        "VMR": [34., 35.],
        "AVK": [[36., 37.], [38., 39.]],
    }


def test_to_l2anc_works(l2anc):
    assert datamodel.to_l2anc(l2anc) == datamodel.L2anc(
        LST=0.,
        Orbit=1,
        SZA1D=2.,
        SZA=[3., 4.],
        Theta=[5., 6.],
    )


def test_to_l2i_works(l2i):
    assert datamodel.to_l2i(l2i) == datamodel.L2i(
        GenerationTime=dt.datetime(2000, 1, 2, 3, 4, 5),
        Residual=7.,
        MinLmFactor=8.,
        FreqMode=9
    )


def test_to_l2_works(l2):
    assert datamodel.to_l2(l2) == datamodel.L2(
        InvMode="10",
        ScanID=11,
        Time=dt.datetime(1858, 11, 29, 0, 0),
        Lat1D=13.,
        Lon1D=14.,
        Quality=15,
        Altitude=[16., 17.],
        Pressure=[18., 19.],
        Latitude=[20., 21.],
        Longitude=[22., 23.],
        Temperature=[24., 25.],
        ErrorTotal=[26., 27.],
        ErrorNoise=[28., 29.],
        MeasResponse=[30., 31.],
        Apriori=[32., 33.],
        VMR=[34., 35.],
        AVK=[[36., 37.], [38., 39.]],
    )


@pytest.mark.parametrize("name,product,expect", (
    ("Profile", "Temperature", "Retrieved temperature profile."),
    ("Profile", "O3", "Retrieved volume mixing ratio."),
    ("Latitude", "Temperature", "orig description"),
))
def test_parameter_get_description_works(name, product, expect):
    assert datamodel.Parameter(
        name=name,
        units="mm",
        description="orig description",
        dtype="f4",
        dimension=["time"],
        l2type=datamodel.L2Type.l2,
    ).get_description(product) == expect


@pytest.mark.parametrize("name,product,units,expect", (
    ("Lat", "Temperature", "degrees", "degrees"),
    ("Lat", "O3", "degrees", "degrees"),
    ("Profile", "O3", "product_specific", "-"),
    ("Profile", "Temperature", "product_specific", "K"),
    ("AVK", "O3", "product_specific", "%/%"),
    ("AVK", "Temperature", "product_specific", "K/K"),
))
def test_parameter_get_units_works(name, product, units, expect):
    assert datamodel.Parameter(
        name=name,
        units=units,
        description="fake",
        dtype="f4",
        dimension=["time"],
        l2type=datamodel.L2Type.l2,
    ).get_units(product) == expect


@pytest.mark.parametrize("freqmode,expect", (
    (1, datamodel.Filter(residual=1.5, minlmfactor=2.)),
    (8, datamodel.Filter(residual=1.5, minlmfactor=10.)),
    (13, datamodel.Filter(residual=1.5, minlmfactor=10.)),
    (19, datamodel.Filter(residual=1.5, minlmfactor=10.)),
    (21, datamodel.Filter(residual=1.5, minlmfactor=2.)),
))
def test_l2i_filter_works(freqmode, expect):
    assert datamodel.L2i(
        GenerationTime=dt.datetime(2000, 1, 2, 3, 4, 5),
        Residual=7.,
        MinLmFactor=8.,
        FreqMode=freqmode
    ).filter == expect


@pytest.mark.parametrize("freqmode,residual,lmfactor", (
    (1, 1.5, 2),
    (8, 1.5, 10),
))
def test_l2i_isvalid_works(freqmode, residual, lmfactor):
    assert datamodel.L2i(
        GenerationTime=dt.datetime(2000, 1, 2, 3, 4, 5),
        Residual=residual,
        MinLmFactor=lmfactor,
        FreqMode=freqmode
    ).isvalid()


@pytest.mark.parametrize("para,expect", (
    (
        datamodel.Parameter(
            "LST", "-", "-", "-", ["-"], datamodel.L2Type.l2anc
        ),
        0.,
    ),
    (
        datamodel.Parameter(
            "Residual", "-", "-", "-", ["-"], datamodel.L2Type.l2i
        ),
        7.,
    ),
    (
        datamodel.Parameter(
            "ScanID", "-", "-", "-", ["-"], datamodel.L2Type.l2
        ),
        11.,
    ),
))
def test_l2full_get_data_works(l2, l2i, l2anc, para, expect):
    l2full = datamodel.L2Full(
        l2=datamodel.to_l2(l2),
        l2i=datamodel.to_l2i(l2i),
        l2anc=datamodel.to_l2anc(l2anc)
    )
    assert l2full.get_data(para) == expect


def test_get_file_header_data_works():
    freqmode = 1
    invmode = "2"
    product = "3"
    time_start = dt.datetime(2000, 1, 2, 3, 4, 5)
    time_end = dt.datetime(2001, 1, 2, 3, 4, 6)
    assert set({
        "observation_frequency_mode": "1",
        "inversion_mode": "2",
        "level2_product_name": "3",
        "time_coverage_start": "2000-01-02T03:04:05Z",
        "time_coverage_end": "2001-01-02T03:04:05Z"
    }).issubset(set(datamodel.get_file_header_data(
        freqmode, invmode, product, time_start, time_end
    )))


@pytest.mark.parametrize("project,product,start,expect", (
    ("A", "B / B", dt.datetime(2000, 1, 2), "Odin-SMR_L2_A_B-B_2000-01.nc"),
    ("C", "B - B", dt.datetime(2000, 2, 2), "Odin-SMR_L2_C_B-B_2000-02.nc"),
    ("D", "B B", dt.datetime(2000, 3, 2), "Odin-SMR_L2_D_B-B_2000-03.nc"),
))
def test_generate_filename_works(project, product, start, expect):
    assert (
        datamodel.generate_filename(project, product, start)
        == expect
    )
