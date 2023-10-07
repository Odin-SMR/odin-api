from datetime import datetime
import logging
from textwrap import dedent
from typing import TypedDict

from dateutil.relativedelta import relativedelta  # type: ignore
from flask import current_app, request, jsonify, abort
from flask.views import MethodView
from numpy import around
from threading import Lock
from sqlalchemy import text

# Activate Agg, must be done before imports below
from odinapi.utils import use_agg

from ..pg_database import db
from odinapi.utils.time_util import datetime2mjd, mjd2stw
from .geoloc_tools import get_geoloc_info
from .level1b_scandata_exporter_v2 import get_scan_data_v2, scan2dictlist_v4
from .level1b_scanlogdata_exporter import get_scan_logdata
from .read_apriori import AprioriException, get_apriori
from .read_mls import read_mls_file
from .read_mipas import read_mipas_file, read_esa_mipas_file
from .read_smiles import read_smiles_file
from .read_sageIII import read_sageIII_file
from .read_osiris import read_osiris_file
from .read_odinsmr2_old import read_qsmr_file
from .read_ace import read_ace_file
from .newdonalettyERANC import run_donaletty
from odinapi.utils.defs import SPECIES
from .get_odinapi_info import get_config_data_files

from odinapi.views.baseview import register_versions, BaseView
from odinapi.views.urlgen import get_freqmode_raw_url
from odinapi.utils.defs import FREQMODE_TO_BACKEND
from odinapi.utils import time_util
from odinapi.utils.collocations import get_collocations
from odinapi.utils.swagger import SWAGGER
from odinapi.views.views_cached import get_scan_log_data
import odinapi.utils.get_args as get_args

# Make linter happy
use_agg
SWAGGER.add_parameter("freqmode", "path", int)
SWAGGER.add_parameter("scanno", "path", int)
SWAGGER.add_parameter("date", "path", str, string_format="date")
SWAGGER.add_type(
    "freqmode_info", {"Backend": str, "FreqMode": int, "NumScan": int, "URL": str}
)

logger = logging.getLogger(__name__)


class QueryParams(TypedDict, total=False):
    stw1: int
    stw2: int
    backend: str | None


class DateInfo(BaseView):
    """Get scan counts for a day"""

    query_str = text(
        "select freqmode, backend, count(distinct(stw)) "
        "from ac_cal_level1b "
        "where stw between :stw1 and :stw2 "
        "group by backend,freqmode "
        "order by backend,freqmode "
    )

    @register_versions("swagger", ["v5"])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ["level1"],
            ["date"],
            {"200": SWAGGER.get_type_response("freqmode_info", is_list=True, Date=str)},
            summary="Get scan counts for a day",
        )

    @register_versions("fetch")
    def _get(self, version, date):
        try:
            date1 = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(404)
        date2 = date1 + relativedelta(days=+1)
        mjd1 = int(datetime2mjd(date1))
        mjd2 = int(datetime2mjd(date2))
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        return self.gen_data(date, version, QueryParams(stw1=stw1, stw2=stw2))

    @register_versions("return", ["v4"])
    def _return(self, version, data, date):
        return dict(Date=date, Info=data)

    @register_versions("return", ["v5"])
    def _return_v5(self, version, data, date):
        return dict(Date=date, Data=data, Type="freqmode_info", Count=len(data))

    def gen_data(self, date, version, params: QueryParams):
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

    SUPPORTED_VERSIONS = ["v4"]
    query_str = text(
        dedent(
            """\
        select freqmode, backend, count(distinct(stw))
        from ac_cal_level1b
        where stw between :stw1 and :stw2
            and backend=:backend
        group by backend,freqmode
        order by backend,freqmode"""
        )
    )

    @register_versions("fetch")
    def _get(self, version, date, backend):
        try:
            date1 = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            abort(404)
        date2 = date1 + relativedelta(days=+1)
        mjd1 = int(datetime2mjd(date1))
        mjd2 = int(datetime2mjd(date2))
        stw1 = mjd2stw(mjd1)
        stw2 = mjd2stw(mjd2)
        return self.gen_data(
            date, version, QueryParams(stw1=stw1, stw2=stw2, backend=backend)
        )

    @register_versions("return")
    def _return(self, version, data, date, backend):
        return dict(Date=date, Info=data)


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


SWAGGER.add_type(
    "Log",
    {
        "AltEnd": float,
        "AltStart": float,
        "DateTime": str,
        "FreqMode": int,
        "LatEnd": float,
        "LatStart": float,
        "LonEnd": float,
        "LonStart": float,
        "MJDEnd": float,
        "MJDStart": float,
        "NumSpec": int,
        "Quality": int,
        "ScanID": int,
        "SunZD": float,
        "URLS": {
            url_key: str
            for url_key in ["URL-apriori-%s" % species for species in SPECIES]
            + ["URL-log", "URL-ptz", "URL-spectra"]
        },
    },
)


class FreqmodeInfoNoBackend(BaseView):
    SUPPORTED_VERSIONS = ["v5"]
    LOCK = Lock()

    @classmethod
    def _acquire_lock(cls, timeout: int = 1) -> bool:
        return cls.LOCK.acquire(timeout=timeout)

    @classmethod
    def _release_lock(cls) -> None:
        cls.LOCK.release()

    @register_versions("swagger")
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ["level1"],
            ["date", "freqmode"],
            {"200": SWAGGER.get_type_response("Log", is_list=True)},
            summary="Get log info for scans in a day and freqmode",
        )

    @register_versions("fetch")
    def _fetch_data(self, version, date, freqmode):
        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

        if not self._acquire_lock():
            logging.debug("could not acquire raw lock")
            abort(429)
        logging.debug("raw lock acquired")

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
            logging.debug("raw lock released")

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
    @register_versions("swagger")
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ["level1"],
            ["date", "freqmode", "scanno"],
            {"200": SWAGGER.get_type_response("Log")},
            summary="Get log info for a scan",
        )

    @register_versions("fetch")
    def _fetch_data(self, version, date, freqmode, scanno):
        return super(ScanInfoNoBackend, self)._fetch_data(version, date, freqmode)

    @register_versions("return")
    def _return_data_v5(self, version, data, date, freqmode, scanno):
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


SWAGGER.add_type(
    "L1b",
    {
        "Altitude": [float],
        "Apodization": [int],
        "AttitudeVersion": [int],
        "Backend": [int],
        "Channels": [int],
        "Dec2000": [float],
        "Efftime": [float],
        "FreqCal": [[float]],
        "FreqMode": [int],
        "FreqRes": [float],
        "Frequency": {
            "AppliedDopplerCorr": [float],
            "ChannelsID": [int],
            "IFreqGrid": [float],
            "LOFreq": [float],
            "SubBandIndex": [[int]],
        },
        "Frontend": [int],
        "GPSpos": [[float]],
        "GPSvel": [[float]],
        "IntTime": [float],
        "Latitude": [float],
        "Longitude": [float],
        "MJD": [float],
        "MoonPos": [[float]],
        "Orbit": [float],
        "Quality": [float],
        "RA2000": [float],
        "SBpath": [float],
        "STW": [int],
        "ScanID": [int],
        "Spectrum": [[float]],
        "SunPos": [[float]],
        "SunZD": [float],
        "TSpill": [float],
        "Tcal": [float],
        "Trec": [float],
        "TrecSpectrum": [float],
        "Version": [int],
        "Vgeo": [float],
        "ZeroLagVar": [[float]],
    },
)
SWAGGER.add_parameter("debug", "query", bool)


class ScanSpecNoBackend(ScanSpec):
    """Get L1b data"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("swagger")
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ["level1"],
            ["freqmode", "scanno", "debug"],
            {"200": SWAGGER.get_type_response("L1b")},
            summary="Get level1 data for a scan",
        )

    @register_versions("fetch")
    def _get_v5(self, version, freqmode, scanno):
        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

        try:
            debug = get_args.get_bool("debug")
        except ValueError:
            abort(400)

        return self._get_v4(version, backend, freqmode, scanno, debug)

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
        datadict = run_donaletty(mjd, midlat, midlon, scanno)
        if not datadict:
            return dict()
        self._convert_items(datadict)

        datadictv4 = dict()
        datadictv4["Pressure"] = around(datadict["P"], decimals=8).tolist()
        datadictv4["Temperature"] = around(datadict["T"], decimals=3).tolist()
        datadictv4["Altitude"] = datadict["Z"]
        datadictv4["Latitude"] = datadict["latitude"]
        datadictv4["Longitude"] = datadict["longitude"]
        datadictv4["MJD"] = datadict["mjd"]
        return datadictv4

    def _convert_items(self, datadict):
        for key in ["P", "T", "Z"]:
            if key == "P":
                # convert from hPa to Pa
                datadict[key] *= 100
            if key == "Z":
                # convert from km to m
                datadict[key] *= 1000
            datadict[key] = datadict[key].tolist()

    @register_versions("return")
    def _to_return_format(self, version, datadict, *args, **kwargs):
        return datadict


SWAGGER.add_type(
    "ptz",
    {
        "Altitude": [float],
        "Latitude": float,
        "Longitude": float,
        "MJD": float,
        "Pressure": [float],
        "Temperature": [float],
    },
)


class ScanPTZNoBackend(ScanPTZ):
    """Get PTZ data"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("swagger")
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ["level1"],
            ["freqmode", "scanno"],
            {"200": SWAGGER.get_type_response("ptz")},
            summary="Get ptz data for a scan",
        )

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


SWAGGER.add_parameter(
    "aprsource", "query", str, description="Alternative apriori data source to use"
)


class ScanAPR(BaseView):
    """Get apriori data for a certain species"""

    SUPPORTED_VERSIONS = ["v4"]
    logger = logging.getLogger("odinapi").getChild(__name__)

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
        except AprioriException as err:
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


SWAGGER.add_parameter("species", "path", str)
SWAGGER.add_type(
    "apriori",
    {
        "Pressure": [float],
        "Altitude": [float],
        "Species": str,
        "VMR": [float],
    },
)


class ScanAPRNoBackend(ScanAPR):
    """Get apriori data for a certain species"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("swagger")
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ["level1"],
            ["freqmode", "scanno", "species", "aprsource"],
            {"200": SWAGGER.get_type_response("apriori")},
            summary="Get apriori data for a scan and species",
        )

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


SWAGGER.add_type("collocation", {"Instrument": str, "Species": str, "URL": str})


class CollocationsView(BaseView):
    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("swagger")
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ["level1"],
            ["freqmode", "scanno"],
            {"200": SWAGGER.get_type_response("collocation", is_list=True)},
            summary="Get collocations for a scan",
        )

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
        dedent(
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
        dedent(
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
        dedent(
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
        dedent(
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
        dedent(
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
