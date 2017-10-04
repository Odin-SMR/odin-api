# pylint: disable=E0401
'''module for extracting scan log data
   from odin scan
'''

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import numpy as N
import matplotlib.pyplot as plt
from matplotlib import dates
from odinapi.views.level1b_scandata_exporter_v2 import get_scan_data_v2
from odinapi.views.date_tools import mjd2stw, datetime2mjd
from odinapi.views.utils import copyemptydict


class ScanInfoExporter(object):
    '''A class derived for extracting loginfo from odin scan'''
    def __init__(self, backend, freqmode, con):
        self.backend = backend
        self.freqmode = freqmode
        self.con = con

    def get_orbit_stw(self, orbit):
        '''get min and max stw from a given orbit'''
        query = self.con.query('''
                  select min(foo.stw) as minstw ,max(foo.stw) as maxstw,
                  min(foo.mjd) as minmjd, max(foo.mjd) as maxmjd from
                  (select stw,mjd from attitude_level1 where
                  orbit>={0} and orbit<{0}+1 order by stw) as foo
                             '''.format(orbit))
        result = query.dictresult()
        maxstw = result[0]['maxstw']
        minstw = result[0]['minstw']
        maxmjd = result[0]['maxmjd']
        minmjd = result[0]['minmjd']
        return minstw, maxstw, minmjd, maxmjd

    def get_scanid(self, minstw, maxstw):
        '''get scanid within a time span'''
        query = self.con.query(
            '''select distinct(stw) from
               ac_cal_level1b
               where stw between {0} and {1} and
               backend = '{2}' and freqmode = {3}
               order by stw
            '''.format(*[minstw, maxstw,
                         self.backend, self.freqmode])
        )
        result = query.dictresult()
        scanid = []
        for row in result:
            scanid.append(row['stw'])
        return scanid

    def extract_scan_loginfo(self, date1, date2, scanid):
        '''extract loginfo for a given scan '''
        try:
            data = get_scan_data_v2(
                self.con, self.backend, self.freqmode, scanid
            )
        except IndexError:
            return []
        required_items = [
            'mjd', 'latitude', 'longitude', 'altitude',
            'sunzd', 'freqmode', 'quality']
        for item in required_items:
            if item not in data.keys():
                # if missing data item
                return []
            else:
                if data[item][0] is None or data[item][-1] is None:
                    # if data item is empty
                    return []
        mjd0 = datetime(1858, 11, 17)
        datei = mjd0 + relativedelta(days=+data['mjd'][0])
        # check that scan starts within desired time span
        if datei >= date1 and datei <= date2:
            outdata = {
                'ScanID': scanid,
                'LatStart': data['latitude'][0],
                'LatEnd': data['latitude'][-1],
                'LonStart': data['longitude'][0],
                'LonEnd': data['longitude'][-1],
                'AltStart': data['altitude'][0],
                'AltEnd': data['altitude'][-1],
                'MJDStart': data['mjd'][0],
                'MJDEnd': data['mjd'][-1],
                'SunZD': (data['sunzd'][0] + data['sunzd'][-1]) / 2.0,
                'FreqMode': data['freqmode'][0],
                'NumSpec': len(data['latitude']),
                'DateTime': mjd0 + timedelta(
                    (data['mjd'][0] + data['mjd'][-1]) / 2.0
                ),
                'Quality': data['quality'][0],
            }
            return outdata
        return []

    def get_loginfo_of_scans(self, date1, date2, scanid):
        '''loop over scans and extract the desired data'''
        loginfo = dict()
        loginfodict_created = 0
        for stw in scanid:
            try:
                scanloginfo = self.extract_scan_loginfo(date1, date2, stw)
            except ValueError:
                continue
            if scanloginfo == []:
                continue
            if loginfodict_created == 0:
                # create an empty dict
                loginfo = copyemptydict(scanloginfo)
                loginfodict_created = 1
            loginfo = append2dict(loginfo, scanloginfo)
        return loginfo


def append2dict(adict, bdict):
    '''append data to dictionary'''
    for item in adict:
        adict[item].append(bdict[item])
    return adict


def plot_loginfo(backend, date1, date2, data):
    '''plot data'''
    for item in data.keys():
        data[item] = N.array(data[item])
    fig = plt.figure(figsize=(15, 8))
    fig.suptitle(
        '''Scan loginfo for {0}: {1} - {2}'''.format(*[backend, date1, date2])
    )
    # -
    ax1 = plt.subplot2grid((6, 1), (0, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['StartLat'], 'b.')
    plt.plot(data['DateTime'], data['EndLat'], 'r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Lat. [Deg.]')
    # -
    ax1 = plt.subplot2grid((6, 1), (1, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['StartLon'], 'b.')
    plt.plot(data['DateTime'], data['EndLon'], 'r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Lon. [Deg.]')
    # -
    ax1 = plt.subplot2grid((6, 1), (2, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['AltStart'] / 1e3, 'b.')
    plt.plot(data['DateTime'], data['AltEnd'] / 1e3, 'r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Alt. [Km]')
    # -
    ax1 = plt.subplot2grid((6, 1), (3, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['SunZD'], '-r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('SunZD [Deg.]')
    # -
    ax1 = plt.subplot2grid((6, 1), (4, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['FreqMode'], '-r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('FM [-]')
    # -
    ax1 = plt.subplot2grid((6, 1), (5, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['NumSpec'], '-r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.yaxis.set_label_text('NumSpec [-]')
    plt.ylim([0, N.max(data['NumSpec'])])
    dates.DateFormatter('%Y/%m/%d-%hh:%mm')
    ax1.xaxis.set_label_text('Date [year/month]')
    plt.xticks(rotation=10)
    return fig


def get_scan_logdata(con, backend, datei, freqmode=-1, dmjd=0.25):
    '''get loginfo of scans for a given date'''
    sinfo = ScanInfoExporter(backend, freqmode, con)
    try:
        date1 = datetime.strptime(datei, '%Y-%m-%dT%H:%M:%S')
        mjd1 = datetime2mjd(date1)
        mjd2 = mjd1 + dmjd
        date2 = date1 + relativedelta(days=+dmjd)
        # estimate stws from mjds
        # (make sure the stws are outside the true range)
        # since mjd2stw is only an approximate converter
        minstw = mjd2stw(mjd1 - 0.1)
        maxstw = mjd2stw(mjd2 + 0.1)
    except ValueError:
        orbit = int(datei)
        [minstw, maxstw, mjd1, mjd2] = sinfo.get_orbit_stw(orbit)
        date1 = datetime(1858, 11, 17) + relativedelta(days=+mjd1)
        date2 = datetime(1858, 11, 17) + relativedelta(days=+mjd2)
        minstw = minstw - 16 * 60 * 15
        maxstw = maxstw + 16 * 60 * 15
    # extract scanids within the given time ranges
    scanid = sinfo.get_scanid(minstw, maxstw)
    # loop over scans and extract the desired data
    loginfo = sinfo.get_loginfo_of_scans(date1, date2, scanid)
    return loginfo, date1, date2
