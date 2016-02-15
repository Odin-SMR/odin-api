""" doc
"""
from flask import request, url_for
from flask import jsonify, abort
from flask.views import MethodView
from matplotlib import use
use("Agg")
from geoloc_tools import get_geoloc_info
from level1b_scandata_exporter import get_scan_data, scan2dictlist
from level1b_scandata_exporter_v2 import (get_scan_data_v2, scan2dictlist_v2,
                                          scan2dictlist_v4)
from level1b_scanlogdata_exporter import get_scan_logdata
from read_apriori import get_apriori
from read_mls import read_mls_file
from read_mipas import read_mipas_file
from read_smiles import read_smiles_file
from read_sageIII import read_sageIII_file
from newdonalettyEcmwfNC import date2mjd, mjd2stw, run_donaletty
from datetime import datetime
from dateutil.relativedelta import relativedelta
from database import DatabaseConnector


class DateInfo(MethodView):
    """plots information"""
    def get(self, version, date):
        """GET"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        date1 = datetime.strptime(date, '%Y-%m-%d')
        date2 = date1 + relativedelta(days=+1)
        mjd1 = date2mjd(date1)
        mjd2 = date2mjd(date2)
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        query_str = self.gen_query(stw1, stw2, mjd1, mjd2)
        date_iso = date1.date().isoformat()
        info_list = self.gen_data(date_iso, version, query_str)
        return jsonify(Date=date_iso, Info=info_list)

    def gen_data(self, date, version, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        info_list = []
        for row in result:
            info_dict = {}
            info_dict['Backend'] = row['backend']
            info_dict['FreqMode'] = row['freqmode']
            info_dict['NumScan'] = row['count']
            info_dict['URL'] = (
                '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}').format(
                    request.url_root, version, date, row['backend'],
                    row['freqmode'])
            info_list.append(info_dict)
        con.close()
        return info_list

    def gen_query(self, stw1, stw2, mjd1, mjd2):
        query_str = (
            "select freqmode, backend, count(distinct(stw)) "
            "from ac_cal_level1b "
            # "join attitude_level1 using(backend,stw) "
            "where stw between {0} and {1} "
            # "and mjd between {2} and {3} "
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
        info_list = self.gen_data(date_iso, version, query_str)
        return jsonify(Date=date, Info=info_list)

    def gen_query(self, stw1, stw2, mjd1, mjd2, backend):
        query_str = (
            "select freqmode, backend, count(distinct(stw)) "
            "from ac_cal_level1b "
            # "join attitude_level1 using(backend,stw) "
            "where stw between {0} and {1} "
            # "and mjd between {2} and {3} "
            "and backend='{4}' "
            "group by backend,freqmode "
            "order by backend,freqmode "
            ).format(stw1, stw2, mjd1, mjd2, backend)
        return query_str


class FreqmodeInfo(MethodView):
    """loginfo for all scans from a given date and freqmode"""
    def get(self, version, date, backend, freqmode):
        """GET method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)

        con = DatabaseConnector()
        loginfo = {}
        if version in ['v1', 'v2', 'v3']:
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
                'NumSpec',
                'FirstSpectrum',
                'LastSpectrum',
                'MJD',
                'ScanID',
            ]
        elif version in ['v4']:
            itemlist = [
                'DateTime',
                'FreqMode',
                'LatStart',
                'LatEnd',
                'LonStart',
                'LonEnd',
                'SunZD',
                'AltStart',
                'AltEnd',
                'NumSpec',
                'MJDStart',
                'MJDEnd',
                'ScanID',
            ]

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
            'OClO',
        ]

        if version == "v1":
            loginfo, _, _ = get_scan_logdata(
                con, backend, date+'T00:00:00', freqmode=int(freqmode), dmjd=1,
                version=version)
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
                datadict = {'ScanID': [], 'URL': []}
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
        elif version in ['v2', 'v3']:

            loginfo, _, _ = get_scan_logdata(
                con, backend, date+'T00:00:00', freqmode=int(freqmode), dmjd=1,
                version=version)

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
            for ind in range(len(loginfo['ScanID'])):

                freq_mode = loginfo['FreqMode'][ind]
                scanid = loginfo['ScanID'][ind]

                datadict = dict()
                for item in itemlist:
                    datadict[item] = loginfo[item][ind]

                datadict['URL'] = '{0}rest_api/{1}/scan/{2}/{3}/{4}'.format(
                    request.url_root,
                    version,
                    backend,
                    freq_mode,
                    scanid)
                datadict['URL-ptz'] = (
                    '{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}').format(
                        request.url_root,
                        version,
                        date,
                        backend,
                        freq_mode,
                        scanid
                        )
                for species in species_list:
                    datadict['''URL-apriori-{0}'''.format(species)] = (
                        '{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}').format(
                            request.url_root,
                            version,
                            species,
                            date,
                            backend,
                            freq_mode,
                            scanid
                            )
                loginfo['Info'].append(datadict)

        elif version in ['v4']:

            loginfo, _, _ = get_scan_logdata(
                con, backend, date+'T00:00:00', freqmode=int(freqmode), dmjd=1,
                version=version)

            try:
                for index in range(len(loginfo['ScanID'])):
                    loginfo['DateTime'][index] = (
                        loginfo['DateTime'][index]).isoformat('T')
            except KeyError:
                loginfo['Info'] = []
                return jsonify({'Info': loginfo['Info']})

            for item in loginfo.keys():
                try:
                    loginfo[item] = loginfo[item].tolist()
                except AttributeError:
                    pass

            loginfo['Info'] = []
            for ind in range(len(loginfo['ScanID'])):

                freq_mode = loginfo['FreqMode'][ind]
                scanid = loginfo['ScanID'][ind]

                datadict = dict()
                for item in itemlist:
                    datadict[item] = loginfo[item][ind]
                datadict['URLS'] = dict()
                datadict['URLS']['URL-spectra'] = (
                    '{0}rest_api/{1}/scan/{2}/{3}/{4}').format(
                        request.url_root,
                        version,
                        backend,
                        freq_mode,
                        scanid)
                datadict['URLS']['URL-ptz'] = (
                    '{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}').format(
                        request.url_root,
                        version,
                        date,
                        backend,
                        freq_mode,
                        scanid
                        )
                for species in species_list:
                    datadict['URLS']['''URL-apriori-{0}'''.format(species)] = (
                        '{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}').format(
                            request.url_root,
                            version,
                            species,
                            date,
                            backend,
                            freq_mode,
                            scanid
                            )
                loginfo['Info'].append(datadict)

        if version == "v1":

            return jsonify(loginfo)

        elif version in ['v2', 'v3', 'v4']:

            return jsonify({'Info': loginfo['Info']})


class ScanSpec(MethodView):
    """plots information: data from a given scan"""
    def get(self, version, backend, freqmode, scanno):
        """GET-method"""
        con = DatabaseConnector()
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        if version == "v1":
            spectra = get_scan_data(con, backend, freqmode, scanno)
            # spectra is a dictionary containing the relevant data
            datadict = scan2dictlist(spectra)
            return jsonify(datadict)
        elif version == "v2":
            spectra = get_scan_data_v2(con, backend, freqmode, scanno)
            # spectra is a dictionary containing the relevant data
            if spectra == {}:
                abort(404)
            datadict = scan2dictlist_v2(spectra)
            return jsonify(datadict)
        elif version == "v3":
            spectra = get_scan_data_v2(con, backend, freqmode, scanno)
            if spectra == {}:
                abort(404)
            # spectra is a dictionary containing the relevant data
            datadict = scan2dictlist_v2(spectra)
            return jsonify(datadict)
        elif version == "v4":
            spectra = get_scan_data_v2(con, backend, freqmode, scanno)
            if spectra == {}:
                abort(404)
            # spectra is a dictionary containing the relevant data
            datadict = scan2dictlist_v4(spectra)
            return jsonify(datadict)


class ScanPTZ(MethodView):
    """plots information: data from a given scan"""
    def get(self, version, date, backend, freqmode, scanno):
        """GET-method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        url_base = request.headers['Host']
        url_base = url_base.replace('webapi', 'localhost')
        url = 'http://' + url_base + url_for('.scaninfo', version='v1',
                                             date=date, backend=backend,
                                             freqmode=freqmode)
        mjd, _, midlat, midlon = get_geoloc_info(url, scanno)
        datadict = run_donaletty(mjd, midlat, midlon, scanno)
        for item in ['P', 'T', 'Z']:
            if item == 'P' and version in ['v4']:
                # convert from hPa to Pa
                datadict[item] = datadict[item]*100
            if item == 'Z' and version in ['v4']:
                # convert from km to m
                datadict[item] = datadict[item]*1000

            datadict[item] = datadict[item].tolist()
        if version in ['v4']:
            datadictv4 = dict()
            datadictv4['Pressure'] = datadict['P']
            datadictv4['Temperature'] = datadict['T']
            datadictv4['Altitude'] = datadict['Z']
            datadictv4['Latitude'] = datadict['latitude']
            datadictv4['Longitude'] = datadict['longitude']
            datadictv4['MJD'] = datadict['datetime']
            datadict = datadictv4

        return jsonify(datadict)


class ScanAPR(MethodView):
    """plots information: data from a given scan"""
    def get(self, version, species, date, backend, freqmode, scanno):
        """GET-method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        url_base = request.headers['Host']
        url_base = url_base.replace('webapi', 'localhost')
        url = 'http://' + url_base + url_for('.scaninfo', version='v1',
                                             date=date, backend=backend,
                                             freqmode=freqmode)
        _, day_of_year, midlat, _ = get_geoloc_info(url, scanno)
        datadict = get_apriori(species, day_of_year, midlat)
        for item in ['pressure', 'vmr']:
            datadict[item] = datadict[item].tolist()
        if version in ['v4']:
            datadictv4 = dict()
            datadictv4['Pressure'] = datadict['pressure']
            datadictv4['VMR'] = datadict['vmr']
            datadictv4['Species'] = datadict['species']
            datadict = datadictv4
        return jsonify(datadict)


class VdsFreqmodeInfo(MethodView):
    """verification data set scan info"""
    def get(self, version, backend, freqmode):
        """GET-method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        query_string = """select backend,freqmode,species,instrument,count(*)
                          from collocations
                          where backend='{0}' and freqmode={1}
                          group by backend, freqmode, species, instrument
                          """.format(backend, freqmode)
        datadict = self.gen_data(query_string, version)
        return jsonify(datadict)

    def gen_data(self, query_string, version):

        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        datadict = {'VDS': []}
        for row in result:
            data = dict()
            data['Backend'] = row['backend']
            data['FreqMode'] = row['freqmode']
            data['Species'] = row['species']
            data['Instrument'] = row['instrument']
            data['NumScan'] = row['count']
            data['URL'] = '{0}rest_api/{1}/vds/{2}/{3}/{4}/{5}'.format(
                request.url_root,
                version,
                row['backend'],
                row['freqmode'],
                row['species'],
                row['instrument'],)
            datadict['VDS'].append(data)
        return datadict


class VdsInstrumentInfo(MethodView):
    """verification data set scan info"""
    def get(self, version, backend, freqmode, instrument, species):
        """GET-method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        query_string = '''select date, backend, freqmode,
                          species, instrument, count(*) from collocations
                          where backend='{0}' and
                                freqmode={1} and
                                species='{2}' and
                                instrument='{3}'
                          group by date, backend, freqmode, species, instrument
                          order by date'''.format(backend, freqmode, species,
                                                  instrument)
        datadict = self.gen_data(query_string, version)
        return jsonify(datadict)

    def gen_data(self, query_string, version):

        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        datadict = {'VDS': []}
        for row in result:
            data = dict()
            data['Date'] = row['date']
            data['Backend'] = row['backend']
            data['FreqMode'] = row['freqmode']
            data['Species'] = row['species']
            data['Instrument'] = row['instrument']
            data['NumScan'] = row['count']
            data['URL'] = '{0}rest_api/{1}/vds/{2}/{3}/{4}/{5}/{6}'.format(
                request.url_root,
                version,
                row['backend'],
                row['freqmode'],
                row['species'],
                row['instrument'],
                row['date'],)
            datadict['VDS'].append(data)
        return datadict


class VdsDateInfo(MethodView):
    """verification data set scan info"""
    def get(self, version, backend, freqmode, species, instrument, date):
        """GET-method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        query_string = '''select * from collocations
                          where backend='{0}' and
                                freqmode={1} and
                                species='{2}' and
                                instrument='{3}'
                                and date='{4}' '''.format(backend, freqmode,
                                                          species, instrument,
                                                          date)
        datadict = self.gen_data(query_string, version, backend, freqmode,
                                 species, instrument, date)
        return jsonify(datadict)

    def gen_data(self, query_string, version, backend, freqmode, species,
                 instrument, date):

        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        datadict = {'VDS': []}
        lista1 = ['Date', 'FreqMode', 'Backend', 'ScanID', 'AltEnd',
                  'AltStart', 'LatEnd', 'LatStart', 'LonEnd', 'LonStart',
                  'MJDEnd', 'MJDStart', 'NumSpec', 'SunZD', 'Datetime']
        lista2 = ['Latitude', 'Longitude', 'MJD', 'Instrument', 'Species',
                  'File', 'File_Index', 'DMJD', 'DTheta']
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
            'OClO',
        ]

        for row in result:
            data = dict()
            odin = dict()
            for item in lista1:
                odin[item] = row[item.lower()]
            collocation = dict()
            for item in lista2:
                collocation[item] = row[item.lower()]
            data['OdinInfo'] = odin
            data['CollocationInfo'] = collocation
            data['URLS'] = dict()
            data['URLS']['URL-spectra'] = ('{0}rest_api/{1}/scan/{2}/{3}/{4}'
                                           ).format(request.url_root, version,
                                                    backend, freqmode,
                                                    row['scanid'])
            data['URLS']['URL-ptz'] = ('{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}'
                                       ).format(request.url_root, version,
                                                row['date'], backend, freqmode,
                                                row['scanid'])
            for species in species_list:
                data['URLS']['''URL-apriori-{0}'''.format(species)] = (
                    '{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}').format(
                        request.url_root,
                        version,
                        species,
                        row['date'],
                        backend,
                        freqmode,
                        row['scanid'])
            data['URLS']['''URL-{0}-{1}'''.format(row['instrument'],
                                                  row['species'])] = (
                '{0}rest_api/{1}/vds_external/{2}/{3}/{4}/{5}/{6}').format(
                request.url_root,
                version,
                row['instrument'],
                row['species'],
                row['date'],
                row['file'],
                row['file_index'])
            datadict['VDS'].append(data)
        con.close()
        return datadict


class VdsScanInfo(MethodView):
    """verification data set scan info"""
    def get(self, version, backend, freqmode):
        """GET-method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        query_string = '''select distinct(scanid), date, freqmode, backend,
                          altend, altstart, latend, latstart, lonend, lonstart,
                          mjdend, mjdstart, numspec, sunzd
                          from collocations
                          where backend='{0}' and freqmode={1}
                          '''.format(backend, freqmode)
        datadict = self.gen_data(query_string, version, backend, freqmode)
        return jsonify(datadict)

    def gen_data(self, query_string, version, backend, freqmode):

        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        datadict = {'VDS': []}
        lista1 = ['Date', 'FreqMode', 'Backend', 'ScanID', 'AltEnd',
                  'AltStart', 'LatEnd', 'LatStart', 'LonEnd', 'LonStart',
                  'MJDEnd', 'MJDStart', 'NumSpec', 'SunZD']
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
            'OClO',
        ]

        data = dict()
        for row in result:
            odin = dict()

            for item in lista1:
                odin[item] = row[item.lower()]
            data['Info'] = odin
            data['URLS'] = dict()
            data['URLS']['URL-spectra'] = ('{0}rest_api/{1}/scan/{2}/{3}/{4}'
                                           ).format(request.url_root, version,
                                                    backend, freqmode,
                                                    row['scanid'])
            data['URLS']['URL-ptz'] = ('{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}'
                                       ).format(request.url_root, version,
                                                row['date'], backend, freqmode,
                                                row['scanid'])
            for species in species_list:
                data['URLS']['''URL-apriori-{0}'''.format(species)] = (
                    '{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}').format(
                        request.url_root,
                        version,
                        species,
                        row['date'],
                        backend,
                        freqmode,
                        row['scanid'])
            datadict['VDS'].append(data)
        con.close()
        return datadict


class VdsExtData(MethodView):
    """display verification data set data from external instruments"""
    def get(self, version, instrument, species, date, filename, file_index):
        """GET-method"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        datadict = self.gen_data(instrument, species, date, filename,
                                 file_index)
        return jsonify(datadict)

    def gen_data(self, instrument, species, date, filename, file_index):

        if instrument == 'mls':
            data = read_mls_file(filename, date, species, file_index)
        elif instrument == 'mipas':
            data = read_mipas_file(filename, date, species, file_index)
        elif instrument == 'smiles':
            data = read_smiles_file(filename, date, species, file_index)
        elif instrument == 'sage-III':
            data = read_sageIII_file(filename, date, species, file_index)
        else:
            abort(404)

        return data
