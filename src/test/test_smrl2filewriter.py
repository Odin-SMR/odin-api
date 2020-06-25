
import os
import datetime as dt

import pytest  # type: ignore
import numpy as np  # type: ignore
from netCDF4 import Dataset, num2date  # type: ignore

from odinapi.utils import smrl2filewriter
from odinapi.utils.datamodel import (
    L2Full,
    to_l2,
    to_l2i,
    to_l2anc,
    L2FILE
)


def l2anc(x: float):
    return to_l2anc({
        "LST": 0. + x,
        "Orbit": 1 + int(np.ceil(x)),
        "SZA1D": 2. + x,
        "SZA": [3. + x, 4. + x],
        "Theta": [5. + x, 6. + x],
    })


def l2i(x: float):
    return to_l2i({
        "GenerationTime": "2000-01-02T03:04:05Z",
        "Residual": 7. + x,
        "MinLmFactor": 8. + x,
        "FreqMode": 9 + x,
    })


def l2(x: float):
    return to_l2({
        "InvMode": "10",
        "ScanID": 11 + int(np.ceil(x)),
        "MJD": 12. + x,
        "Lat1D": 13. + x,
        "Lon1D": 14. + x,
        "Quality": 15 + int(x),
        "Altitude": [16. + x, 17. + x],
        "Pressure": [18. + x, 19. + x],
        "Latitude": [20. + x, 21. + x],
        "Longitude": [22. + x, 23. + x],
        "Temperature": [24. + x, 25. + x],
        "ErrorTotal": [26. + x, 27. + x],
        "ErrorNoise": [28. + x, 29. + x],
        "MeasResponse": [30. + x, 31. + x],
        "Apriori": [32. + x, 33. + x],
        "VMR": [34. + x, 35. + x],
        "AVK": [[36. + x, 37. + x], [38. + x, 39. + x]],
        "Profile": [40. + x, 41. + x],
    })


@pytest.fixture
def l2data():
    l2data = []
    for x in [0., 0.5, 1.0]:
        l2data.append(L2Full(l2i(x), l2anc(x), l2(x)))
    return l2data


@pytest.fixture
def filewriter(l2data):
    return smrl2filewriter.L2FileCreater(
        "Proj1", 9, "O3", L2FILE.parameters, l2data, "/tmp"
    )


@pytest.fixture
def l2file(tmpdir, l2data):
    fc = smrl2filewriter.L2FileCreater(
            "Proj1", 9, "O3", L2FILE.parameters, l2data, tmpdir
    )
    fc.write_to_file()
    return fc


class TestL2FileCreater:

    def test_start_works(self, filewriter):
        assert filewriter.start == dt.datetime(1858, 11, 29, 0, 0)

    def test_end_works(self, filewriter):
        assert filewriter.end == dt.datetime(1858, 11, 30, 0, 0)

    def test_ntimes_works(self, filewriter):
        assert filewriter.ntimes == 3

    def test_nlevels_works(self, filewriter):
        assert filewriter.nlevels == 2

    def test_invmode_works(self, filewriter):
        assert filewriter.invmode == "10"

    def test_get_filename_works(self, filewriter):
        assert filewriter.filename() == "/tmp/Odin-SMR_L2_Proj1_O3_1858-11.nc"

    def test_get_header_works(self, filewriter):
        assert set({
            "observation_frequency_mode": "9",
            "inversion_mode": "10",
            "level2_product_name": "O3",
            "time_coverage_start": "1858-11-29T00:00:00Z",
            "time_coverage_end": "1858-11-30T00:00:00Z",
        }).issubset(set(filewriter.header))

    def test_write_to_file_genereates_a_file(self, l2file):
        outfile = l2file.filename()
        assert os.path.isfile(outfile)

    def test_write_time_to_file_works(self, l2file):
        outfile = l2file.filename()
        with Dataset(outfile, "r") as ds:
            assert np.all(
                num2date(ds["Time"][:], ds["Time"].units)
                == [
                    dt.datetime(1858, 11, 29, 0, 0),
                    dt.datetime(1858, 11, 29, 12, 0),
                    dt.datetime(1858, 11, 30, 0, 0),
                ]
            )
            assert ds["Time"].description == "Mean time of the scan."

    def test_write_profile_to_file_works(self, l2file):
        outfile = l2file.filename()
        with Dataset(outfile, "r") as ds:
            assert np.all(
                ds["Profile"][:]
                == [[40., 41.], [40.5, 41.5], [41., 42.]]
            )
            assert (
                ds["Profile"].description == "Retrieved volume mixing ratio."
            )
            assert (
                ds["Profile"].units == "-"
            )

    @pytest.mark.parametrize("para,expect", (
        ("observation_frequency_mode", "9"),
        ("inversion_mode", "10"),
        ("level2_product_name", "O3"),
        ("time_coverage_start", "1858-11-29T00:00:00Z"),
        ("time_coverage_end", "1858-11-30T00:00:00Z"),
    ))
    def test_write_to_file_header_works(self, l2file, para, expect):
        outfile = l2file.filename()
        with Dataset(outfile, "r") as ds:
            assert getattr(ds, para) == expect
