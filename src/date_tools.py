from datetime import datetime
# These functions should be moved to a folder somewhere
def datestring_to_date(string):
    """create a datetime from string"""
    year = int(string[0:4])
    if string[4] == '0':
        month = int(string[5])
    else:
        month = int(string[4:6])
    if string[6] == '0':
        day = int(string[7])
    else:
        day = int(string[6:8])
    date = datetime(year, month, day)
    return date

def date2mjd(date1):
    """Convert from date to mjd"""
    mjd1 = date1-datetime(1858, 11, 17)
    return mjd1.days

def mjd2stw(mjd1):
    """Convert from mjd to stw"""
    mjd0 = 56416.7782534
    stw0 = 6161431982
    rate = 1/16.0016444
    stw = (mjd1-mjd0)*86400.0/rate+stw0
    return int(stw)

def stw2mjd(stw):
    """Convert from stw to mjd"""
    stw0 = 6161431982
    mjd0 = 56416.7782534
    rate = 1/16.0016444
    mjd = mjd0+(stw-stw0)*rate/86400.0
    return mjd

def stw_from_date(date1, date2):
    """Convert from stw to date"""
    mjd1 = date2mjd(date1)
    mjd2 = date2mjd(date2)
    stw1 = mjd2stw(mjd1)
    stw2 = mjd2stw(mjd2)
    return stw1, stw2

def datetime2mjd(date):
    """datetime to mjd"""
    mjd0 = datetime(1858,11,17)
    datetime_diff = date-mjd0
    seconds_per_day = 24.0*60*60
    mjd = datetime_diff.days + datetime_diff.seconds/seconds_per_day
    return mjd

#======================================

