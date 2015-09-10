from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta


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


def get_freqmode_info(con):

    con=db()

    date0 = datetime(2015,1,1)
    scanlist=[]

    for i in range(10):
        date1 = date0 + relativedelta(days = +i)
        date2 = date1 + relativedelta(days = +1)
        mjd1 = date2mjd(date1)
        mjd2 = date2mjd(date2)
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)

        temp=['AC1', '549', 511, 'STRAT',2, stw1, stw2, mjd1, mjd2]
        query = con.query('''
          select floor(mjd) as date,freqmode from
          ac_cal_level1b
          join attitude_level1 using(backend,stw)
          where stw between {5} and {6}
          and backend='{0}'
          and frontend='{1}'
          and version=8
          and spectype='CAL'
          and intmode='{2}'
          and sourcemode='{3}'
          and freqmode={4}
          and mjd between {7} and {8}
          group by date,freqmode
          order by date
          '''.format(*temp))

        result = query.dictresult()

        for row in result:
            scanlist.append(row)
         
    return scanlist


