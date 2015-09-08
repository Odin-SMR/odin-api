import numpy as N
import copy
from pg import DB
from sys import stderr,stdout,stdin,argv,exit
import matplotlib.pyplot as plt
import matplotlib
from dateutil.relativedelta import relativedelta
from datetime import datetime
from date_tools import *
from datetime import date,datetime,timedelta

class Scanloginfo_exporter():
    '''A class derived for extracting loginfo from odin scan'''

    def __init__(self,backend,con):
        self.backend=backend
        self.con=con

    def get_orbit_stw(self,orbit):
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

        return minstw,maxstw,minmjd,maxmjd

    def get_scan_data(self, minstw, maxstw, minmjd, maxmjd):
        '''get attitude data within given stws'''

        query = self.con.query('''
                  select stw,calstw,latitude,longitude,mjd,
                  altitude,sunzd,freqmode from
                  attitude_level1
                  join ac_level1b using(stw,backend)
                  join ac_level0 using(stw,backend)
                  where stw between {0} and {1} and
                  mjd between {2} and {3} and
                  backend = '{4}' and sig_type='SIG' and
                  (intmode=1023 or intmode=511)
                  order by stw
                             '''.format(*[minstw,maxstw,minmjd,maxmjd,self.backend]))

        result = query.dictresult()

         #write result to a dictionary
        data = {
            'calstw'    : [],
            'latitude'  : [],
            'longitude' : [],
            'altitude'  : [],
            'mjd'       : [],
            'sunzd'     : [],
            'stw'       : [],
            'freqmode'  : [],
                }

        for row in result:
            for item in row.keys():
                data[item].append(row[item])

        for item in data.keys():
            data[item] = N.array(data[item])

        return data

    def extract_scan_loginfo(self,data,calstw,date1,date2):
        '''extract loginfo for a given scan '''
        mjd0 = datetime(1858,11,17)
        ind = N.nonzero( (data['calstw']==calstw) )[0]
        datei = mjd0 + relativedelta(days = +data['mjd'][ind[0]])
        #check that scan starts within desired time span
        if datei >= date1 and datei<=date2:

            outdata = {
             'ScanID'        : calstw,
             'StartLat'      : data['latitude'][ind[0]],
             'EndLat'        : data['latitude'][ind[-1]],
             'StartLon'      : data['longitude'][ind[0]],
             'EndLon'        : data['longitude'][ind[-1]],
             'AltStart'      : data['altitude'][ind[0]],
             'AltEnd'        : data['altitude'][ind[-1]],
             'MJD'           : ( data['mjd'][ind[0]] + data['mjd'][ind[-1]] ) / 2.0,
             'SunZD'         : ( data['sunzd'][ind[0]] + data['sunzd'][ind[-1]] ) / 2.0,
             'FreqMode'      : data['freqmode'][ind[0]],
             'NumSpec'       : ind.shape[0],
             'FirstSpectrum' : data['stw'][ind[0]],
             'LasttSpectrum' : data['stw'][ind[-1]],
             'DateTime'      : mjd0 + timedelta(( data['mjd'][ind[0]] + data['mjd'][ind[-1]] ) / 2.0),
                   }

            return outdata
        else:
            return []


def plot_loginfo(backend,date1,date2,data):
    '''plot data'''

    for item in data.keys():
        data[item] = N.array(data[item])

    fig=plt.figure(figsize=(15,8))
    fig.suptitle('''Scan loginfo for {0}: {1} - {2}'''.format(*[backend, date1, date2]))

    ax1 = plt.subplot2grid((6,1), (0,0), colspan=1,rowspan=1)
    plt.plot(data['DateTime'],data['StartLat'],'b.')
    plt.plot(data['DateTime'],data['EndLat'],'r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Lat. [Deg.]')

    ax1 = plt.subplot2grid((6,1), (1,0), colspan=1,rowspan=1)
    plt.plot(data['DateTime'],data['StartLon'],'b.')
    plt.plot(data['DateTime'],data['EndLon'],'r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Lon. [Deg.]')

    ax1 = plt.subplot2grid((6,1), (2,0), colspan=1,rowspan=1)
    plt.plot(data['DateTime'],data['AltStart']/1e3,'b.')
    plt.plot(data['DateTime'],data['AltEnd']/1e3,'r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('Alt. [Km]')

    ax1 = plt.subplot2grid((6,1), (3,0), colspan=1,rowspan=1)
    plt.plot(data['DateTime'],data['SunZD'],'-r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('SunZD [Deg.]')

    ax1 = plt.subplot2grid((6,1), (4,0), colspan=1,rowspan=1)
    plt.plot(data['DateTime'],data['FreqMode'],'-r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.axes.xaxis.set_ticklabels([])
    ax1.yaxis.set_label_text('FM [-]')

    ax1 = plt.subplot2grid((6,1), (5,0), colspan=1,rowspan=1)
    plt.plot(data['DateTime'],data['NumSpec'],'-r*')
    ax1.grid(True)
    ax1.minorticks_on()
    ax1.yaxis.set_label_text('NumSpec [-]')
    plt.ylim([0, N.max(data['NumSpec'])])
    hfmt = dates.DateFormatter('%Y/%m/%d-%hh:%mm')
    ax1.xaxis.set_label_text('Date [year/month]')
    plt.xticks(rotation=10)

    return fig

def append2dict(a,b):
    for item in a.keys():
        a[item].append(b[item])
    return a

def copyemptydict(a):
    b = dict()
    for item in a.keys():
        b[item] = []
    return b




def get_scan_logdata(con, backend,date,):


    a = Scanloginfo_exporter(backend, con)
    mjd0 = datetime(1858,11,17)

    try:

        date1 = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        query = 'date'
        mjd1 = datetime2mjd(date1)
        # add 6 hours to mjd2
        dmjd = 0.25
        mjd2 = mjd1 + dmjd
        date2 = date1 + relativedelta(days = +dmjd)
        # estimate stws from mjds (make sure the stws are outside the true range)
        # since mjd2stw is only an approximate converter
        minstw = mjd2stw( mjd1 - 0.1)
        maxstw = mjd2stw( mjd2 + 0.1)

    except:

        orbit = int(date)
        query = 'orbit'
        [minstw, maxstw, mjd1, mjd2] = a.get_orbit_stw(orbit)
        date1 = mjd0 + relativedelta(days = +mjd1)
        date2 = mjd0 + relativedelta(days = +mjd2)
        minstw = minstw - 16*60*15
        maxstw = maxstw + 16*60*15

    # extract data from scans within given time ranges
    data = a.get_scan_data(minstw, maxstw, mjd1-0.1, mjd2+0.1)

    calstw = N.unique(data['calstw'])
    # loop over scans and extract the desired data
    loginfo = dict()
    loginfodict_created = 0
    for ind,stw in enumerate(calstw):

        scanloginfo = a.extract_scan_loginfo(data,stw,date1,date2)

        if scanloginfo==[]:
            continue

        if loginfodict_created == 0:
            #create an empty dict
            loginfo = copyemptydict(scanloginfo)
        loginfodict_created = 1

        loginfo = append2dict(loginfo,scanloginfo)

    return loginfo
