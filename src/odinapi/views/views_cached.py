"""
Provide level1 views that extracts data from cache database.
"""

from datetime import datetime, date, timedelta
from odinapi.pg_database import squeeze_query
from typing import TypedDict

from flask import abort, jsonify, request
from flask.views import MethodView
from sqlalchemy import TextClause, text

from odinapi.pg_database import db
from .level1b_scanlogdata_exporter import ScanInfoExporter
from .urlgen import get_freqmode_info_url
from ..utils import get_args
from ..utils.defs import FREQMODE_TO_BACKEND, SPECIES


def get_scan_logdata_cached(date, freqmode, scanid=None):
    # generate query
    backend = ""
    try:
        backend = FREQMODE_TO_BACKEND[freqmode]
    except KeyError:
        abort(404)

    if date is not None:
        query_string = text(
            squeeze_query(
                """\
            select *
            from scans_cache
            where date = :d
            and freqmode = :f
            and backend = :b
            order by backend, freqmode"""
            )
        )
        query = db.session.execute(
            query_string, params=dict(d=date, f=freqmode, b=backend)
        )
    elif scanid is not None:
        query_string = text(
            squeeze_query(
                """\
            select *
            from scans_cache
            where scanid = :s
                and freqmode = :f
                and backend = :b
            order by backend, freqmode"""
            )
        )
        query = db.session.execute(
            query_string, params=dict(s=scanid, f=freqmode, b=backend)
        )
    else:
        abort(404)

    # execute query
    result = [row._asdict() for row in query]

    # translate keys
    key_translation = {
        "freqmode": "FreqMode",
        "backend": "BackEnd",
        "scanid": "ScanID",
        "altend": "AltEnd",
        "altstart": "AltStart",
        "latend": "LatEnd",
        "latstart": "LatStart",
        "lonend": "LonEnd",
        "lonstart": "LonStart",
        "mjdend": "MJDEnd",
        "mjdstart": "MJDStart",
        "numspec": "NumSpec",
        "sunzd": "SunZD",
        "datetime": "DateTime",
        "quality": "Quality",
    }
    translated = {}

    for key in key_translation:
        for row in result:
            try:
                value = row[key]
            except KeyError:
                continue

            try:
                translated[key_translation[key]].append(value)
            except KeyError:
                translated[key_translation[key]] = [value]

    return translated


def get_scan_logdata_uncached(freqmode, scanid):
    """get scan logdata from uncached tables"""
    try:
        backend = FREQMODE_TO_BACKEND[freqmode]
    except KeyError:
        abort(404)
    scan_info_exporter = ScanInfoExporter(backend, freqmode)
    scan_log_data = scan_info_exporter.extract_scan_log(scanid)

    logdata_asdict_withlists = {}
    for key in scan_log_data:
        logdata_asdict_withlists[key] = [scan_log_data[key]]

    return logdata_asdict_withlists


def get_scan_log_data(freqmode, scanid):
    logdata = get_scan_logdata_cached(
        date=None, freqmode=int(freqmode), scanid=int(scanid)
    )
    if logdata == {}:
        # if scan logdata is not yet in cache table
        logdata = get_scan_logdata_uncached(int(freqmode), int(scanid))
    return logdata


class MeasurementsCacheParams(TypedDict, total=False):
    date1: date
    date2: date
    backend: str


def generate_freq_mode_data(
    query: TextClause,
    root_url,
    version,
    params: MeasurementsCacheParams,
    include_date=False,
    date=None,
):
    result = db.session.execute(query, params=params)
    info_list = []
    for row in result:
        info_dict = {}
        if include_date:
            info_dict["Date"] = row.date
        info_dict["Backend"] = row.backend
        info_dict["FreqMode"] = row.freqmode
        info_dict["NumScan"] = row.nscans
        info_dict["URL"] = get_freqmode_info_url(
            root_url, version, date or row.date, row.backend, row.freqmode
        )
        info_list.append(info_dict)
    return info_list


class DateInfoCached(MethodView):
    """DateInfo using a cached table"""

    query = text(
        squeeze_query(
            """\
        select freqmode, backend, nscans
        from measurements_cache
        where date = :date1
        order by backend, freqmode"""
        )
    )

    def get(self, version: str, date: str):
        """Get date info from cache"""
        if version not in ["v4", "v5"]:
            return jsonify({"Error": f"Version {version} not supported"}), 404

        try:
            datetime_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(404)

        data = generate_freq_mode_data(
            self.query,
            request.url_root,
            version,
            {"date1": datetime_obj.date()},
            date=date,
        )

        if version == "v4":
            return jsonify(Date=date, Info=data)
        else:  # v5
            return jsonify(Date=date, Data=data, Type="freqmode_info", Count=len(data))


class PeriodInfoCached(MethodView):
    """Period using a cached table
    This is used to populate the calendar. The standard length of the period
    is six weeks, just enough to fill a Full Calendar view.
    """

    query = text(
        squeeze_query(
            """\
        select date, freqmode, backend, nscans
        from measurements_cache
        where date between :date1 and :date2
        order by backend, freqmode"""
        )
    )

    def get(self, version, year, month, day):
        """Get period info from cache"""
        if version not in ["v4", "v5"]:
            return jsonify({"Error": f"Version {version} not supported"}), 404

        try:
            date_start = date(year, month, day)
        except ValueError:
            abort(404)

        period_length = request.args.get("length", 42, type=int)
        date_end = date_start + timedelta(days=period_length - 1)
        data = generate_freq_mode_data(
            self.query,
            request.url_root,
            version,
            {"date1": date_start, "date2": date_end},
            include_date=True,
        )

        if version == "v4":
            return jsonify(period_start=date_start, period_end=date_end, Info=data)
        else:  # v5
            return jsonify(
                PeriodStart=date_start.isoformat(),
                PeriodEnd=date_end.isoformat(),
                Data=data,
                Type="freqmode_info",
                Count=len(data),
            )


class DateBackendInfoCached(DateInfoCached):
    """DateInfo for a certain backend using a cached table"""

    query = text(
        squeeze_query(
            """\
        select freqmode, backend, nscans
        from measurements_cache
        where date = :date1
            and backend= :backend
        group by backend, freqmode, nscans
        order by backend, freqmode, nscans"""
        )
    )

    def get(self, version, date: str, backend):
        """Get date backend info from cache"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404

        try:
            datetime_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(404)

        data = generate_freq_mode_data(
            self.query,
            request.url_root,
            version,
            {"date1": datetime_obj.date(), "backend": backend},
            date=date,
        )

        return jsonify(Date=date, Info=data)


def make_loginfo_v4(loginfo, keylist, ind, version, date, backend):
    freq_mode = loginfo["FreqMode"][ind]
    scanid = loginfo["ScanID"][ind]

    datadict = dict()
    for key in keylist:
        datadict[key] = loginfo[key][ind]
    datadict["URLS"] = dict()
    datadict["URLS"]["URL-log"] = (
        "{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}/{5}"
    ).format(request.url_root, version, date, backend, freq_mode, scanid)
    datadict["URLS"]["URL-spectra"] = ("{0}rest_api/{1}/scan/{2}/{3}/{4}/").format(
        request.url_root, version, backend, freq_mode, scanid
    )
    datadict["URLS"]["URL-ptz"] = ("{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}/").format(
        request.url_root, version, date, backend, freq_mode, scanid
    )
    for species in SPECIES:
        url_key = "URL-apriori-{0}".format(species)
        datadict["URLS"][url_key] = (
            "{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}/"
        ).format(request.url_root, version, species, date, backend, freq_mode, scanid)
    return datadict


def make_loginfo_v5(loginfo, keylist, ind, version, apriori=None):
    if apriori is None:
        apriori = SPECIES
    freq_mode = loginfo["FreqMode"][ind]
    scanid = loginfo["ScanID"][ind]

    datadict = dict()
    for key in keylist:
        datadict[key] = loginfo[key][ind]
    datadict["URLS"] = dict()
    datadict["URLS"]["URL-log"] = ("{0}rest_api/{1}/level1/{2}/{3}/Log/").format(
        request.url_root, version, freq_mode, scanid
    )
    datadict["URLS"]["URL-spectra"] = ("{0}rest_api/{1}/level1/{2}/{3}/L1b/").format(
        request.url_root, version, freq_mode, scanid
    )
    datadict["URLS"]["URL-ptz"] = ("{0}rest_api/{1}/level1/{2}/{3}/ptz/").format(
        request.url_root, version, freq_mode, scanid
    )
    for species in apriori.intersection(SPECIES):
        url_key = "URL-apriori-{0}".format(species)
        datadict["URLS"][url_key] = (
            "{0}rest_api/{1}/level1/{2}/{3}/apriori/{4}/"
        ).format(request.url_root, version, freq_mode, scanid, species)
    return datadict


class FreqmodeInfoCached(MethodView):
    """loginfo for all scans from a given date and freqmode"""

    KEYS_V4 = [
        "DateTime",
        "FreqMode",
        "LatStart",
        "LatEnd",
        "LonStart",
        "LonEnd",
        "SunZD",
        "AltStart",
        "AltEnd",
        "NumSpec",
        "MJDStart",
        "MJDEnd",
        "ScanID",
        "Quality",
    ]

    def get(self, version, date, backend, freqmode, scanno=None):
        """Get frequency mode info from cache"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404

        loginfo = {}
        keylist = self.KEYS_V4

        loginfo = get_scan_logdata_cached(date, freqmode=int(freqmode), scanid=scanno)

        for key in loginfo:
            try:
                loginfo[key] = loginfo[key].tolist()
            except AttributeError:
                pass

        loginfo["Info"] = []
        try:
            for ind in range(len(loginfo["ScanID"])):
                loginfo["Info"].append(
                    make_loginfo_v4(loginfo, keylist, ind, version, date, backend)
                )
        except KeyError:
            loginfo["Info"] = []

        data = loginfo["Info"]

        if scanno is None:
            return jsonify(Info=data)
        else:
            for s in data:
                if s["ScanID"] == scanno:
                    return jsonify(Info=s)
        return jsonify(Info={})


class FreqmodeInfoCachedNoBackend(MethodView):
    """loginfo for all scans without backend specification"""

    def get(self, version, date, freqmode, scanno=None, apriori=None):
        """Get frequency mode info from cache without backend"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

        if apriori is None:
            apriori = SPECIES
        loginfo = {}
        keylist = FreqmodeInfoCached.KEYS_V4

        loginfo = get_scan_logdata_cached(date, freqmode=int(freqmode), scanid=scanno)

        for key in loginfo:
            try:
                loginfo[key] = loginfo[key].tolist()
            except AttributeError:
                pass

        loginfo["Info"] = []
        try:
            for ind in range(len(loginfo["ScanID"])):
                loginfo["Info"].append(
                    make_loginfo_v5(loginfo, keylist, ind, version, apriori)
                )
        except KeyError:
            loginfo["Info"] = []

        data = loginfo["Info"]
        return jsonify(Data=data, Type="Log", Count=len(data))


class ScanInfoCachedNoBackend(MethodView):
    """Scan info for a single scan without backend"""

    def get(self, version, date, freqmode, scanno):
        """Get scan info from cache without backend"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

        loginfo = {}
        keylist = FreqmodeInfoCached.KEYS_V4

        loginfo = get_scan_logdata_cached(date, freqmode=int(freqmode), scanid=scanno)

        for key in loginfo:
            try:
                loginfo[key] = loginfo[key].tolist()
            except AttributeError:
                pass

        loginfo["Info"] = []
        try:
            for ind in range(len(loginfo["ScanID"])):
                loginfo["Info"].append(
                    make_loginfo_v5(loginfo, keylist, ind, version, SPECIES)
                )
        except KeyError:
            loginfo["Info"] = []

        data = loginfo["Info"]
        for s in data:
            if s["ScanID"] == scanno:
                return jsonify(Data=s, Type="Log", Count=None)
        abort(404)


class L1LogCached(MethodView):
    """L1 log for a freqmode and scanno"""

    def get(self, version, freqmode, scanno):
        """GET method"""
        if version not in ["v4", "v5"]:
            return jsonify({"Error": f"Version {version} not supported"}), 404

        keylist = FreqmodeInfoCached.KEYS_V4
        loginfo = get_scan_log_data(freqmode, scanno)

        for key in loginfo:
            try:
                loginfo[key] = loginfo[key].tolist()
            except AttributeError:
                pass

        loginfo["Info"] = []
        try:
            for ind in range(len(loginfo["ScanID"])):
                if version == "v4":
                    try:
                        backend = FREQMODE_TO_BACKEND[freqmode]
                    except KeyError:
                        abort(404)
                    date = loginfo["DateTime"][ind].date().isoformat()
                    loginfo["Info"].append(
                        make_loginfo_v4(loginfo, keylist, ind, version, date, backend)
                    )
                else:  # v5
                    loginfo["Info"].append(
                        make_loginfo_v5(loginfo, keylist, ind, version)
                    )
        except KeyError:
            loginfo["Info"] = []

        data = loginfo["Info"]

        for s in data:
            if s["ScanID"] == scanno:
                if version == "v4":
                    return jsonify(Info=s)
                else:  # v5
                    return jsonify(Data=s, Type="Log", Count=None)

        return (
            jsonify(Info={})
            if version == "v4"
            else jsonify(Data={}, Type="Log", Count=None)
        )


class L1LogCached_v4(L1LogCached):
    """Support class for L1 log endpoint in v4"""

    def get(self, version, freqmode, scanno):
        """Enforce v4 only"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404
        return super().get(version, freqmode, scanno)


class L1LogCachedList(MethodView):
    """Get a list of L1 Logs for a certain period"""

    def get(self, version, freqmode):
        """Get L1 log list for a time period"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

        start_time = get_args.get_datetime("start_time")
        end_time = get_args.get_datetime("end_time")
        if start_time and end_time and start_time > end_time:
            abort(400)

        apriori = get_args.get_list("apriori")
        if apriori is None:
            apriori = set()
        elif "all" in apriori or "ALL" in apriori:
            apriori = SPECIES
        else:
            apriori = set(apriori)

        log_list = []
        the_date = start_time
        keylist = FreqmodeInfoCached.KEYS_V4

        while the_date < end_time:
            loginfo = get_scan_logdata_cached(
                the_date.strftime("%Y-%m-%d"), freqmode=int(freqmode), scanid=None
            )

            for key in loginfo:
                try:
                    loginfo[key] = loginfo[key].tolist()
                except AttributeError:
                    pass

            try:
                for ind in range(len(loginfo["ScanID"])):
                    log_entry = make_loginfo_v5(loginfo, keylist, ind, version, apriori)
                    log_list.append(log_entry)
            except KeyError:
                pass

            the_date += timedelta(days=1)

        return jsonify(Data=log_list, Type="Log", Count=len(log_list))
