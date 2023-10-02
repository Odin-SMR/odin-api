import pytest  # type: ignore
import datetime as dt
import numpy as np  # type: ignore

from odinapi.utils import datamodel


@pytest.fixture(scope="session")
def l2anc():
    return {
        "LST": 0.0,
        "Orbit": 1,
        "SZA1D": 2.0,
        "SZA": [3.0, 4.0],
        "Theta": [5.0, 6.0],
    }


@pytest.fixture(scope="session")
def l2i():
    return {
        "GenerationTime": "2000-01-02T03:04:05Z",
        "Residual": 7.0,
        "MinLmFactor": 8.0,
        "FreqMode": 9,
    }


@pytest.fixture(scope="session")
def l2():
    return {
        "InvMode": "10",
        "ScanID": 11,
        "MJD": 12.0,
        "Lat1D": 13.0,
        "Lon1D": 14.0,
        "Quality": 15,
        "Altitude": [16.0, 17.0],
        "Pressure": [18.0, 19.0],
        "Latitude": [20.0, 21.0],
        "Longitude": [22.0, 23.0],
        "Temperature": [24.0, 25.0],
        "ErrorTotal": [26.0, 27.0],
        "ErrorNoise": [28.0, 29.0],
        "MeasResponse": [30.0, 31.0],
        "Apriori": [32.0, 33.0],
        "VMR": [34.0, 35.0],
        "AVK": [[36.0, 37.0], [38.0, 39.0]],
    }


def test_is_temperature_works():
    product = "Bla-Bla-/ Temperature Bla"
    assert datamodel.is_temperature(product)
    product = "Bla-Bla-/ O3 Bla"
    assert not datamodel.is_temperature(product)


def test_to_l2anc_works(l2anc):
    assert datamodel.to_l2anc(l2anc) == datamodel.L2anc(
        LST=0.0,
        Orbit=1,
        SZA1D=2.0,
        SZA=[3.0, 4.0],
        Theta=[5.0, 6.0],
    )


def test_to_l2i_works(l2i):
    assert datamodel.to_l2i(l2i) == datamodel.L2i(
        GenerationTime=dt.datetime(2000, 1, 2, 3, 4, 5),
        Residual=7.0,
        MinLmFactor=8.0,
        FreqMode=9,
    )


@pytest.mark.parametrize(
    "product,expect",
    (
        ("Temperature", [24.0, 25.0]),
        ("O3", [34.0, 35.0]),
    ),
)
def test_to_l2_works(l2, product, expect):
    assert datamodel.to_l2(l2, product) == datamodel.L2(
        InvMode="10",
        ScanID=11,
        Time=dt.datetime(1858, 11, 29, 0, 0),
        Lat1D=13.0,
        Lon1D=14.0,
        Quality=15,
        Altitude=[16.0, 17.0],
        Pressure=[18.0, 19.0],
        Latitude=[20.0, 21.0],
        Longitude=[22.0, 23.0],
        Temperature=[24.0, 25.0],
        ErrorTotal=[26.0, 27.0],
        ErrorNoise=[28.0, 29.0],
        MeasResponse=[30.0, 31.0],
        Apriori=[32.0, 33.0],
        VMR=[34.0, 35.0],
        AVK=[[36.0, 37.0], [38.0, 39.0]],
        Profile=expect,
    )


@pytest.mark.parametrize(
    "para,expect",
    (
        (datamodel.L2Desc.Profile, "Profile"),
        (datamodel.L2Desc.Latitude, "Latitude"),
        (datamodel.L2iDesc.MinLmFactor, "MinLmFactor"),
        (datamodel.L2iDesc.Residual, "Residual"),
        (datamodel.L2ancDesc.LST, "LST"),
        (datamodel.L2ancDesc.SZA, "SZA"),
    ),
)
def test_parameter_name_works(para, expect):
    assert (
        datamodel.Parameter(
            description=para,
            unit=datamodel.Unit.product,
            dtype=datamodel.DType.f4,
            dimension=datamodel.Dimension.d2,
        ).name
        == expect
    )


@pytest.mark.parametrize(
    "para,expect",
    (
        (datamodel.L2Desc.Profile, datamodel.L2Type.l2),
        (datamodel.L2Desc.Latitude, datamodel.L2Type.l2),
        (datamodel.L2iDesc.MinLmFactor, datamodel.L2Type.l2i),
        (datamodel.L2iDesc.Residual, datamodel.L2Type.l2i),
        (datamodel.L2ancDesc.LST, datamodel.L2Type.l2anc),
        (datamodel.L2ancDesc.SZA, datamodel.L2Type.l2anc),
    ),
)
def test_parameter_l2type_works(para, expect):
    assert (
        datamodel.Parameter(
            description=para,
            unit=datamodel.Unit.product,
            dtype=datamodel.DType.f4,
            dimension=datamodel.Dimension.d2,
        ).l2type
        == expect
    )


@pytest.mark.parametrize(
    "para,product,expect",
    (
        (datamodel.L2Desc.Profile, "Temperature", "Retrieved temperature profile."),
        (datamodel.L2Desc.Profile, "O3", "Retrieved volume mixing ratio."),
        (
            datamodel.L2Desc.Latitude,
            "Temperature",
            "Approximate latitude of each retrieval value.",
        ),
    ),
)
def test_parameter_get_description_works(para, product, expect):
    assert (
        datamodel.Parameter(
            description=para,
            unit="mm",
            dtype="f4",
            dimension=["time"],
        ).get_description(datamodel.is_temperature(product))
        == expect
    )


@pytest.mark.parametrize(
    "name,product,unit,expect",
    (
        (
            datamodel.L2Desc.Latitude,
            "Temperature",
            datamodel.Unit.lat,
            datamodel.Unit.lat,
        ),
        (datamodel.L2Desc.Latitude, "O3", datamodel.Unit.lat, datamodel.Unit.lat),
        (
            datamodel.L2Desc.Profile,
            "O3",
            datamodel.Unit.product,
            datamodel.Unit.unitless,
        ),
        (
            datamodel.L2Desc.Profile,
            "Temperature",
            datamodel.Unit.product,
            datamodel.Unit.temperature,
        ),
        (datamodel.L2Desc.AVK, "O3", datamodel.Unit.product, datamodel.Unit.poverp),
        (
            datamodel.L2Desc.AVK,
            "Temperature",
            datamodel.Unit.unitless,
            datamodel.Unit.koverk,
        ),
    ),
)
def test_parameter_get_unit_works(name, product, unit, expect):
    assert (
        datamodel.Parameter(
            description=name,
            unit=unit,
            dtype="f4",
            dimension=["time"],
        ).get_unit(datamodel.is_temperature(product))
        == expect
    )


@pytest.mark.parametrize(
    "freqmode,expect",
    (
        (1, datamodel.Filter(residual=1.5, minlmfactor=2.0)),
        (8, datamodel.Filter(residual=1.5, minlmfactor=10.0)),
        (13, datamodel.Filter(residual=1.5, minlmfactor=10.0)),
        (19, datamodel.Filter(residual=1.5, minlmfactor=10.0)),
        (21, datamodel.Filter(residual=1.5, minlmfactor=2.0)),
    ),
)
def test_l2i_filter_works(freqmode, expect):
    assert (
        datamodel.L2i(
            GenerationTime=dt.datetime(2000, 1, 2, 3, 4, 5),
            Residual=7.0,
            MinLmFactor=8.0,
            FreqMode=freqmode,
        ).filter
        == expect
    )


@pytest.mark.parametrize(
    "freqmode,residual,lmfactor",
    (
        (1, 1.5, 2),
        (8, 1.5, 10),
    ),
)
def test_l2i_isvalid_works(freqmode, residual, lmfactor):
    assert datamodel.L2i(
        GenerationTime=dt.datetime(2000, 1, 2, 3, 4, 5),
        Residual=residual,
        MinLmFactor=lmfactor,
        FreqMode=freqmode,
    ).isvalid()


@pytest.mark.parametrize(
    "freqmode,residual,lmfactor",
    (
        (1, 1.5, 3),
        (8, 1.5, 11),
        (1, 1.6, 2),
        (8, 1.6, 10),
        (1, np.inf, 2),
        (1, np.NINF, 2),
        (1, np.NAN, 2),
        (1, 1.5, np.inf),
        (1, 1.5, np.NINF),
        (1, 1.5, np.NAN),
    ),
)
def test_l2i_is_not_valid_works(freqmode, residual, lmfactor):
    assert not datamodel.L2i(
        GenerationTime=dt.datetime(2000, 1, 2, 3, 4, 5),
        Residual=residual,
        MinLmFactor=lmfactor,
        FreqMode=freqmode,
    ).isvalid()


@pytest.mark.parametrize(
    "para,expect",
    (
        (
            datamodel.Parameter(
                datamodel.L2ancDesc.LST,
                "-",
                "-",
                "-",
            ),
            0.0,
        ),
        (
            datamodel.Parameter(
                datamodel.L2iDesc.Residual,
                "-",
                "-",
                "-",
            ),
            7.0,
        ),
        (
            datamodel.Parameter(
                datamodel.L2Desc.ScanID,
                "-",
                "-",
                "-",
            ),
            11.0,
        ),
    ),
)
def test_l2full_get_data_works(l2, l2i, l2anc, para, expect):
    l2full = datamodel.L2Full(
        l2=datamodel.to_l2(l2, "O3"),
        l2i=datamodel.to_l2i(l2i),
        l2anc=datamodel.to_l2anc(l2anc),
    )
    assert l2full.get_data(para) == expect


def test_get_file_header_data_works():
    freqmode = 1
    invmode = "2"
    product = "3"
    time_start = dt.datetime(2000, 1, 2, 3, 4, 5)
    time_end = dt.datetime(2001, 1, 2, 3, 4, 6)
    assert set(
        {
            "observation_frequency_mode": "1",
            "inversion_mode": "2",
            "level2_product_name": "3",
            "time_coverage_start": "2000-01-02T03:04:05Z",
            "time_coverage_end": "2001-01-02T03:04:05Z",
        }
    ).issubset(
        set(
            datamodel.get_file_header_data(
                freqmode, invmode, product, time_start, time_end
            )
        )
    )


@pytest.mark.parametrize(
    "project,product,start,expect",
    (
        ("A", "B / B", dt.datetime(2000, 1, 2), "Odin-SMR_L2_A_B-B_2000-01.nc"),
        ("C", "B - B", dt.datetime(2000, 2, 2), "Odin-SMR_L2_C_B-B_2000-02.nc"),
        ("D", "B B", dt.datetime(2000, 3, 2), "Odin-SMR_L2_D_B-B_2000-03.nc"),
    ),
)
def test_generate_filename_works(project, product, start, expect):
    assert datamodel.generate_filename(project, product, start) == expect
