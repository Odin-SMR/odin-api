from datetime import datetime

import pytest  # type: ignore


from odinapi.utils import time_util


TIME_DATA = [
    {
        "stw": 37091441,
        "mjd": 51987.00783565,
        "date": datetime(2001, 3, 19, 0, 11, 17, 765000),
    },
    {
        "stw": 230021048,
        "mjd": 52126.55539352,
        "date": datetime(2001, 8, 5, 13, 19, 46, 485000),
    },
    {
        "stw": 1963672472,
        "mjd": 53380.51880787,
        "date": datetime(2005, 1, 10, 12, 27, 5, 669000),
    },
    {
        "stw": 2970095158,
        "mjd": 54108.47037037,
        "date": datetime(2007, 1, 8, 11, 17, 20, 63000),
    },
    {
        "stw": 4296163273,
        "mjd": 55067.62170139,
        "date": datetime(2009, 8, 24, 14, 55, 15, 332000),
    },
    {
        "stw": 5640984948,
        "mjd": 56040.33696759,
        "date": datetime(2012, 4, 23, 8, 5, 14, 787000),
    },
    {
        "stw": 7080072195,
        "mjd": 57081.23371528,
        "date": datetime(2015, 2, 28, 5, 36, 33, 990000),
    },
    {
        "stw": 8590260909,
        "mjd": 58173.55767361,
        "date": datetime(2018, 2, 24, 13, 23, 3, 340000),
    },
    {
        "stw": 10052785570,
        "mjd": 59231.405625,
        "date": datetime(2021, 1, 17, 9, 44, 6, 412000),
    },
    {
        "stw": 12893747299,
        "mjd": 59247.36561343,
        "date": datetime(2021, 2, 2, 8, 46, 29, 545000),
    },
]


class TestTimeConversions:
    @pytest.mark.parametrize("stw,mjd", (((t["stw"], t["mjd"]) for t in TIME_DATA)))
    def test_stw2mjd(self, stw, mjd):
        assert time_util.stw2mjd(stw) == pytest.approx(mjd, abs=1e-3)

    @pytest.mark.parametrize("mjd,stw", (((t["mjd"], t["stw"]) for t in TIME_DATA)))
    def test_mjd2stw(self, mjd, stw):
        assert time_util.mjd2stw(mjd) == pytest.approx(stw, abs=1e3)

    @pytest.mark.parametrize("mjd,expect", (((t["mjd"], t["date"]) for t in TIME_DATA)))
    def test_mjd2datetime(self, mjd, expect):
        date = time_util.mjd2datetime(mjd)
        assert (date - expect).total_seconds() == pytest.approx(0, abs=1)

    @pytest.mark.parametrize("date,mjd", (((t["date"], t["mjd"]) for t in TIME_DATA)))
    def test_datetime2mjd(self, date, mjd):
        assert time_util.datetime2mjd(date) == pytest.approx(mjd, abs=1e-4)

    @pytest.mark.parametrize("date,stw", (((t["date"], t["stw"]) for t in TIME_DATA)))
    def test_datetime2stw(self, date, stw):
        assert time_util.datetime2stw(date) == pytest.approx(stw, abs=1e3)

    @pytest.mark.parametrize("stw,expect", (((t["stw"], t["date"]) for t in TIME_DATA)))
    def test_stw2datetime(self, stw, expect):
        date = time_util.stw2datetime(stw)
        assert (date - expect).total_seconds() == pytest.approx(0, abs=1e2)
