# pylint: disable=E0401,C0413
'''module for extracting scan log data
   from odin scan
'''
from datetime import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa
from matplotlib import dates  # noqa
from odinapi.views.level1b_scandata_exporter_v2 import(  # noqa
    get_scan_data_v2,
)
from odinapi.views.date_tools import(  # noqa
    mjd2stw, datetime2mjd, mjd2datetime,
)


class ScanInfoExporter(object):
    '''A class derived for extracting loginfo from odin scan'''
    def __init__(self, backend, freqmode, con):
        self.backend = backend
        self.freqmode = freqmode
        self.con = con

    def get_scanids(self, minstw, maxstw):
        '''get scanids within a time span'''
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
        return [row['stw'] for row in result]

    def extract_scan_log(self, scanid):
        '''extract log info for a given scan '''
        try:
            scan_data = get_scan_data_v2(
                self.con, self.backend, self.freqmode, scanid
            )
        except(IndexError, TypeError, ValueError):
            return {}

        if not scan_data_is_valid(scan_data):
            return {}

        return {
            'ScanID': scanid,
            'LatStart': scan_data['latitude'][0],
            'LatEnd': scan_data['latitude'][-1],
            'LonStart': scan_data['longitude'][0],
            'LonEnd': scan_data['longitude'][-1],
            'AltStart': scan_data['altitude'][0],
            'AltEnd': scan_data['altitude'][-1],
            'MJDStart': scan_data['mjd'][0],
            'MJDEnd': scan_data['mjd'][-1],
            'SunZD': (scan_data['sunzd'][0] + scan_data['sunzd'][-1]) / 2.0,
            'FreqMode': scan_data['freqmode'][0],
            'NumSpec': len(scan_data['latitude']),
            'DateTime': mjd2datetime(
                (scan_data['mjd'][0] + scan_data['mjd'][-1]) / 2.0),
            'Quality': scan_data['quality'][0],
        }

    def get_log_of_scans(self, date_start, date_end, scanids):
        '''loop over scans and extract the desired data'''
        list_of_scan_logs = []
        for scanid in scanids:
            scan_log = self.extract_scan_log(scanid)
            if scan_log == {}:
                continue
            # check that scan starts within desired time span
            if (mjd2datetime(scan_log['MJDStart']) >= date_start and
                    mjd2datetime(scan_log['MJDStart']) <= date_end):
                list_of_scan_logs.append(scan_log)
        return list_of_scan_logs


def scan_data_is_valid(scan_data):
    '''check that data is not missing or empty'''
    required_items = [
        'mjd', 'latitude', 'longitude', 'altitude',
        'sunzd', 'freqmode', 'quality']
    for item in required_items:
        if item not in scan_data.keys():
            # if missing data item
            return False
        else:
            if (scan_data[item][0] is None or
                    scan_data[item][-1] is None):
                # if data item is empty
                return False
    return True


def plot_loginfo(backend, date1, date2, data):
    '''plot data'''
    for item in data.keys():
        data[item] = np.array(data[item])
    fig = plt.figure(figsize=(15, 8))
    fig.suptitle(
        '''Scan loginfo for {0}: {1} - {2}'''.format(*[backend, date1, date2])
    )
    # -
    ax1 = plt.subplot2grid((6, 1), (0, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['LatStart'], 'b.')
    plt.plot(data['DateTime'], data['LatEnd'], 'r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Lat. [Deg.]')
    # -
    ax1 = plt.subplot2grid((6, 1), (1, 0), colspan=1, rowspan=1)
    plt.plot(data['DateTime'], data['LonStart'], 'b.')
    plt.plot(data['DateTime'], data['LonEnd'], 'r*')
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
    plt.ylim([0, np.max(data['NumSpec'])])
    dates.DateFormatter('%Y/%m/%d-%hh:%mm')
    ax1.xaxis.set_label_text('Date [year/month]')
    plt.xticks(rotation=10)
    return fig


def get_scan_logdata(con, backend, datei, freqmode=-1, dmjd=0.25):
    '''get loginfo of scans for a given date'''
    scan_info_exporter = ScanInfoExporter(backend, freqmode, con)
    date_start = datetime.strptime(datei, '%Y-%m-%dT%H:%M:%S')
    mjd_start = datetime2mjd(date_start)
    mjd_end = mjd_start + dmjd
    date_end = date_start + relativedelta(days=+dmjd)
    # extract scanids within the given time ranges
    # (make sure the stws are outside the true range,
    # since mjd2stw is only an approximate converter)
    scanids = scan_info_exporter.get_scanids(
        mjd2stw(mjd_start - 0.1),
        mjd2stw(mjd_end + 0.1))
    # loop over scans and extract the desired data
    list_of_scan_logs = scan_info_exporter.get_log_of_scans(
        date_start, date_end, scanids)
    loginfo = {}
    for item in list_of_scan_logs[0].keys():
        loginfo[item] = [scan_log[item] for scan_log in list_of_scan_logs]
    return (loginfo, date_start, date_end)
