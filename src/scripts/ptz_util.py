'''help class to find scan to preprocess'''


from dateutil.relativedelta import relativedelta
from odinapi.views.geoloc_tools import getscangeoloc
import requests as R


class PrecalcPTZ(object):
    '''class derived to precalc ptz'''
    def __init__(self, url_root, freqmode, date_start, date_end):
        self.date_start = date_start
        self.date_end = date_end
        self.freqmode = freqmode
        self.url_root = url_root
        self.date_range = []
        self.scanlist = []

    def get_date_range(self):
        '''create date list'''
        self.date_range.append(self.date_start)
        while self.date_range[-1] < self.date_end:
            self.date_range.append(
                self.date_range[-1] + relativedelta(days=1))

    def get_scandata4dateandfreqmode(self, date_i, freqmode):
        '''get scaninfo'''
        temp = [
            self.url_root,
            'freqmode_info',
            date_i.strftime("%Y-%m-%d"),
            freqmode
        ]
        url_string = '''{0}/{1}/{2}/{3}'''.format(*temp)
        self.scanlist = []
        try:
            data = R.get(url_string).json()
            for scan in data['Data']:
                scanid, mjd, midlat, midlon = get_geoloc_info(scan)
                self.scanlist.append([mjd, midlat, midlon, scanid])
        except ValueError:
            # one ends up here if freqmoe_i is
            # not measured the given date
            self.scanlist = []

    def get_freqmodes4date(self, date_i):
        '''get measured freqmodes for a given date'''
        if self.freqmode == -1:
            temp = [
                self.url_root,
                'freqmode_info',
                date_i.strftime("%Y-%m-%d")
            ]
            url_string = '''{0}/{1}/{2}'''.format(*temp)
            data = R.get(url_string).json()
            freqmodes = []
            if data['Count'] > 0:
                for fm_info in data['Data']:
                    freqmodes.append(fm_info['FreqMode'])
        else:
            freqmodes = [self.freqmode]
        return freqmodes


def get_geoloc_info(scan):
    '''Get the day of year and mid-latitude of the scan'''
    scanid = scan['ScanID']
    startlon = scan['LonStart']
    startlat = scan['LatStart']
    endlon = scan['LonEnd']
    endlat = scan['LatEnd']
    midlat, midlon = getscangeoloc(
        startlat, startlon, endlat, endlon
    )
    mjd = (scan['MJDStart'] + scan['MJDEnd'])/2
    return scanid, mjd, midlat, midlon
