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
    use_agg,  # noqa: F401
)
from odinapi.utils.collocations import get_collocations
from odinapi.utils.defs import FREQMODE_TO_BACKEND, SPECIES

from odinapi.utils.time_util import datetime2mjd, mjd2stw
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


class FreqmodeInfo(MethodView):
    """loginfo for all scans from a given date and freqmode"""

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

    def get(self, version, date, backend, freqmode, scanno=None):
        """Get frequency mode info"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404

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
            return jsonify(Info=loginfo["Info"])

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

        if scanno is None:
            try:
                return jsonify(Info=loginfo["Info"])
            except TypeError:
                return jsonify(Info=[])
        else:
            for s in loginfo["Info"]:
                if s["ScanID"] == scanno:
                    return jsonify(Info=s)
            return jsonify(Info={})


class FreqmodeInfoNoBackend(MethodView):
    """loginfo for all scans from a given date and freqmode without backend"""

    LOCK = Lock()

    def __init__(self):
        import logging

        self.logger = logging.getLogger("odinapi").getChild(self.__class__.__name__)

    @classmethod
    def _acquire_lock(cls, timeout: int = 1) -> bool:
        return cls.LOCK.acquire(timeout=timeout)

    @classmethod
    def _release_lock(cls) -> None:
        cls.LOCK.release()

    def get(self, version, date, freqmode):
        """Get frequency mode info without backend"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

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
            return jsonify(Data=[], Type="Log", Count=0)

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

        data = loginfo["Info"]
        if not data:
            data = []
        return jsonify(Data=data, Type="Log", Count=len(data))


class ScanInfoNoBackend(MethodView):
    """Get scan info without backend"""

    LOCK = Lock()

    def __init__(self):
        import logging

        self.logger = logging.getLogger("odinapi").getChild(self.__class__.__name__)

    @classmethod
    def _acquire_lock(cls, timeout: int = 1) -> bool:
        return cls.LOCK.acquire(timeout=timeout)

    @classmethod
    def _release_lock(cls) -> None:
        cls.LOCK.release()

    def get(self, version, date, freqmode, scanno):
        """Get scan info without backend"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

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
            abort(404)

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

        data = loginfo["Info"]
        for s in data:
            if s["ScanID"] == scanno:
                return jsonify(Data=s, Type="Log", Count=None)
        abort(404)


class ScanSpec(MethodView):
    """Get L1b data"""

    def get(self, version, backend, freqmode, scanno, debug=False):
        """Get L1b data for a scan"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404

        spectra = get_scan_data_v2(backend, freqmode, scanno, debug)
        if spectra == {}:
            abort(404)
        # spectra is a dictionary containing the relevant data
        return jsonify(scan2dictlist_v4(spectra))


class ScanSpecNoBackend(MethodView):
    """Get L1b data"""

    def get(self, version, freqmode, scanno):
        """Get L1b data for a scan without specifying backend"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

        debug = None
        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)
        try:
            debug = get_args.get_bool("debug")
        except ValueError:
            abort(400)

        spectra = get_scan_data_v2(backend, freqmode, scanno, bool(debug))
        if spectra == {}:
            abort(404)

        data = scan2dictlist_v4(spectra)
        return jsonify(Data=data, Type="L1b", Count=None)


class ScanPTZ(MethodView):
    """Get PTZ data"""

    def get(self, version, date, backend, freqmode, scanno):
        """Get PTZ data for a scan"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404

        loginfo = get_scan_log_data(freqmode, scanno)
        if loginfo == {}:
            abort(404)
        mjd, _, midlat, midlon = get_geoloc_info(loginfo)
        ptz = get_ptz(backend, scanno, mjd, midlat, midlon)
        if not ptz:
            return jsonify({})
        return jsonify(ptz)


class ScanPTZNoBackend(MethodView):
    """Get PTZ data"""

    def get(self, version, freqmode, scanno):
        """Get PTZ data for a scan without specifying backend"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

        try:
            backend = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

        loginfo = get_scan_log_data(freqmode, scanno)
        if loginfo == {}:
            abort(404)
        mjd, _, midlat, midlon = get_geoloc_info(loginfo)
        ptz = get_ptz(backend, scanno, mjd, midlat, midlon)
        if not ptz:
            return jsonify(Data={}, Type="ptz", Count=None)
        return jsonify(Data=ptz, Type="ptz", Count=None)


class ScanAPR(MethodView):
    """Get apriori data for a certain species"""

    def __init__(self):
        import logging

        self.logger = logging.getLogger("odinapi").getChild(self.__class__.__name__)

    def get(self, version, species, date, backend, freqmode, scanno):
        """Get apriori data for a scan"""
        if version != "v4":
            return jsonify({"Error": f"Version {version} not supported, only v4"}), 404

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
        return jsonify(
            Pressure=around(datadict["pressure"], decimals=8).tolist(),
            VMR=datadict["vmr"].tolist(),
            Species=datadict["species"],
            Altitude=datadict["altitude"].tolist(),
        )


class ScanAPRNoBackend(MethodView):
    """Get apriori data for a certain species"""

    def __init__(self):
        import logging

        self.logger = logging.getLogger("odinapi").getChild(self.__class__.__name__)

    def get(self, version, freqmode, scanno, species):
        """Get apriori data for a scan without specifying backend"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

        try:
            # Validate freqmode by checking if it maps to a backend
            _ = FREQMODE_TO_BACKEND[freqmode]
        except KeyError:
            abort(404)

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

        return jsonify(
            Data={
                "Pressure": around(datadict["pressure"], decimals=8).tolist(),
                "VMR": datadict["vmr"].tolist(),
                "Species": datadict["species"],
                "Altitude": datadict["altitude"].tolist(),
            },
            Type="apriori",
            Count=None,
        )


class CollocationsView(MethodView):
    """Get collocations for a scan"""

    def get(self, version, freqmode, scanno):
        """Get L2 collocations"""
        if version != "v5":
            return jsonify({"Error": f"Version {version} not supported, only v5"}), 404

        try:
            collocations = get_L2_collocations(
                request.url_root, version, freqmode, scanno
            )
        except KeyError:
            abort(404)

        return jsonify(Data=collocations, Type="collocation", Count=len(collocations))


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


class ConfigDataFiles(MethodView):
    """display example files available to the system"""

    def get(self, version):
        """Get configuration data files"""
        data = get_config_data_files()
        return jsonify(data)
