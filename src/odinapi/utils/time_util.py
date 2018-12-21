from datetime import datetime, timedelta

MJD0 = 56416.7782534
stw0 = 6161431982
rate = 1/16.0016444
MJD_START_DATE = datetime(1858, 11, 17)


def datetime2mjd(dt):
    diff = dt - MJD_START_DATE
    return diff.days + (
        diff.seconds + diff.microseconds*1e-6)*datetime2mjd.days_per_second


datetime2mjd.days_per_second = 1./60/60/24


def datetime2stw(dt):
    return mjd2stw(datetime2mjd(dt))


def mjd2stw(mjd1):
    stw = (mjd1-MJD0)*86400.0/rate+stw0
    return int(stw)


def stw2mjd(stw1):
    mjd = (stw1 - stw0)*rate/86400.0+MJD0
    return mjd


def mjd2datetime(mjd):
    return MJD_START_DATE + timedelta(days=mjd)


def stw2datetime(stw):
    return mjd2datetime(stw2mjd(stw))
