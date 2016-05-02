""" doc
"""
from flask import jsonify, abort, request
from flask.views import MethodView
from datetime import datetime, date, timedelta
from database import DatabaseConnector
from level1b_scanlogdata_exporter import get_scan_logdata


def get_backend(freqmode):
    backends = {
        1: "AC2",
        2: "AC1",
        8: "AC2",
        13: "AC1",
        14: "AC2",
        17: "AC2",
        19: "AC1",
        21: "AC1",
        22: "AC2",
        23: "AC1",
        24: "AC1",
        25: "AC1",
        29: "AC1",
        102: "AC2",
        113: "AC2",
        119: "AC2",
        121: "AC2",
    }
    return backends[freqmode]


def get_scan_logdata_cached(con, date, freqmode, scanid=None):
    # generate query
    if date is not None:
        query_string = (
            "select * "
            "from scans_cache "
            "where date = '{0}' "
            "and freqmode = {1} "
            "and backend = '{2}' "
            "order by backend, freqmode "
            ).format(date, freqmode, get_backend(freqmode))
        query = con.query(query_string)
    elif scanid is not None:
        query_string = (
            "select * "
            "from scans_cache "
            "where scanid = {0} "
            "and freqmode = {1} "
            "and backend = '{2}' "
            "order by backend, freqmode "
            ).format(scanid, freqmode, get_backend(freqmode))
        query = con.query(query_string)
    else:
        abort(404)

    # execute query
    result = query.dictresult()

    # translate keys
    infoDict = {}
    itemDict = {
        'datetime': 'DateTime',
        'freqmode': 'FreqMode',
        'backend':  'BackEnd',
        'scanid':   'ScanID',
        'altend':   'AltEnd',
        'altstart': 'AltStart',
        'latend':   'LatEnd',
        'latstart': 'LatStart',
        'lonend':   'LonEnd',
        'lonstart': 'LonStart',
        'mjdend':   'MJDEnd',
        'mjdstart': 'MJDStart',
        'numspec':  'NumSpec',
        'sunzd':    'SunZD',
        'datetime': 'DateTime',
    }

    for key in itemDict.keys():
        for row in result:
            try:
                item = row[key]
            except KeyError:
                continue

            try:
                infoDict[itemDict[key]].append(item)
            except KeyError:
                infoDict[itemDict[key]] = [item]

    return infoDict


class DateInfoCached(MethodView):
    """DateInfo using a cached table"""
    def get(self, version, date):
        """GET"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        try:
            date1 = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            date1 = datetime(2015, 1, 3)
        date_iso_str = date1.date().isoformat()
        query_str = self.gen_query(date_iso_str)
        info_list = self.gen_data(date_iso_str, version, query_str)
        return jsonify(Date=date_iso_str, Info=info_list)

    def gen_data(self, date, version, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        info_list = []
        for row in result:
            info_dict = {}
            info_dict['Backend'] = row['backend']
            info_dict['FreqMode'] = row['freqmode']
            info_dict['NumScan'] = row['nscans']
            info_dict['URL'] = (
                '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/').format(
                    request.url_root, version, date, row['backend'],
                    row['freqmode'])
            info_list.append(info_dict)
        con.close()
        return info_list

    def gen_query(self, date):
        query_str = (
            "select freqmode, backend, nscans "
            "from measurements_cache "
            "where date = '{0}' "
            "order by backend, freqmode "
            ).format(date)
        return query_str


class PeriodInfoCached(MethodView):
    """Period using a cached table
    This is used to populate the calendar. The standard length of the period
    is six weeks, just enough to fill a Full Calendar view.
    """
    def get(self, version, year, month, day):
        """GET"""
        if version not in ['v4']:
            abort(404)
        try:
            date_start = date(year, month, day)
        except ValueError:
            abort(404)
        period_length = request.args.get('length', 42, type=int)
        date_end = date_start + timedelta(days=period_length-1)
        query_string = (
            "select date, freqmode, backend, nscans "
            "from measurements_cache "
            "where date between '{0}' and '{1}' "
            "order by backend, freqmode "
            ).format(date_start.isoformat(), date_end.isoformat())
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        info_list = []
        for row in result:
            info_dict = {}
            info_dict['Date'] = row['date']
            info_dict['Backend'] = row['backend']
            info_dict['FreqMode'] = row['freqmode']
            info_dict['NumScan'] = row['nscans']
            info_dict['URL'] = (
                '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/').format(
                    request.url_root, version, row['date'], row['backend'],
                    row['freqmode'])
            info_list.append(info_dict)
        con.close()
        return jsonify(
            period_start=date_start.isoformat(),
            period_end=date_end.isoformat(),
            Info=info_list)


class DateBackendInfoCached(DateInfoCached):
    """plots information"""
    def get(self, version, date, backend):
        """GET"""
        date1 = datetime.strptime(date, '%Y-%m-%d')
        date_iso = date1.date().isoformat()
        query_str = self.gen_query(date_iso, backend)
        info_list = self.gen_data(date_iso, version, query_str)
        return jsonify(Date=date, Info=info_list)

    def gen_query(self, date, backend):
        query_str = (
            "select freqmode, backend, nscans "
            "from measurements_cache "
            "where date = '{0}' "
            "and backend= '{1}' "
            "group by backend, freqmode, nscans "
            "order by backend, freqmode, nscans "
            ).format(date, backend)
        return query_str


class FreqmodeInfoCached(MethodView):
    """loginfo for all scans from a given date and freqmode"""
    def get(self, version, date, backend, freqmode, scanno=None):
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
                datadict['URL'] = '{0}rest_api/v1/scan/{1}/{2}/{3}/'.format(
                    request.url_root,
                    backend,
                    freq_mode,
                    scanid)
                datadict['URL-log'] = (
                    '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/{5}').format(
                        request.url_root,
                        version,
                        date,
                        backend,
                        freq_mode,
                        scanid)
                datadict['URL-ptz'] = (
                    '{0}rest_api/v1/ptz/{1}/{2}/{3}/{4}/').format(
                        request.url_root,
                        date,
                        backend,
                        freq_mode,
                        scanid
                        )
                for species in species_list:
                    datadict['''URL-apriori-{0}'''.format(species)] = (
                        '{0}rest_api/v1/apriori/{1}/{2}/{3}/{4}/{5}/').format(
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

                datadict['URL'] = '{0}rest_api/{1}/scan/{2}/{3}/{4}/'.format(
                    request.url_root,
                    version,
                    backend,
                    freq_mode,
                    scanid)
                datadict['URL-log'] = (
                    '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/{5}').format(
                        request.url_root,
                        version,
                        date,
                        backend,
                        freq_mode,
                        scanid)
                datadict['URL-ptz'] = (
                    '{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}/').format(
                        request.url_root,
                        version,
                        date,
                        backend,
                        freq_mode,
                        scanid
                        )
                for species in species_list:
                    datadict['''URL-apriori-{0}'''.format(species)] = (
                        '{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}/').format(
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

            loginfo = get_scan_logdata_cached(con, date,
                                              freqmode=int(freqmode))

            for item in loginfo.keys():
                try:
                    loginfo[item] = loginfo[item].tolist()
                except AttributeError:
                    pass

            loginfo['Info'] = []
            try:
                for ind in range(len(loginfo['ScanID'])):

                    freq_mode = loginfo['FreqMode'][ind]
                    scanid = loginfo['ScanID'][ind]

                    datadict = dict()
                    for item in itemlist:
                        datadict[item] = loginfo[item][ind]
                    datadict['URLS'] = dict()
                    datadict['URLS']['URL-log'] = (
                        '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/{5}'
                        '').format(request.url_root,
                                   version,
                                   date,
                                   backend,
                                   freq_mode,
                                   scanid)
                    datadict['URLS']['URL-spectra'] = (
                        '{0}rest_api/{1}/scan/{2}/{3}/{4}/').format(
                            request.url_root,
                            version,
                            backend,
                            freq_mode,
                            scanid)
                    datadict['URLS']['URL-ptz'] = (
                        '{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}/').format(
                            request.url_root,
                            version,
                            date,
                            backend,
                            freq_mode,
                            scanid
                            )
                    for species in species_list:
                        datadict['URLS']['''URL-apriori-{0}'''.format(species)] \
                            = ('{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}/'
                               ).format(
                                request.url_root,
                                version,
                                species,
                                date,
                                backend,
                                freq_mode,
                                scanid
                                )
                    loginfo['Info'].append(datadict)
            except KeyError:
                loginfo['Info'] = []
                return jsonify({'Info': loginfo['Info']})

        if version == "v1":

            if scanno is None:
                return jsonify(loginfo)
            else:
                for s in loginfo['Info']:
                    if s['ScanID'] == scanno:
                        return s

        elif version in ['v2', 'v3', 'v4']:
            if scanno is None:
                return jsonify({'Info': loginfo['Info']})
            else:
                for s in loginfo['Info']:
                    if s['ScanID'] == scanno:
                        return jsonify({"Info": s})

        # If we reach this point, something has gone wrong:
        abort(404)


class L1LogCached(MethodView):
    """L1 log  for all scans from freqmode and scanno"""
    def get(self, version, freqmode, scanno):
        """GET method"""
        if version not in ['v4']:
            abort(404)

        backend = get_backend(freqmode)

        con = DatabaseConnector()
        loginfo = {}
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

        loginfo = get_scan_logdata_cached(con, date=None,
                                          freqmode=int(freqmode),
                                          scanid=int(scanno))

        for item in loginfo.keys():
            try:
                loginfo[item] = loginfo[item].tolist()
            except AttributeError:
                pass

        loginfo['Info'] = []
        try:
            for ind in range(len(loginfo['ScanID'])):

                freq_mode = loginfo['FreqMode'][ind]
                scanid = loginfo['ScanID'][ind]

                datadict = dict()
                for item in itemlist:
                    datadict[item] = loginfo[item][ind]
                datadict['URLS'] = dict()
                datadict['URLS']['URL-log'] = (
                    '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/{5}'
                    '').format(request.url_root,
                               version,
                               date,
                               backend,
                               freq_mode,
                               scanid)
                datadict['URLS']['URL-spectra'] = (
                    '{0}rest_api/{1}/scan/{2}/{3}/{4}/').format(
                        request.url_root,
                        version,
                        backend,
                        freq_mode,
                        scanid)
                datadict['URLS']['URL-ptz'] = (
                    '{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}/').format(
                        request.url_root,
                        version,
                        date,
                        backend,
                        freq_mode,
                        scanid
                        )
                for species in species_list:
                    datadict['URLS']['''URL-apriori-{0}'''.format(species)] \
                        = ('{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}/'
                           ).format(request.url_root,
                                    version,
                                    species,
                                    date,
                                    backend,
                                    freq_mode,
                                    scanid
                                    )
                loginfo['Info'].append(datadict)
        except KeyError:
            loginfo['Info'] = []
            return jsonify({'Info': loginfo['Info']})

        for s in loginfo['Info']:
            if s['ScanID'] == scanno:
                return jsonify({"Info": s})

        # If we reach this point, something has gone wrong:
        abort(404)
