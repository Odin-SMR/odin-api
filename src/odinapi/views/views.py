""" doc
"""
from flask import request
from flask import jsonify
from flask.views import MethodView
from matplotlib import use
use("Agg")
from geoloc_tools import get_geoloc_info
from utils import copyemptydict
from level1b_scandata_exporter import get_scan_data, scan2dictlist
from level1b_scanlogdata_exporter import get_scan_logdata
from read_apriori import get_apriori
from newdonalettyEcmwfNC import date2mjd, mjd2stw, run_donaletty
from sys import stderr, stdout, stdin, argv, exit
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from matplotlib.ticker import ScalarFormatter, FormatStrFormatter
from matplotlib import dates, rc
from dateutil.relativedelta import relativedelta
import matplotlib
from database import DatabaseConnector
import requests as R

class DateInfo(MethodView):
    """plots information"""
    def get(self, version, date):
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
    def get(self, version, date, backend):
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
    def get(self, version, date, backend, freqmode):
        """GET method"""
        con = DatabaseConnector()
        loginfo = {}
        itemlist = [
                    'DateTime',
                    'FreqMode',
                    'StartLat',
                    'EndLat',
                    'StartLon',
                    'EndLon',
                    'SunZD',
                    'AltStart',
                    'AltEnd',
                    'ScanID']
        species_list = [
                    'BrO',
                    'Cl2O2',
                    'CO',
                    'HCl',
                    'HO2',
                    'NO2',
                    'OCS',
                    'C2H2',
                    'ClO',
                    'H2CO',
                    'HCN',
                    'HOBr',
                    'NO',
                    'OH',
                    'C2H6',
                    'ClONO2',
                    'H2O2',
                    'HCOOH',
                    'HOCl',
                    'O2',
                    'SF6',
                    'CH3Cl',
                    'ClOOCl',
                    'H2O',
                    'HF',
                    'N2',
                    'O3',
                    'SO2',
                    'CH3CN',
                    'CO2',
                    'H2S',
                    'HI',
                    'N2O',
                    'OBrO',
                    'CH4',
                    'COF2',
                    'HBr',
                    'HNO3',
                    'NH3',
                    'OClO']
 


        if version == "v1":
            loginfo, _, _ = get_scan_logdata(
                con, backend, date+'T00:00:00', int(freqmode), 1)
            for index in range(len(loginfo['ScanID'])):
                row = []
                row.append(loginfo['DateTime'][index].date())
                for item in itemlist:
                    row.append(loginfo[item][index])
            for item in loginfo.keys():
                try:
                    loginfo[item] = loginfo[item].tolist()
                except AttributeError:
                    pass
            loginfo['Info'] = []
            for freq_mode, scanid in zip(
                    loginfo['FreqMode'],
                    loginfo['ScanID']):
                datadict = {'ScanID':[], 'URL':[]}
                datadict['ScanID'] = scanid
                datadict['URL'] = '{0}rest_api/v1/scan/{1}/{2}/{3}'.format(
                    request.url_root,
                    backend,
                    freq_mode,
                    scanid)
                datadict['URL-ptz'] = (
                    '{0}rest_api/v1/ptz/{1}/{2}/{3}/{4}').format(
                        request.url_root,
                        date,
                        backend,
                        freq_mode,
                        scanid
                        )
                for species in species_list:
                    datadict['''URL-apriori-{0}'''.format(species)] = (
                        '{0}rest_api/v1/apriori/{1}/{2}/{3}/{4}/{5}').format(
                            request.url_root,
                            species,
                            date,
                            backend,
                            freq_mode,
                            scanid
                            )
                loginfo['Info'].append(datadict)
        elif version == "v2":

            loginfo, _, _ = get_scan_logdata(
                con, backend, date+'T00:00:00', int(freqmode), 1)
            for index in range(len(loginfo['ScanID'])):
                row = []
                row.append(loginfo['DateTime'][index].date())
                for item in itemlist:
                    row.append(loginfo[item][index])
           
            for item in loginfo.keys():
                try:
                    loginfo[item] = loginfo[item].tolist()
                except AttributeError:
                    pass
            loginfo['Info'] = []
            for ind in range(len(loginfo)):
      
                freq_mode = loginfo['FreqMode'][ind]
                scanid = loginfo['ScanID'][ind]
                
                datadict = dict()
                for item in itemlist:

                    datadict[item]=loginfo[item][ind]

                datadict['URL'] = '{0}rest_api/v1/scan/{1}/{2}/{3}'.format(
                    request.url_root,
                    backend,
                    freq_mode,
                    scanid)
                datadict['URL-ptz'] = (
                    '{0}rest_api/v1/ptz/{1}/{2}/{3}/{4}').format(
                        request.url_root,
                        date,
                        backend,
                        freq_mode,
                        scanid
                        )
                for species in species_list:
                    datadict['''URL-apriori-{0}'''.format(species)] = (
                        '{0}rest_api/v1/apriori/{1}/{2}/{3}/{4}/{5}').format(
                            request.url_root,
                            species,
                            date,
                            backend,
                            freq_mode,
                            scanid
                            )
                loginfo['Info'].append(datadict)

        if version == "v1":

            return jsonify(loginfo)

        elif version == "v2":

            return jsonify({'Info':loginfo['Info']})


class ScanSpec(MethodView):
    """plots information: data from a given scan"""
    def get(self, version, backend, freqmode, scanno):
        """GET-method"""
        con = DatabaseConnector()
        spectra = get_scan_data(con, backend, freqmode, scanno)
        #spectra is a dictionary containing the relevant data
        datadict = scan2dictlist(spectra)
        return jsonify(datadict)

class ScanPTZ(MethodView):
    """plots information: data from a given scan"""
    def get(self, version, date, backend, freqmode, scanno):
        """GET-method"""
        url = '''{0}rest_api/v1/freqmode_info/{1}/{2}/{3}'''.format(
            request.url_root,
            date,
            backend,
            freqmode)
        mjd, _, midlat, midlon = get_geoloc_info(url, scanno)
        datadict = run_donaletty(mjd, midlat, midlon, scanno)
        for item in ['P', 'T', 'Z']:
            datadict[item] = datadict[item].tolist()
        return jsonify(datadict)

class ScanAPR(MethodView):
    """plots information: data from a given scan"""
    def get(self, version, species, date, backend, freqmode, scanno):
        """GET-method"""
        url = '''{0}rest_api/v1/freqmode_info/{1}/{2}/{3}'''.format(
            request.url_root,
            date,
            backend,
            freqmode)
        _, day_of_year, midlat, _ = get_geoloc_info(url, scanno)
        datadict = get_apriori(species, day_of_year, midlat)
        for item in ['pressure', 'vmr']:
            datadict[item] = datadict[item].tolist()
        return jsonify(datadict)

