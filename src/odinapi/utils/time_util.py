# pylint: skip-file
from datetime import datetime


def datetime2mjd(dt):
    diff = dt - datetime(1858, 11, 17)
    return diff.days + (
        diff.seconds + diff.microseconds*1e-6)*datetime2mjd.days_per_second
datetime2mjd.days_per_second = 1./60/60/24


def datetime2stw(dt):
    return mjd2stw(datetime2mjd(dt))


def mjd2stw(mjd1):
    MJD0 = 56416.7782534
    stw0 = 6161431982
    rate = 1/16.0016444
    stw = (mjd1-MJD0)*86400.0/rate+stw0
    return int(stw)
