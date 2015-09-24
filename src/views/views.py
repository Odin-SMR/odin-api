""" doc
"""
from flask import request, send_file
from flask import render_template, jsonify
from flask.views import MethodView
import io
from matplotlib import use
use("Agg")
from date_tools import *
from utils import copyemptydict
from level1b_scandata_exporter import *
from level1b_scanlogdata_exporter import *
from pg import DB
from sys import stderr, stdout, stdin, argv, exit
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
from matplotlib import dates, rc
from dateutil.relativedelta import relativedelta
import matplotlib

class DateInfo(MethodView):
    """plots information"""
    def get(self, date):
        """GET"""
        date1 = datetime.strptime(date, '%Y-%m-%d')
        date2 = date1 + relativedelta(days=+1)
        mjd1 = date2mjd(date1)
        mjd2 = date2mjd(date2)
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        query_str = self.gen_query(stw1, stw2, mjd1, mjd2)
        date_iso = date1.date().isoformat()
        info_list = self.gen_data(date_iso, query_str)
        return jsonify(Date=date_iso, Info=info_list)

    def gen_data(self, date, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        info_list = []
        for row in result:
            info_dict = {}
            info_dict['Backend'] = row['backend']
            info_dict['FreqMode'] = row['freqmode']
            info_dict['NumScan'] = row['count']
            info_dict['URL'] = '{0}rest_api/v1/freqmode_info/{1}/{2}/{3}'.format(
                request.url_root, date, row['backend'], row['freqmode'])
            info_list.append(info_dict)
        con.close()
        return info_list

    def gen_query(self, stw1, stw2, mjd1, mjd2):
        query_str = (
            "select freqmode, backend, count(distinct(stw)) "
            "from ac_cal_level1b "
            "join attitude_level1 using(backend,stw) "
            "where stw between {0} and {1} "
            "and mjd between {2} and {3} "
            "group by backend,freqmode "
            "order by backend,freqmode "
            ).format(stw1, stw2, mjd1, mjd2)
        return query_str


class DateBackendInfo(DateInfo):
    """plots information"""
    def get(self, date, backend):
        """GET"""
        date1 = datetime.strptime(date, '%Y-%m-%d')
        date2 = date1 + relativedelta(days=+1)
        mjd1 = date2mjd(date1)
        mjd2 = date2mjd(date2)
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        query_str = self.gen_query(stw1, stw2, mjd1, mjd2, backend)
        date_iso = date1.date().isoformat()
        info_list = self.gen_data(date_iso, query_str)
        return jsonify(Date=date, Info=info_list)

    def gen_query(self, stw1, stw2, mjd1, mjd2, backend):
        query_str = (
            "select freqmode, backend, count(distinct(stw)) "
            "from ac_cal_level1b "
            "join attitude_level1 using(backend,stw) "
            "where stw between {0} and {1} "
            "and mjd between {2} and {3} "
            "and backend='{4}' "
            "group by backend,freqmode "
            "order by backend,freqmode "
            ).format(stw1, stw2, mjd1, mjd2, backend)
        return query_str

class FreqmodeInfo(MethodView):
    """loginfo for all scans from a given date and freqmode"""
    def get(self, date, backend, freqmode):
        con = DatabaseConnector()
        loginfo, date1, date2 = get_scan_logdata(
            con, backend, date+'T00:00:00', int(freqmode), 1)
        for index in range(len(loginfo['ScanID'])):
            row = []
            row.append(loginfo['DateTime'][index].date())
            for item in ['DateTime', 'FreqMode', 'StartLat', 'EndLat', 'SunZD', 'AltStart', 'AltEnd', 'ScanID']:
                row.append(loginfo[item][index])
        for item in loginfo.keys():
            try:
                loginfo[item] = loginfo[item].tolist()
            except:
                pass
        loginfo['Info'] = []
        for fm, scanid in zip(loginfo['FreqMode'], loginfo['ScanID']):
            datadict = {'ScanID':[], 'URL':[]}
            datadict['ScanID'] = scanid
            datadict['URL'] = '{0}rest_api/v1/scan/{1}/{2}/{3}'.format(
                request.url_root, 
                backend, 
                fm, 
                scanid)
            loginfo['Info'].append(datadict)
        return jsonify(**loginfo)


class ScanSpec(MethodView):
    """plots information: data from a given scan"""
    def get(self, backend, freqmode, scanno):
        con = DatabaseConnector()
        spectra = get_scan_data(con, backend, freqmode, scanno)
        #spectra is a dictionary containing the relevant data
        datadict = scan2dictlist(spectra)
        return jsonify(**datadict)

class DatabaseConnector(DB):
    def __init__(self):
        super(DatabaseConnector, self).__init__(
            dbname='odin',
            user='odinop',
            host='postgresql',
            passwd='***REMOVED***'
            )

