from datetime import datetime
from threading import Lock
from typing import TypedDict

from dateutil.relativedelta import relativedelta  # type: ignore
from flask import abort, jsonify, request
from flask.views import MethodView
from numpy import around
from sqlalchemy import text

import odinapi.utils.get_args as get_args
from odinapi.pg_database import squeeze_query

# Activate Agg, must be done before imports below
from odinapi.utils import (
    time_util,
    use_agg,  # noqa: F401
)
from odinapi.utils.collocations import get_collocations
from odinapi.utils.defs import FREQMODE_TO_BACKEND, SPECIES

from odinapi.utils.time_util import datetime2mjd, mjd2stw
from odinapi.views.baseview import BaseView, register_versions
from odinapi.views.urlgen import get_freqmode_raw_url
from odinapi.views.views_cached import get_scan_log_data

from ..pg_database import db
from .geoloc_tools import get_geoloc_info
from .get_odinapi_info import get_config_data_files
from .level1b_scandata_exporter_v2 import get_scan_data_v2, scan2dictlist_v4
from .level1b_scanlogdata_exporter import get_scan_logdata
from .read_ace import read_ace_file
from .read_apriori import AprioriException, get_apriori
from .read_mipas import read_esa_mipas_file, read_mipas_file
from .read_mls import read_mls_file
from .read_odinsmr2_old import read_qsmr_file
from .read_osiris import read_osiris_file
from .read_ptz import get_ptz
from .read_sageIII import read_sageIII_file
from .read_smiles import read_smiles_file


class QueryParams(TypedDict, total=False):
    stw1: int
    stw2: int
    backend: str | None


class DateInfo(MethodView):
    """Get scan counts for a day"""

    query_str = text(
        "select freqmode, backend, count(distinct(stw)) "
        "from ac_cal_level1b "
        "where stw between :stw1 and :stw2 "
        "group by backend,freqmode "
        "order by backend,freqmode "
    )

    def get(self, version, date):
        """Get scan counts for a specific date"""
        if version not in ["v4", "v5"]:
            return jsonify({"Error": f"Version {version} not supported"}), 404
        
        try:
            date1 = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(404)
        
        date2 = date1 + relativedelta(days=+1)
        mjd1 = int(datetime2mjd(date1))
        mjd2 = int(datetime2mjd(date2))
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        
        data = self._gen_data(date, version, QueryParams(stw1=stw1, stw2=stw2))
        
        if version == "v4":
            return jsonify(Date=date, Info=data)
        else:  # v5
            return jsonify(Date=date, Data=data, Type="freqmode_info", Count=len(data))

    def _gen_data(self, date, version, params: QueryParams):
        result = db.session.execute(self.query_str, params=params)
        info_list = []
        for row in result:
            info_dict = {}
            info_dict["Backend"] = row.backend
            info_dict["FreqMode"] = row.freqmode
            info_dict["NumScan"] = row.count
            info_dict["URL"] = get_freqmode_raw_url(
                request.url_root, version, date, row.backend, row.freqmode
            )
            info_list.append(info_dict)
        return info_list


class DateBackendInfo(DateInfo):
    """Get scan counts for a day and backend"""

    query_str = text(
        squeeze_query(
            """\
        select freqmode, backend, count(distinct(stw))
        from ac_cal_level1b
        where stw between :stw1 and :stw2
            and backend=:backend
        group by backend,freqmode
        order by backend,freqmode"""
        )
    )

    def get(self, version, date, backend):
        """Get scan counts for a specific date and backend"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404
        
        try:
            date1 = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(404)
        
        date2 = date1 + relativedelta(days=+1)
        mjd1 = int(datetime2mjd(date1))
        mjd2 = int(datetime2mjd(date2))
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        
        data = self._gen_data(
            date, version, QueryParams(stw1=stw1, stw2=stw2, backend=backend)
        )
        
        return jsonify(Date=date, Info=data)


class FreqmodeInfo(BaseView):
    """loginfo for all scans from a given date and freqmode"""

    SUPPORTED_VERSIONS = ["v4"]

    KEYS_V4 = [
        "Quality",
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
    ]

    @register_versions("fetch", ["v4"])
    def _fetch_data_v4(self, version, date, backend, freqmode, scanno=None):
        loginfo = {}
        keylist = self.KEYS_V4

        loginfo, _, _ = get_scan_logdata(
            backend,
            date + "T00:00:00",
            freqmode=int(freqmode),
            dmjd=1,
        )

        try:
            for index in range(len(loginfo["ScanID"])):
                loginfo["DateTime"][index] = (loginfo["DateTime"][index]).isoformat("T")
        except KeyError:
            loginfo["Info"] = []
            return jsonify({"Info": loginfo["Info"]})

        for key in loginfo:
            try:
                loginfo[key] = loginfo[key].tolist()
            except AttributeError:
                pass

        loginfo["Info"] = []
        for ind in range(len(loginfo["ScanID"])):
            freq_mode = loginfo["FreqMode"][ind]
            scanid = loginfo["ScanID"][ind]

            datadict = dict()
            for key in keylist:
                datadict[key] = loginfo[key][ind]
            datadict["URLS"] = dict()
            datadict["URLS"]["URL-log"] = (
                "{0}rest_api/{1}/freqmode_raw/{2}/{3}/{4}/{5}/"
            ).format(request.url_root, version, date, backend, freq_mode, scanid)
            datadict["URLS"]["URL-spectra"] = (
                "{0}rest_api/{1}/scan/{2}/{3}/{4}"
            ).format(request.url_root, version, backend, freq_mode, scanid)
            datadict["URLS"]["URL-ptz"] = (
                "{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}"
            ).format(request.url_root, version, date, backend, freq_mode, scanid)
            for species in SPECIES:
                datadict["URLS"]["""URL-apriori-{0}""".format(species)] = (
                    "{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}"
                ).format(
                    request.url_root, version, species, date, backend, freq_mode, scanid
                )
            loginfo["Info"].append(datadict)

        return loginfo

    @register_versions("return", ["v4"])
    def _return_data_v2(self, version, loginfo, date, backend, freqmode, scanno=None):
        if scanno is None:
            try:
                return {"Info": loginfo["Info"]}
            except TypeError:
                return {"Info": []}
        else:
            for s in loginfo["Info"]:
                if s["ScanID"] == scanno:
                    return {"Info": s}


class FreqmodeInfoNoBackend(BaseView):
    SUPPORTED_VERSIONS = ["v5"]
    LOCK = Lock()

    @classmethod
    def _acquire_lock(cls, timeout: int = 1) -> bool:
        return cls.LOCK.acquire(timeout=timeout)

    @classmethod
    def _release_lock(cls) -> None:
        cls.LOCK.release()

    @register_versions("fetch")
    def _fetch_data(self, version, date, freqmode):
        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

        if not self._acquire_lock():
            self.logger.debug("could not acquire raw lock")
            abort(429)
        self.logger.debug("raw lock acquired")

        try:
            loginfo = {}
            keylist = FreqmodeInfo.KEYS_V4

            loginfo, _, _ = get_scan_logdata(
                backend,
                date + "T00:00:00",
                freqmode=int(freqmode),
                dmjd=1,
            )
        except Exception as err:
            raise (err)
        finally:
            self._release_lock()
            self.logger.debug("raw lock released")

        try:
            for index in range(len(loginfo["ScanID"])):
                loginfo["DateTime"][index] = (loginfo["DateTime"][index]).isoformat("T")
        except KeyError:
            loginfo["Info"] = []
            return jsonify({"Info": loginfo["Info"]})

        for key in loginfo:
            try:
                loginfo[key] = loginfo[key].tolist()
            except AttributeError:
                pass

        loginfo["Info"] = []
        for ind in range(len(loginfo["ScanID"])):
            freq_mode = loginfo["FreqMode"][ind]
            scanid = loginfo["ScanID"][ind]

            datadict = dict()
            for key in keylist:
                datadict[key] = loginfo[key][ind]
            datadict["URLS"] = dict()
            datadict["URLS"]["URL-log"] = (
                "{0}rest_api/{1}/level1/{2}/{3}/Log/"
            ).format(request.url_root, version, freq_mode, scanid)
            datadict["URLS"]["URL-spectra"] = (
                "{0}rest_api/{1}/level1/{2}/{3}/L1b/"
            ).format(request.url_root, version, freq_mode, scanid)
            datadict["URLS"]["URL-ptz"] = (
                "{0}rest_api/{1}/level1/{2}/{3}/ptz/"
            ).format(request.url_root, version, freq_mode, scanid)
            for species in SPECIES:
                datadict["URLS"]["""URL-apriori-{0}""".format(species)] = (
                    "{0}rest_api/{1}/level1/{2}/{3}/apriori/{4}/"
                ).format(request.url_root, version, freq_mode, scanid, species)
            loginfo["Info"].append(datadict)

        return loginfo["Info"]

    @register_versions("return")
    def _return_data_v5(self, version, data, date, freqmode):
        if not data:
            data = []
        return {"Data": data, "Type": "Log", "Count": len(data)}


class ScanInfoNoBackend(FreqmodeInfoNoBackend):
    @register_versions("fetch")
    def _fetch_data(self, version, date, freqmode, scanno):  # type: ignore
        return super(ScanInfoNoBackend, self)._fetch_data(version, date, freqmode)

    @register_versions("return")
    def _return_data_v5(self, version, data, date, freqmode, scanno):  # type: ignore
        for s in data:
            if s["ScanID"] == scanno:
                return {"Data": s, "Type": "Log", "Count": None}
        abort(404)


class ScanSpec(BaseView):
    """Get L1b data"""

    SUPPORTED_VERSIONS = ["v4"]

    @register_versions("fetch", ["v4"])
    def _get_v4(self, version, backend, freqmode, scanno, debug=False):
        spectra = get_scan_data_v2(backend, freqmode, scanno, debug)
        if spectra == {}:
            abort(404)
        # spectra is a dictionary containing the relevant data
        return scan2dictlist_v4(spectra)

    @register_versions("return")
    def _to_return_format(self, version, datadict, *args, **kwargs):
        return datadict


class ScanSpecNoBackend(ScanSpec):
    """Get L1b data"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get_v5(self, version, freqmode, scanno):
        debug = None
        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)
        try:
            debug = get_args.get_bool("debug")
        except ValueError:
            abort(400)
        return self._get_v4(version, backend, freqmode, scanno, bool(debug))

    @register_versions("return")
    def _to_return_format(self, version, data, *args, **kwargs):
        return {"Data": data, "Type": "L1b", "Count": None}


class ScanPTZ(BaseView):
    """Get PTZ data"""

    SUPPORTED_VERSIONS = ["v4"]

    @register_versions("fetch", ["v4"])
    def _get_ptz_v4(self, version, date, backend, freqmode, scanno):
        loginfo = get_scan_log_data(freqmode, scanno)
        if loginfo == {}:
            abort(404)
        mjd, _, midlat, midlon = get_geoloc_info(loginfo)
        ptz = get_ptz(backend, scanno, mjd, midlat, midlon)
        if not ptz:
            return dict()
        return ptz

    @register_versions("return")
    def _to_return_format(self, version, datadict, *args, **kwargs):
        return datadict


class ScanPTZNoBackend(ScanPTZ):
    """Get PTZ data"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get_ptz_v5(self, version, freqmode, scanno):
        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

        # TODO: Not always correct date?
        date = time_util.stw2datetime(scanno).strftime("%Y-%m-%d")
        return self._get_ptz_v4(version, date, backend, freqmode, scanno)

    @register_versions("return")
    def _to_return_format(self, version, datadict, *args, **kwargs):
        return {"Data": datadict, "Type": "ptz", "Count": None}


class ScanAPR(BaseView):
    """Get apriori data for a certain species"""

    SUPPORTED_VERSIONS = ["v4"]

    @register_versions("fetch", ["v4"])
    def _get_v4(self, version, species, date, backend, freqmode, scanno):
        loginfo = get_scan_log_data(freqmode, scanno)
        if loginfo == {}:
            self.logger.warning("could not get scandata")
            abort(404)
        _, day_of_year, midlat, _ = get_geoloc_info(loginfo)
        try:
            datadict = get_apriori(
                species,
                day_of_year,
                midlat,
                source=get_args.get_string("aprsource"),
            )
        except AprioriException:
            self.logger.warning("could not find apriori data")
            abort(404)
        # vmr can be very small, problematic to decreaese number of digits
        return {
            "Pressure": around(datadict["pressure"], decimals=8).tolist(),
            "VMR": datadict["vmr"].tolist(),
            "Species": datadict["species"],
            "Altitude": datadict["altitude"].tolist(),
        }

    @register_versions("return")
    def _return_format(self, version, data, *args, **kwargs):
        return data


class ScanAPRNoBackend(ScanAPR):
    """Get apriori data for a certain species"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get_v5(self, version, freqmode, scanno, species):
        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

        # TODO: Not always correct date?
        date = time_util.stw2datetime(scanno).strftime("%Y-%m-%d")
        return self._get_v4(version, species, date, backend, freqmode, scanno)

    @register_versions("return")
    def _return_format(self, version, datadict, *args, **kwargs):
        return {"Data": datadict, "Type": "apriori", "Count": None}


class CollocationsView(BaseView):
    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get(self, version, freqmode, scanno):
        try:
            return get_L2_collocations(request.url_root, version, freqmode, scanno)
        except KeyError:
            abort(404)

    @register_versions("return")
    def _return(self, version, collocations, freqmode, scanno):
        return {"Data": collocations, "Type": "collocation", "Count": len(collocations)}


def get_L2_collocations(root_url, version, freqmode, scanno):
    collocations_fields = ["date", "instrument", "species", "file", "file_index"]
    collocations = []
    for coll in get_collocations(freqmode, scanno, fields=collocations_fields):
        url = (
            "{root}rest_api/{version}/vds_external/{instrument}/"
            "{species}/{date}/{file}/{file_index}"
        ).format(
            root=root_url,
            version=version,
            instrument=coll["instrument"],
            species=coll["species"],
            date=coll["date"],
            file=coll["file"],
            file_index=coll["file_index"],
        )
        collocations.append(
            {"URL": url, "Instrument": coll["instrument"], "Species": coll["species"]}
        )
    return collocations


class VdsInfo(MethodView):
    """verification data set scan info"""

    query = text(
        squeeze_query(
            """select backend, freqmode, count(distinct(scanid))
        from collocations group by backend,freqmode"""
        )
    )

    def get(self, version):
        """GET-method"""
        if version not in ["v4"]:
            abort(404)
        datadict = self.gen_data(version)
        return jsonify(datadict)

    def gen_data(self, version):
        result = db.session.execute(self.query)
        datadict = {"VDS": []}
        for row_result in result:
            row = row_result._asdict()
            data = dict()
            data["Backend"] = row["backend"]
            data["FreqMode"] = row["freqmode"]
            data["NumScan"] = row["count"]
            data["URL-collocation"] = "{0}rest_api/{1}/vds/{2}/{3}".format(
                request.url_root, version, row["backend"], row["freqmode"]
            )
            data["URL-allscans"] = ("{0}rest_api/{1}/vds/{2}/{3}/allscans").format(
                request.url_root, version, row["backend"], row["freqmode"]
            )
            datadict["VDS"].append(data)
        return datadict


class VdsFreqmodeInfo(MethodView):
    """verification data set scan info"""

    query = text(
        squeeze_query(
            """\
        select backend,freqmode,species,instrument,count(*)
        from collocations
        where backend=:backend and freqmode=:freqmode
        group by backend, freqmode, species, instrument"""
        )
    )

    def get(self, version, backend, freqmode):
        """GET-method"""
        if version not in ["v4"]:
            abort(404)
        datadict = self.gen_data(version, dict(backend=backend, freqmode=freqmode))
        return jsonify(datadict)

    def gen_data(self, version, params):
        result = db.session.execute(self.query, params=params)
        datadict = {"VDS": []}
        for row_result in result:
            row = row_result._asdict()
            data = dict()
            data["Backend"] = row["backend"]
            data["FreqMode"] = row["freqmode"]
            data["Species"] = row["species"]
            data["Instrument"] = row["instrument"]
            data["NumScan"] = row["count"]
            data["URL"] = "{0}rest_api/{1}/vds/{2}/{3}/{4}/{5}".format(
                request.url_root,
                version,
                row["backend"],
                row["freqmode"],
                row["species"],
                row["instrument"],
            )
            datadict["VDS"].append(data)
        return datadict


class VdsInstrumentInfo(MethodView):
    """verification data set scan info"""

    query = text(
        squeeze_query(
            """\
        select date, backend, freqmode,species, instrument, count(*)
        from collocations
        where backend=:backend and
            freqmode=:freqmode and
            species=:species and
            instrument=:instrument
        group by date, backend, freqmode, species, instrument
        order by date"""
        )
    )

    def get(self, version, backend, freqmode, instrument, species):
        """GET-method"""
        if version not in ["v4"]:
            abort(404)
        datadict = self.gen_data(
            version,
            dict(
                backend=backend,
                freqmode=freqmode,
                instrument=instrument,
                species=species,
            ),
        )
        return jsonify(datadict)

    def gen_data(self, version, params):
        result = db.session.execute(self.query, params=params)
        datadict = {"VDS": []}
        for row_result in result:
            row = row_result._asdict()
            data = dict()
            data["Date"] = row["date"].isoformat()
            data["Backend"] = row["backend"]
            data["FreqMode"] = row["freqmode"]
            data["Species"] = row["species"]
            data["Instrument"] = row["instrument"]
            data["NumScan"] = row["count"]
            data["URL"] = "{0}rest_api/{1}/vds/{2}/{3}/{4}/{5}/{6}".format(
                request.url_root,
                version,
                row["backend"],
                row["freqmode"],
                row["species"],
                row["instrument"],
                row["date"],
            )
            datadict["VDS"].append(data)
        return datadict


class VdsDateInfo(MethodView):
    """verification data set scan info"""

    query = text(
        squeeze_query(
            """select * from collocations
        where backend=:backend and
        freqmode=:freqmode and
        species=:species and
        instrument=:instrument
        and date=:date """
        )
    )

    def get(self, version, backend, freqmode, species, instrument, date):
        """GET-method"""
        if version not in ["v4"]:
            abort(404)
        datadict = self.gen_data(version, backend, freqmode, species, instrument, date)
        return jsonify(datadict)

    def gen_data(self, version, backend, freqmode, species, instrument, date):
        result = db.session.execute(
            self.query,
            params=dict(
                backend=backend,
                freqmode=freqmode,
                species=species,
                instrument=instrument,
                date=date,
            ),
        )
        datadict = {"VDS": []}
        odin_keys = [
            "Date",
            "FreqMode",
            "Backend",
            "ScanID",
            "AltEnd",
            "AltStart",
            "LatEnd",
            "LatStart",
            "LonEnd",
            "LonStart",
            "MJDEnd",
            "MJDStart",
            "NumSpec",
            "SunZD",
            "Datetime",
        ]
        collocation_keys = [
            "Latitude",
            "Longitude",
            "MJD",
            "Instrument",
            "Species",
            "File",
            "File_Index",
            "DMJD",
            "DTheta",
        ]

        for row_data in result:
            row = row_data._asdict()
            data = dict()
            odin = dict()
            for key in odin_keys:
                odin[key] = row[key.lower()]
            collocation = dict()
            for key in collocation_keys:
                collocation[key] = row[key.lower()]
            data["OdinInfo"] = odin
            data["CollocationInfo"] = collocation
            data["URLS"] = dict()
            data["URLS"]["URL-spectra"] = ("{0}rest_api/{1}/scan/{2}/{3}/{4}").format(
                request.url_root, version, backend, freqmode, row["scanid"]
            )
            data["URLS"]["URL-ptz"] = ("{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}").format(
                request.url_root, version, row["date"], backend, freqmode, row["scanid"]
            )
            for species in SPECIES:
                data["URLS"]["""URL-apriori-{0}""".format(species)] = (
                    "{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}"
                ).format(
                    request.url_root,
                    version,
                    species,
                    row["date"],
                    backend,
                    freqmode,
                    row["scanid"],
                )
            data["URLS"][
                """URL-{0}-{1}""".format(row["instrument"], row["species"])
            ] = ("{0}rest_api/{1}/vds_external/{2}/{3}/{4}/{5}/{6}").format(
                request.url_root,
                version,
                row["instrument"],
                row["species"],
                row["date"],
                row["file"],
                row["file_index"],
            )
            datadict["VDS"].append(data)
        return datadict


class VdsScanInfo(MethodView):
    """verification data set scan info"""

    query = text(
        squeeze_query(
            """\
        select distinct(scanid), date, freqmode, backend,
        altend, altstart, latend, latstart, lonend, lonstart,
        mjdend, mjdstart, numspec, sunzd
        from collocations
        where backend=:backend and freqmode=:freqmode"""
        )
    )

    def get(self, version, backend, freqmode):
        """GET-method"""
        if version not in ["v4"]:
            abort(404)
        datadict = self.gen_data(version, backend, freqmode)
        return jsonify(datadict)

    def gen_data(self, version, backend, freqmode):
        result = db.session.execute(
            self.query, params=dict(backend=backend, freqmode=freqmode)
        )
        datadict = {"VDS": []}
        odin_keys = [
            "Date",
            "FreqMode",
            "Backend",
            "ScanID",
            "AltEnd",
            "AltStart",
            "LatEnd",
            "LatStart",
            "LonEnd",
            "LonStart",
            "MJDEnd",
            "MJDStart",
            "NumSpec",
            "SunZD",
        ]

        for row_data in result:
            row = row_data._asdict()
            data, odin = dict(), dict()
            for key in odin_keys:
                odin[key] = row[key.lower()]
            data["Info"] = odin
            data["URLS"] = dict()
            data["URLS"]["URL-spectra"] = ("{0}rest_api/{1}/scan/{2}/{3}/{4}").format(
                request.url_root, version, backend, freqmode, row["scanid"]
            )
            data["URLS"]["URL-ptz"] = ("{0}rest_api/{1}/ptz/{2}/{3}/{4}/{5}").format(
                request.url_root, version, row["date"], backend, freqmode, row["scanid"]
            )
            for species in SPECIES:
                data["URLS"]["""URL-apriori-{0}""".format(species)] = (
                    "{0}rest_api/{1}/apriori/{2}/{3}/{4}/{5}/{6}"
                ).format(
                    request.url_root,
                    version,
                    species,
                    row["date"],
                    backend,
                    freqmode,
                    row["scanid"],
                )
            datadict["VDS"].append(data)
        return datadict


class VdsExtData(MethodView):
    """display verification data set data from external instruments"""

    def get(self, version, instrument, species, date, file, file_index):
        """GET-method"""
        if version not in ["v4"]:
            abort(404)
        datadict = self.gen_data(instrument, species, date, file, file_index)
        return jsonify(datadict)

    def gen_data(self, instrument, species, date, file, file_index):
        if instrument == "mls":
            data = read_mls_file(file, date, species, file_index)
        elif instrument == "mipas":
            data = read_mipas_file(file, date, species, file_index)
        elif instrument == "mipas_esa":
            data = read_esa_mipas_file(file, date, species)
        elif instrument == "smiles":
            data = read_smiles_file(file, date, species, file_index)
        elif instrument == "sageIII":
            data = read_sageIII_file(file, date, species, "solar")
        elif instrument == "sageIII_lunar":
            data = read_sageIII_file(file, date, species, "lunar")
        elif instrument == "osiris":
            data = read_osiris_file(file, date, species, file_index)
        elif instrument == "smr":
            data = read_qsmr_file(file, species, file_index)
        elif instrument == "ace":
            data = read_ace_file(file, date, file_index)
        else:
            abort(404)

        return data


class ConfigDataFiles(BaseView):
    """display example files available to the system"""

    @register_versions("fetch")
    def gen_data(self, version):
        """get the data"""
        return get_config_data_files()

    @register_versions("return")
    def return_data(self, version, data):
        return data
