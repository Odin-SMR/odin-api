# pylint: skip-file
"""
Provide level1 views that extracts data from cache database.
"""
from datetime import datetime, date, timedelta

from flask import abort, request

from odinapi.utils.defs import FREQMODE_TO_BACKEND, SPECIES
from odinapi.utils.swagger import SWAGGER
from odinapi.utils import get_args
from database import DatabaseConnector
from level1b_scanlogdata_exporter import get_scan_logdata
from odinapi.views.baseview import BaseView, register_versions
from odinapi.views.urlgen import get_freqmode_info_url


def get_scan_logdata_cached(con, date, freqmode, scanid=None):
    # generate query
    try:
        backend = FREQMODE_TO_BACKEND[freqmode]
    except KeyError:
        abort(404)

    if date is not None:
        query_string = (
            "select * "
            "from scans_cache "
            "where date = '{0}' "
            "and freqmode = {1} "
            "and backend = '{2}' "
            "order by backend, freqmode "
            ).format(date, freqmode, backend)
        query = con.query(query_string)
    elif scanid is not None:
        query_string = (
            "select * "
            "from scans_cache "
            "where scanid = {0} "
            "and freqmode = {1} "
            "and backend = '{2}' "
            "order by backend, freqmode "
            ).format(scanid, freqmode, backend)
        query = con.query(query_string)
    else:
        abort(404)

    # execute query
    result = query.dictresult()

    # translate keys
    infoDict = {}
    itemDict = {
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
        'quality': 'Quality',
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


def generate_freq_mode_data(query_string, root_url, version,
                            include_date=False, date=None):
    con = DatabaseConnector()
    query = con.query(query_string)
    result = query.dictresult()
    con.close()
    info_list = []
    for row in result:
        info_dict = {}
        if include_date:
            info_dict['Date'] = row['date']
        info_dict['Backend'] = row['backend']
        info_dict['FreqMode'] = row['freqmode']
        info_dict['NumScan'] = row['nscans']
        info_dict['URL'] = get_freqmode_info_url(
            root_url, version, date or row['date'], row['backend'],
            row['freqmode'])
        info_list.append(info_dict)
    return info_list


class DateInfoCached(BaseView):
    """DateInfo using a cached table"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level1'],
            ['version', 'date'],
            {"200": SWAGGER.get_type_response(
                'freqmode_info', is_list=True, Date=str)},
            summary="Get scan counts for a day from cached table"
        )

    @register_versions('fetch')
    def _fetch_data(self, version, date):
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            abort(404)
        query_str = self.gen_query(date)
        return generate_freq_mode_data(
            query_str, request.url_root, version, date=date)

    @register_versions('return', ['v4'])
    def _return_data(self, version, data, date):
        return dict(Date=date, Info=data)

    @register_versions('return', ['v5'])
    def _return_data_v5(self, version, data, date):
        return dict(
            Date=date, Data=data, Type='freqmode_info', Count=len(data))

    def gen_query(self, date):
        query_str = (
            "select freqmode, backend, nscans "
            "from measurements_cache "
            "where date = '{0}' "
            "order by backend, freqmode "
            ).format(date)
        return query_str


SWAGGER.add_parameter('year', 'path', str, description="yyyy")
SWAGGER.add_parameter('month', 'path', str, description="mm")
SWAGGER.add_parameter('day', 'path', str, description="dd")
SWAGGER.add_parameter(
    'length', 'query', int, description="Period length in number of days")


class PeriodInfoCached(BaseView):
    """Period using a cached table
    This is used to populate the calendar. The standard length of the period
    is six weeks, just enough to fill a Full Calendar view.
    """
    SUPPORTED_VERSIONS = ['v4', 'v5']

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level1'],
            ['version', 'year', 'month', 'day', 'length'],
            {"200": SWAGGER.get_type_response(
                'freqmode_info', is_list=True, PeriodStart=str,
                PeriodEnd=str)},
            summary="Get scan counts per day for a period",
            description=(
                "This is used to populate the calendar. "
                "The default length of the period is six weeks, "
                "just enough to fill a full calendar view."
            ))

    @register_versions('fetch')
    def _fetch_data(self, version, year, month, day):
        try:
            date_start = date(year, month, day)
        except ValueError:
            abort(404)
        period_length = request.args.get('length', 42, type=int)
        date_end = date_start + timedelta(days=period_length-1)
        query_str = self.gen_query(date_start, date_end)
        data = generate_freq_mode_data(query_str, request.url_root, version,
                                       include_date=True)
        return data, date_start, date_end

    def gen_query(self, date_start, date_end):
        return (
            "select date, freqmode, backend, nscans "
            "from measurements_cache "
            "where date between '{0}' and '{1}' "
            "order by backend, freqmode "
            ).format(date_start.isoformat(), date_end.isoformat())

    @register_versions('return', ['v4'])
    def _return_data(self, version, data, *args, **kwargs):
        data, start, end = data
        return dict(
            period_start=start,
            period_end=end,
            Info=data)

    @register_versions('return', ['v5'])
    def _return_data_v5(self, version, data, *args, **kwargs):
        data, start, end = data
        return dict(
            PeriodStart=start.isoformat(),
            PeriodEnd=end.isoformat(),
            Data=data,
            Type='freqmode_info',
            Count=len(data))


class DateBackendInfoCached(DateInfoCached):
    """DateInfo for a certain backend using a cached table"""

    SUPPORTED_VERSIONS = ['v4']

    @register_versions('fetch')
    def _fetch_data(self, version, date, backend):
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            abort(404)
        query_str = self.gen_query(date, backend)
        return generate_freq_mode_data(
            query_str, request.url_root, version, date=date)

    @register_versions('return')
    def _return_data(self, version, data, date, backend):
        return dict(Date=date, Info=data)

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


def make_loginfo_v4(loginfo, itemlist, ind, version, date, backend):
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
    for species in SPECIES:
        url_key = 'URL-apriori-{0}'.format(species)
        datadict['URLS'][url_key] = (
            '{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}/').format(
                request.url_root,
                version,
                species,
                date,
                backend,
                freq_mode,
                scanid
        )
    return datadict


def make_loginfo_v5(loginfo, itemlist, ind, version, apriori=SPECIES):
    freq_mode = loginfo['FreqMode'][ind]
    scanid = loginfo['ScanID'][ind]

    datadict = dict()
    for item in itemlist:
        datadict[item] = loginfo[item][ind]
    datadict['URLS'] = dict()
    datadict['URLS']['URL-log'] = (
        '{0}rest_api/{1}/level1/{2}/{3}/Log/'
        '').format(request.url_root,
                   version,
                   freq_mode,
                   scanid)
    datadict['URLS']['URL-spectra'] = (
        '{0}rest_api/{1}/level1/{2}/{3}/L1b/').format(
            request.url_root,
            version,
            freq_mode,
            scanid)
    datadict['URLS']['URL-ptz'] = (
        '{0}rest_api/{1}/level1/{2}/{3}/ptz/').format(
            request.url_root,
            version,
            freq_mode,
            scanid
        )
    for species in apriori.intersection(SPECIES):
        url_key = 'URL-apriori-{0}'.format(species)
        datadict['URLS'][url_key] = (
            '{0}rest_api/{1}/level1/{2}/{3}/apriori/{4}/').format(
                request.url_root,
                version,
                freq_mode,
                scanid,
                species
        )
    return datadict


class FreqmodeInfoCached(BaseView):
    """loginfo for all scans from a given date and freqmode"""

    ITEMS_V4 = [
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
        'Quality']

    @register_versions('fetch', ['v4'])
    def _fetch_data_v4(self, version, date, backend, freqmode, scanno=None):

        con = DatabaseConnector()
        loginfo = {}
        itemlist = self.ITEMS_V4

        loginfo = get_scan_logdata_cached(
            con, date, freqmode=int(freqmode), scanid=scanno)
        con.close()

        for item in loginfo.keys():
            try:
                loginfo[item] = loginfo[item].tolist()
            except AttributeError:
                pass

        loginfo['Info'] = []
        try:
            for ind in range(len(loginfo['ScanID'])):
                loginfo['Info'].append(
                    make_loginfo_v4(
                        loginfo, itemlist, ind, version, date, backend))
        except KeyError:
            loginfo['Info'] = []

        return loginfo['Info']

    @register_versions('return', ['v4'])
    def _return_data_v2(self, version, data, date, backend, freqmode,
                        scanno=None):
        if scanno is None:
            return {'Info': data}
        else:
            for s in data:
                if s['ScanID'] == scanno:
                    return {"Info": s}


class FreqmodeInfoCachedNoBackend(BaseView):
    SUPPORTED_VERSIONS = ['v5']

    @register_versions('swagger')
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level1'],
            ['version', 'date', 'freqmode'],
            {"200": SWAGGER.get_type_response('Log', is_list=True)},
            summary=(
                "Get log info for scans in a day and freqmode from "
                "cached table")
        )

    @register_versions('fetch')
    def _fetch_data(
            self, version, date, freqmode, scanno=None, apriori=SPECIES):
        con = DatabaseConnector()
        loginfo = {}
        itemlist = FreqmodeInfoCached.ITEMS_V4

        loginfo = get_scan_logdata_cached(
            con, date, freqmode=int(freqmode), scanid=scanno)
        con.close()

        for item in loginfo.keys():
            try:
                loginfo[item] = loginfo[item].tolist()
            except AttributeError:
                pass

        loginfo['Info'] = []
        try:
            for ind in range(len(loginfo['ScanID'])):
                loginfo['Info'].append(
                    make_loginfo_v5(loginfo, itemlist, ind, version, apriori))
        except KeyError:
            loginfo['Info'] = []

        return loginfo['Info']

    @register_versions('return')
    def _return_data(self, version, data, date, freqmode):
        return {'Data': data, 'Type': 'Log', 'Count': len(data)}


class ScanInfoCachedNoBackend(FreqmodeInfoCachedNoBackend):

    @register_versions('swagger')
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level1'],
            ['version', 'date', 'freqmode', 'scanno'],
            {"200": SWAGGER.get_type_response('Log')},
            summary="Get log info for a scan from cached table"
        )

    @register_versions('fetch')
    def _fetch_data(self, version, date, freqmode, scanno):
        return super(ScanInfoCachedNoBackend, self)._fetch_data(
            version, date, freqmode, scanno=scanno)

    @register_versions('return')
    def _return_data(self, version, data, date, freqmode, scanno):
        for s in data:
            if s['ScanID'] == scanno:
                return {'Data': s, 'Type': 'Log', 'Count': None}
        abort(404)


class L1LogCached(BaseView):
    """L1 log for a freqmode and scanno"""
    SUPPORTED_VERSIONS = ['v4', 'v5']

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level1'],
            ['version', 'freqmode', 'scanno'],
            {"200": SWAGGER.get_type_response('Log')},
            summary="Get log info for a scan from cached table"
        )

    @register_versions('fetch', ['v4'])
    def _fetch_data_v4(self, version, freqmode, scanno):
        """GET method"""

        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

        con = DatabaseConnector()
        loginfo = {}
        itemlist = FreqmodeInfoCached.ITEMS_V4

        loginfo = get_scan_logdata_cached(
            con, date=None, freqmode=int(freqmode), scanid=int(scanno))
        con.close()

        for item in loginfo.keys():
            try:
                loginfo[item] = loginfo[item].tolist()
            except AttributeError:
                pass

        loginfo['Info'] = []
        try:
            for ind in range(len(loginfo['ScanID'])):
                date = loginfo['DateTime'][ind].split(' ')[0]
                loginfo['Info'].append(
                    make_loginfo_v4(
                        loginfo, itemlist, ind, version, date, backend))
        except KeyError:
            loginfo['Info'] = []

        return loginfo['Info']

    @register_versions('return', ['v4'])
    def _return_data_v4(self, version, data, freqmode, scanno):
        for s in data:
            if s['ScanID'] == scanno:
                return {"Info": s}

    @register_versions('fetch', ['v5'])
    def _fetch_data(self, version, freqmode, scanno):
        con = DatabaseConnector()
        loginfo = {}
        itemlist = FreqmodeInfoCached.ITEMS_V4

        loginfo = get_scan_logdata_cached(
            con, date=None, freqmode=int(freqmode), scanid=scanno)
        con.close()

        for item in loginfo.keys():
            try:
                loginfo[item] = loginfo[item].tolist()
            except AttributeError:
                pass

        loginfo['Info'] = []
        try:
            for ind in range(len(loginfo['ScanID'])):
                loginfo['Info'].append(
                    make_loginfo_v5(loginfo, itemlist, ind, version))
        except KeyError:
            loginfo['Info'] = []

        return loginfo['Info']

    @register_versions('return', ['v5'])
    def _return_data(self, version, data, freqmode, scanno):
        for s in data:
            if s['ScanID'] == scanno:
                return {'Data': s, 'Type': 'Log', 'Count': None}


class L1LogCached_v4(L1LogCached):
    """Support class for L1 log endpoint in v4"""
    SUPPORTED_VERSIONS = ['v4']


SWAGGER.add_parameter(
    'start_time', 'query', str, string_format='date',
    description="Return data after this time (inclusive).")
SWAGGER.add_parameter(
    'end_time', 'query', str, string_format='date',
    description="Return data before this time (exclusive).")
SWAGGER.add_parameter(
    'apriori', 'query', [str], collection_format='multi',
    description=(
        "Return apriori data only for these species, or use 'all' for "
        "all apriori data.")
)


class L1LogCachedList(FreqmodeInfoCachedNoBackend):
    """Get a list of L1 Logs for a certain period"""
    SUPPORTED_VERSIONS = ['v5']

    @register_versions('swagger')
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level1'],
            ['version', 'freqmode', 'start_time', 'end_time', 'apriori'],
            {"200": SWAGGER.get_type_response('Log', is_list=True)},
            summary=(
                "Get log info for scans in period and freqmode from "
                "cached table"),
            description=(
                "Get log info for scans in period and freqmode from "
                "cached table. Apriori URLs are by default only "
                "returned for requested species, use 'apriori=all' to "
                "override this. Species names are case sensitive, "
                "invalid species names will be ignored - see data "
                "documentation for information on available apriori "
                "data."),
        )

    @register_versions('fetch')
    def _fetch_data(self, version, freqmode):
        start_time = get_args.get_datetime('start_time')
        end_time = get_args.get_datetime('end_time')
        if start_time and end_time and start_time > end_time:
            abort(400)

        apriori = get_args.get_list('apriori')
        if apriori is None:
            apriori = set()
        elif "all" in apriori or "ALL" in apriori:
            apriori = SPECIES
        else:
            apriori = set(apriori)

        log_list = []
        the_date = start_time
        while the_date < end_time:
            loginfo = super(L1LogCachedList, self)._fetch_data(
                version, the_date, freqmode, scanno=None, apriori=apriori)
            if len(loginfo) > 0:
                log_list.extend(loginfo)
            the_date += timedelta(days=1)

        return log_list

    @register_versions('return')
    def _return_data(self, version, data, freqmode):
        return {'Data': data, 'Type': 'Log', 'Count': len(data)}
