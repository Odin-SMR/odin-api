"""Views for getting Level 2 data"""

import http.client
import logging
import urllib.parse
from datetime import datetime, timedelta
from http import HTTPStatus

import dateutil.tz
from flask import abort, jsonify, redirect, request, url_for
from flask.views import MethodView
from flask_httpauth import HTTPBasicAuth  # type: ignore
from pymongo.errors import DuplicateKeyError

import odinapi.utils.get_args as get_args
from odinapi.database import level2db
from odinapi.utils import time_util
from odinapi.utils.defs import FREQMODE_TO_BACKEND
from odinapi.utils.encrypt_util import SECRET_KEY, decode_level2_target_parameter
from odinapi.utils.jsonmodels import (
    JsonModelError,
    check_json,
    l2_prototype,
    l2i_prototype,
)
from odinapi.views.baseview import BadRequest, BaseView, register_versions
from odinapi.views.get_ancillary_data import get_ancillary_data
from odinapi.views.utils import make_rfc5988_pagination_header
from odinapi.views.views import get_L2_collocations

DEFAULT_LIMIT = 1000
DOCUMENT_LIMIT = level2db.DOCUMENT_LIMIT
DOCUMENT_LIMIT_MIN = 1000
DEFAULT_OFFSET = 0
DEFAULT_MINSCANID = 0


def is_development_request(version):
    """Return True if the endpoint targets development projects"""
    if version <= "v4":
        return None
    return "/development/" in request.path


class Level2ProjectBaseView(BaseView):
    """With version v5 and above development projects should only be
    accessible from endpoints that have '/development/' in the path.
    """

    def __init__(self, development=False, **kwargs):
        self.development = development
        super().__init__(**kwargs)

    def get(self, version, project, *args, **kwargs):
        is_dev = is_development_request(version)
        if is_dev is not None:
            projects = level2db.ProjectsDB()
            project_obj = projects.get_project(project)
            if not project_obj:
                abort(404)
            if project_obj["development"] != is_dev:
                abort(404)
        return super().get(version, project, *args, **kwargs)


def get_base_url(version):
    if is_development_request(version):
        return "{}rest_api/{}/level2/development".format(request.url_root, version)
    else:
        return "{}rest_api/{}/level2".format(request.url_root, version)


class Level2Write(MethodView):
    logger = logging.getLogger(__name__)

    def post(self, version):
        """Insert level2 data for a scan id and freq mode"""
        msg = request.args.get("d")
        if not msg:
            self.logger.warning("Level2Write.post: request message is empty")
            abort(400)
        try:
            scanid, freqmode, project = decode_level2_target_parameter(msg)
        except:  # noqa
            self.logger.warning("Level2Write.post: data can not be decoded")
            abort(400)
        data = request.json
        if not data:
            self.logger.warning("Level2Write.post: no json data")
            abort(400)
        if any(k not in data for k in ("L2", "L2I", "L2C")):
            self.logger.warning(
                "Level2Write.post: at least one of L2, L2I, or, L2C is missing"
            )
            abort(400)
        L2c = data.pop("L2C") or ""
        if not isinstance(L2c, str):
            self.logger.warning("Level2Write.post: L2c is not a string")
            abort(400)
        L2 = data.pop("L2") or []
        if isinstance(L2, dict):
            L2 = [L2]
        if not isinstance(L2, list):
            self.logger.warning("Level2Write.post: L2 is not a list")
            abort(400)
        for nr, species in enumerate(L2):
            try:
                check_json(species, prototype=l2_prototype)
            except JsonModelError as e:
                return (
                    jsonify({"error": "L2 species %d: %s" % (nr, e)}),
                    HTTPStatus.BAD_REQUEST,
                )
        L2i = data.pop("L2I") or {}
        if not isinstance(L2i, dict):
            self.logger.warning("Level2Write.post: L2I is not a dict")
            abort(400)
        if L2i:
            try:
                check_json(L2i, prototype=l2i_prototype)
            except JsonModelError as e:
                return jsonify({"error": "L2i: %s" % e}), HTTPStatus.BAD_REQUEST
            L2i["ProcessingError"] = False
        else:
            # Processing error, L2i is empty, we have to trust the provided
            # scanid and freqmode.
            L2i["ScanID"] = scanid
            L2i["FreqMode"] = freqmode
            L2i["ProcessingError"] = True
        if scanid != L2i["ScanID"]:
            self.logger.warning("Level2Write.post: scanid mismatch")
            return (
                jsonify(
                    {"error": "ScanID missmatch (%r != %r)" % (scanid, L2i["ScanID"])}
                ),
                HTTPStatus.BAD_REQUEST,
            )
        if freqmode != L2i["FreqMode"]:
            self.logger.warning("Level2Write.post: freqmode mismatch")
            return (
                jsonify(
                    {
                        "error": "FreqMode missmatch (%r != %r)"
                        % (scanid, L2i["FreqMode"])
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )
        projects = level2db.ProjectsDB()
        projects.add_project_if_not_exists(project)
        db = level2db.Level2DB(project)
        try:
            db.store(L2, L2i, L2c)
        except DuplicateKeyError:
            # DuplicateKeyError should not return an error,
            # we allow to overwrite posted level2 data,
            # if someone wants to reprocess scans we expect
            # that there is a good reason for that
            db.delete(L2i["ScanID"], L2i["FreqMode"])
            db.store(L2, L2i, L2c)
            self.logger.warning(
                "Level2Write.post: DuplicateKeyError "
                "scan data already existed in database "
                "for project={0}, FreqMode={1}, and ScanID={2} "
                "but has now been replaced".format(
                    project, L2i["FreqMode"], L2i["ScanID"]
                )
            )
        return "", HTTPStatus.CREATED

    def delete(self, version):
        """Delete level2 data for a scan id and freq mode"""
        msg = request.args.get("d")
        if not msg:
            abort(400)
        try:
            scanid, freqmode, project = decode_level2_target_parameter(msg)
        except:  # noqa
            abort(400)
        db = level2db.Level2DB(project)
        db.delete(scanid, freqmode)
        return "", HTTPStatus.NO_CONTENT


class Level2ViewProjects(BaseView):
    """Get list of existing projects"""

    @register_versions("fetch")
    def _get_projects(self, version):
        db = level2db.ProjectsDB()
        projects = db.get_projects(development=is_development_request(version))
        base_url = get_base_url(version)
        return [
            {
                "Name": p["name"],
                "URLS": {"URL-project": "{}/{}/".format(base_url, p["name"])},
            }
            for p in projects
        ]

    @register_versions("return", ["v4"])
    def _return_data(self, version, projects):
        return {"Info": {"Projects": projects}}

    @register_versions("return", ["v5"])
    def _return_data_v5(self, version, projects):
        return {"Data": projects, "Type": "level2_project", "Count": len(projects)}


class Level2ViewProject(Level2ProjectBaseView):
    """Get project information"""

    @register_versions("fetch")
    def _get_freqmodes(self, version, project):
        db = level2db.Level2DB(project)
        freqmodes = db.get_freqmodes()
        base_url = get_base_url(version)
        info = {
            "Name": project,
            "FreqModes": [
                {
                    "FreqMode": freqmode,
                    "URLS": {
                        "URL-scans": "{}/{}/{}/scans".format(
                            base_url, project, freqmode
                        ),
                        "URL-failed": "{}/{}/{}/failed".format(
                            base_url, project, freqmode
                        ),
                        "URL-comments": "{}/{}/{}/comments".format(
                            base_url, project, freqmode
                        ),
                    },
                }
                for freqmode in freqmodes
            ],
        }
        return info

    @register_versions("return", ["v4"])
    def _return(self, version, info, project):
        return {"Info": info}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, info, project):
        return {
            "Data": info["FreqModes"],
            "Type": "level2_project_freqmode",
            "Count": len(info["FreqModes"]),
        }


auth = HTTPBasicAuth()
auth.verify_password(lambda _, password: password == SECRET_KEY)


class Level2ProjectPublish(MethodView):
    @auth.login_required
    def post(self, project):
        projectsdb = level2db.ProjectsDB()
        try:
            projectsdb.publish_project(project)
        except level2db.ProjectError:
            abort(http.client.NOT_FOUND)
        return redirect(
            url_for(
                "level2_production.level2viewproject", project=project, version="v5"
            ),
            code=http.client.CREATED,
        )


class Level2ProjectAnnotations(BaseView):
    def get(self, project):  # type: ignore
        projectsdb = level2db.ProjectsDB()
        try:
            annotations = list(projectsdb.get_annotations(project))
            return jsonify(
                Data=[
                    self._annotation_to_json(annotation) for annotation in annotations
                ],
                Type="L2ProjectAnnotation",
                Count=len(annotations),
            )
        except level2db.ProjectError:
            abort(http.client.NOT_FOUND)

    def _annotation_to_json(self, annotation):
        obj = {"Text": annotation.text, "CreatedAt": annotation.created_at}
        if annotation.freqmode is not None:
            obj["FreqMode"] = annotation.freqmode
        return obj

    @auth.login_required
    def post(self, project: str):
        text: str | None = None
        freqmode: str | None = None
        if request.json:
            text = request.json.get("Text", None)
            freqmode = request.json.get("FreqMode", None)
        if text is None or not isinstance(text, str):
            abort(http.client.BAD_REQUEST)
        if freqmode is not None and not isinstance(freqmode, int):
            abort(http.client.BAD_REQUEST)
        projectsdb = level2db.ProjectsDB()
        annotation = level2db.ProjectAnnotation(
            text=text,
            created_at=datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc()),
            freqmode=freqmode,
        )
        try:
            projectsdb.add_annotation(project, annotation)
        except level2db.ProjectError:
            abort(http.client.NOT_FOUND)
        return "", http.client.CREATED


class Level2ViewComments(Level2ProjectBaseView):
    """GET list of comments for a freqmode"""

    @register_versions("fetch")
    def _fetch(self, version, project, freqmode):
        limit = get_args.get_int("limit") or DEFAULT_LIMIT
        offset = get_args.get_int("offset") or DEFAULT_OFFSET
        db = level2db.Level2DB(project)
        comments = db.get_comments(freqmode, offset=offset, limit=limit)
        base_url = get_base_url(version)
        info = {
            "Comments": [
                {
                    "Comment": comment,
                    "URLS": {
                        "URL-scans": "{}/{}/{}/scans?{}".format(
                            base_url,
                            project,
                            freqmode,
                            urllib.parse.urlencode([("comment", comment)]),
                        ),
                        "URL-failed": "{}/{}/{}/failed?{}".format(
                            base_url,
                            project,
                            freqmode,
                            urllib.parse.urlencode([("comment", comment)]),
                        ),
                    },
                }
                for comment in comments
            ]
        }
        count = db.count_comments(freqmode)
        data = {
            "info": info,
            "count": count,
        }
        headers = {
            "Link": make_rfc5988_pagination_header(
                offset,
                limit,
                count,
                self._get_endpoint(),
                version=version,
                project=project,
                freqmode=freqmode,
            ),
        }
        return data, HTTPStatus.OK, headers

    def _get_endpoint(self):
        return (
            "level2_development.level2devviewcomments"
            if self.development
            else "level2_production.level2viewcomments"
        )

    @register_versions("return", ["v4"])
    def _return(self, version, data, project, freqmode):
        return {"Info": data["info"]}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, data, project, freqmode):
        return {
            "Data": data["info"]["Comments"],
            "Type": "level2_scan_comment",
            "Count": data["count"],
        }


class Level2ViewScans(Level2ProjectBaseView):
    """GET list of matching scans"""

    @register_versions("fetch")
    def _fetch(self, version, project, freqmode):
        start_time = get_args.get_datetime("start_time")
        end_time = get_args.get_datetime("end_time")
        limit = get_args.get_int("limit") or DEFAULT_LIMIT
        offset = get_args.get_int("offset") or DEFAULT_OFFSET
        if start_time and end_time and start_time > end_time:
            abort(400)
        param = {
            "start_time": start_time,
            "end_time": end_time,
            "comment": get_args.get_string("comment"),
        }
        db = level2db.Level2DB(project)
        scans = list(db.get_scans(freqmode, limit=limit, offset=offset, **param))
        for scan in scans:
            scan["Date"] = time_util.stw2datetime(scan["ScanID"]).isoformat()
            scan["URLS"] = get_scan_urls(version, project, freqmode, scan["ScanID"])
        count = db.count_scans(freqmode, **param)
        data = {
            "scans": scans,
            "count": count,
        }
        headers = {
            "Link": make_rfc5988_pagination_header(
                offset,
                limit,
                count,
                self._get_endpoint(),
                version=version,
                project=project,
                freqmode=freqmode,
                **param,
            )
        }
        return data, HTTPStatus.OK, headers

    def _get_endpoint(self):
        return (
            "level2_development.level2devviewscans"
            if self.development
            else "level2_production.level2viewscans"
        )

    @register_versions("return", ["v4"])
    def _return(self, version, data, project, freqmode):
        return {"Info": {"Count": data["count"], "Scans": data["scans"]}}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, data, project, freqmode):
        return {
            "Data": data["scans"],
            "Type": "level2_scan_info",
            "Count": data["count"],
        }


class Level2ViewFailedScans(Level2ProjectBaseView):
    """GET list of matching scans that failed the level2 processing"""

    @register_versions("fetch")
    def _fetch(self, version, project, freqmode):
        start_time = get_args.get_datetime("start_time")
        end_time = get_args.get_datetime("end_time")
        limit = get_args.get_int("limit") or DEFAULT_LIMIT
        offset = get_args.get_int("offset") or DEFAULT_OFFSET
        if start_time and end_time and start_time > end_time:
            abort(400)
        param = {
            "start_time": start_time,
            "end_time": end_time,
            "comment": get_args.get_string("comment"),
        }
        db = level2db.Level2DB(project)
        scans = list(db.get_failed_scans(freqmode, offset=offset, limit=limit, **param))
        for scan in scans:
            scan["URLS"] = get_scan_urls(version, project, freqmode, scan["ScanID"])
            scan["Error"] = scan.pop("Comments")[0]
            scan["Date"] = time_util.stw2datetime(scan["ScanID"]).date().isoformat()
        count = db.count_failed_scans(freqmode, **param)
        data = {
            "scans": scans,
            "count": count,
        }
        headers = {
            "Link": make_rfc5988_pagination_header(
                offset,
                limit,
                count,
                self._get_endpoint(),
                version=version,
                project=project,
                freqmode=freqmode,
                **param,
            ),
        }
        return data, HTTPStatus.OK, headers

    def _get_endpoint(self):
        return (
            "level2_development.level2devviewfailed"
            if self.development
            else "level2_production.level2viewfailed"
        )

    @register_versions("return", ["v4"])
    def _return(self, version, data, project, freqmode):
        return {"Info": {"Count": data["count"], "Scans": data["scans"]}}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, data, project, freqmode):
        return {
            "Data": data["scans"],
            "Type": "level2_failed_scan_info",
            "Count": data["count"],
        }


class Level2ViewScan(Level2ProjectBaseView):
    """GET level2 data, info and comments for one scan and freqmode"""

    @register_versions("fetch")
    def _fetch(self, version, project, freqmode, scanno):
        db = level2db.Level2DB(project)
        L2i, L2, L2c = db.get_scan(freqmode, scanno)
        if not L2i:
            abort(404)
        urls = get_scan_urls(version, project, freqmode, scanno)
        info = {"L2": L2, "L2i": L2i, "L2c": L2c, "URLS": urls}
        if version <= "v4":
            collocations = get_L2_collocations(
                request.url_root, version, freqmode, scanno
            )
            info["Collocations"] = collocations
        if version >= "v5":
            if not L2:
                abort(404)
            info["L2anc"] = get_ancillary_data(info["L2"])
        return info

    @register_versions("return", ["v4"])
    def _return(self, version, info, project, freqmode, scanno):
        return {"Info": info}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, info, project, freqmode, scanno):
        L2i = info["L2i"]
        L2i["URLS"] = info["URLS"]
        data = {
            "L2i": {"Data": L2i, "Type": "L2i", "Count": None},
            "L2": {"Data": info["L2"], "Type": "L2", "Count": len(info["L2"])},
            "L2c": {"Data": info["L2c"], "Type": "L2c", "Count": len(info["L2c"])},
            "L2anc": {
                "Data": info["L2anc"],
                "Type": "L2anc",
                "Count": len(info["L2anc"]),
            },
        }
        mixed = {"Data": data, "Type": "mixed", "Count": None}
        return mixed


class L2iView(Level2ProjectBaseView):
    """Get level2 info for one scan and freqmode"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get(self, version, project, freqmode, scanno):
        db = level2db.Level2DB(project)
        L2i = db.get_L2i(freqmode, scanno)
        if not L2i:
            abort(404)
        L2i["URLS"] = get_scan_urls(version, project, freqmode, scanno)
        return L2i

    @register_versions("return")
    def _return(self, version, L2i, project, freqmode, scanno):
        return {"Data": L2i, "Type": "L2i", "Count": None}


class L2cView(Level2ProjectBaseView):
    """Get level2 comments for one scan and freqmode"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get(self, version, project, freqmode, scanno):
        db = level2db.Level2DB(project)
        L2c = db.get_L2c(freqmode, scanno)
        if not L2c:
            abort(404)
        return L2c

    @register_versions("return")
    def _return(self, version, L2c, project, freqmode, scanno):
        return {"Data": L2c, "Type": "L2c", "Count": len(L2c)}


class L2ancView(Level2ProjectBaseView):
    """Get ancillary data for one scan and freqmode"""

    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get(self, version, project, freqmode, scanno):
        product = get_args.get_string("product")
        db = level2db.Level2DB(project)
        L2 = db.get_L2(freqmode, scanno, product=product)
        if not L2:
            abort(404)
        L2anc = get_ancillary_data(L2)
        return L2anc

    @register_versions("return")
    def _return(self, version, L2anc, project, freqmode, scanno):
        return {"Data": L2anc, "Type": "L2anc", "Count": len(L2anc)}


class L2View(Level2ProjectBaseView):
    """Get level2 data for one scan and freqmode"""

    # TODO: Choose if AVK should be included
    SUPPORTED_VERSIONS = ["v5"]

    @register_versions("fetch")
    def _get(self, version, project, freqmode, scanno):
        product = get_args.get_string("product")
        db = level2db.Level2DB(project)
        L2 = db.get_L2(freqmode, scanno, product=product)
        if not L2:
            abort(404)
        return L2

    @register_versions("return")
    def _return(self, version, L2, project, freqmode, scanno):
        return {"Data": L2, "Type": "L2", "Count": len(L2)}


def get_scan_urls(version, project, freqmode, scanno):
    try:
        backend = FREQMODE_TO_BACKEND[freqmode]
    except KeyError:
        abort(404)
    if version <= "v4":
        return {
            "URL-log": "{0}rest_api/{1}/l1_log/{2}/{3}/".format(
                request.url_root, version, freqmode, scanno
            ),
            "URL-level2": "{0}/{1}/{2}/{3}/".format(
                get_base_url(version), project, freqmode, scanno
            ),
            "URL-spectra": "{0}rest_api/{1}/scan/{2}/{3}/{4}/".format(
                request.url_root, version, backend, freqmode, scanno
            ),
        }
    else:
        return {
            "URL-log": "{0}rest_api/{1}/level1/{2}/{3}/Log/".format(
                request.url_root, version, freqmode, scanno
            ),
            "URL-level2": ("{0}/{1}/{2}/{3}/").format(
                get_base_url(version), project, freqmode, scanno
            ),
            "URL-spectra": "{0}rest_api/{1}/level1/{2}/{3}/L1b/".format(
                request.url_root, version, freqmode, scanno
            ),
            "URL-ancillary": ("{0}/{1}/{2}/{3}/L2anc").format(
                get_base_url(version), project, freqmode, scanno
            ),
        }


class Level2ViewProducts(Level2ProjectBaseView):
    """GET available products"""

    @register_versions("fetch", ["v4"])
    def _get(self, version, project):
        db = level2db.Level2DB(project)
        return db.get_product_count()

    @register_versions("return", ["v4"])
    def _return(self, version, products, project):
        return {"Info": {"Products": products}}

    @register_versions("fetch", ["v5"])
    def _get_v5(self, version, project):
        db = level2db.Level2DB(project)
        return db.get_products(freqmode=None)

    @register_versions("return", ["v5"])
    def _return_v5(self, version, products, project):
        return {"Data": products, "Type": "level2_product_name", "Count": len(products)}


class Level2ViewProductsFreqmode(Level2ProjectBaseView):
    """GET available products"""

    @register_versions("fetch", ["v4"])
    def _get(self, version, project, freqmode):
        db = level2db.Level2DB(project)
        return db.get_products(freqmode=int(freqmode))

    @register_versions("return", ["v4"])
    def _return(self, version, products, project, freqmode):
        return {"Info": {"Products": products}}

    @register_versions("fetch", ["v5"])
    def _get_v5(self, version, project, freqmode):
        db = level2db.Level2DB(project)
        return db.get_products(freqmode=int(freqmode))

    @register_versions("return", ["v5"])
    def _return_v5(self, version, products, project, freqmode):
        return {"Data": products, "Type": "level2_product_name", "Count": len(products)}


class Level2ViewLocations(Level2ProjectBaseView):
    """GET data close to provided locations.

    Provide one or more locations and a radius to get data within the
    resulting circles on the earth surface.

    Choose between min/max altitude and min/max pressure.

    Example query:

        product=p1&product=p2&min_pressure=100&max_pressure=1000&
        start_time=2015-10-11&end_time=2016-02-20&radius=100&
        location=-24.0,200.0&location=-30.0,210.0
    """

    @register_versions("fetch")
    def _fetch(self, version, project):
        if not get_args.get_list("location"):
            raise BadRequest("No locations specified")
        try:
            param = parse_parameters()
        except ValueError as err:
            raise BadRequest(str(err))
        db = level2db.Level2DB(project)
        limit = param.pop("document_limit")
        meas_iter = db.get_measurements(param.pop("products"), limit, **param)
        if version == "v4":
            return meas_iter
        scans, next_min_scanid = level2db.get_valid_collapsed_products(
            list(meas_iter), limit
        )
        headers = {}
        if next_min_scanid is not None:
            link = get_level2view_paging_links(
                request.url, param["min_scanid"], next_min_scanid
            )
            headers = {"link": link}
        return scans, HTTPStatus.OK, headers

    @register_versions("return", ["v4"])
    def _return(self, version, results, _):
        results = list(results)
        return {"Info": {"Nr": len(results), "Results": results}}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, results, _):
        return {"Data": results, "Type": "L2", "Count": len(results)}


class Level2ViewDay(Level2ProjectBaseView):
    """Get data for a certain day

    Choose between min/max altitude and min/max pressure.

    Example query:

        product=p1&product=p2&min_pressure=1000&max_pressure=1000
    """

    @register_versions("fetch")
    def _fetch(self, version, project, date):
        try:
            start_time = get_args.get_datetime(val=date)
        except ValueError:
            abort(400)
        if start_time is None:
            abort(400)
        end_time = start_time + timedelta(hours=24)
        try:
            param = parse_parameters(start_time=start_time, end_time=end_time)
        except ValueError as e:
            return jsonify({"Error": str(e)})
        db = level2db.Level2DB(project)
        limit = param.pop("document_limit")
        meas_iter = db.get_measurements(param.pop("products"), limit, **param)
        if version == "v4":
            return meas_iter
        scans, next_min_scanid = level2db.get_valid_collapsed_products(
            list(meas_iter), limit
        )
        headers = {}
        if next_min_scanid is not None:
            link = get_level2view_paging_links(
                request.url, param["min_scanid"], next_min_scanid
            )
            headers = {"link": link}
        return scans, HTTPStatus.OK, headers

    @register_versions("return", ["v4"])
    def _return(self, version, results, *args, **kwargs):
        results = list(results)
        return {"Info": {"Nr": len(results), "Results": results}}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, results, *args, **kwargs):
        return {"Data": results, "Type": "L2", "Count": len(results)}


class Level2ViewArea(Level2ProjectBaseView):
    """Get data for a certain area

    Provide latitude and/or longitude limits to get data for a certain
    area of the earth.

    If no latitude or longitude limits are provided, data for the whole
    earth is returned.

    Choose between min/max altitude and min/max pressure.

    Example url parameters:

        product=p1&product=p2&min_pressure=100&max_pressure=100&
        start_time=2015-10-11&end_time=2016-02-20&min_lat=-80&
        max_lat=-70&min_lon=150&max_lon=200
    """

    @register_versions("fetch")
    def _fetch(self, version, project):
        try:
            param = parse_parameters()
        except ValueError as e:
            raise BadRequest(str(e))

        db = level2db.Level2DB(project)
        limit = param.pop("document_limit")
        meas_iter = db.get_measurements(param.pop("products"), limit, **param)
        if version == "v4":
            return meas_iter
        scans, next_min_scanid = level2db.get_valid_collapsed_products(
            list(meas_iter), limit
        )
        headers = {}
        if next_min_scanid is not None:
            link = get_level2view_paging_links(
                request.url, param["min_scanid"], next_min_scanid
            )
            headers = {"link": link}
        return scans, HTTPStatus.OK, headers

    @register_versions("return", ["v4"])
    def _return(self, version, results, _):
        results = list(results)
        return {"Info": {"Nr": len(results), "Results": results}}

    @register_versions("return", ["v5"])
    def _return_v5(self, version, results, _):
        return {"Data": results, "Type": "L2", "Count": len(results)}


def parse_parameters(**kwargs):
    """Parse parameters coming from the request"""
    products = get_args.get_list("product")

    # Altitude or pressure
    min_pressure = get_args.get_float("min_pressure", kwargs.get("min_pressure"))
    max_pressure = get_args.get_float("max_pressure", kwargs.get("max_pressure"))
    if min_pressure and max_pressure and min_pressure > max_pressure:
        raise ValueError("Min pressure must not be larger than max pressure")

    min_altitude = get_args.get_float("min_altitude", kwargs.get("min_altitude"))
    max_altitude = get_args.get_float("max_altitude", kwargs.get("max_altitude"))
    if min_altitude and max_altitude and min_altitude > max_altitude:
        raise ValueError("Min altitude must not be larger than max altitude")

    if (min_pressure or max_pressure) and (min_altitude or max_altitude):
        raise ValueError(
            "Not supported to filter by altitude and pressure at the same time"
        )

    # Time
    start_time = get_args.get_datetime("start_time", kwargs.get("start_time"))
    end_time = get_args.get_datetime("end_time", kwargs.get("end_time"))
    if start_time and end_time and start_time > end_time:
        raise ValueError("Start time must not be after end time")

    if not (
        any([min_pressure, max_pressure, min_altitude, max_altitude])
        and any([start_time, end_time])
    ):
        raise ValueError(
            "Too broad query, you must provide at least one of pressure or "
            "altitude max/min, and at least one of start_time and "
            "end_time."
        )

    # Geographic
    radius = get_args.get_float("radius")
    locations = get_args.get_list("location") or []
    if locations and not radius:
        raise ValueError("Missing parameter radius")
    circles = [loc.split(",") + [radius] for loc in locations]
    circles = [level2db.GeographicCircle(*c) for c in circles]

    area = [
        get_args.get_string(arg) for arg in ["min_lat", "max_lat", "min_lon", "max_lon"]
    ]

    if circles and any(area):
        raise ValueError(
            ("Not supported to filter both by locations and area at the same time")
        )
    if any(area):
        area = level2db.GeographicArea(*area)
    else:
        area = None

    # Fields to return
    fields = get_args.get_list("field")

    # Limit
    document_limit = max(
        get_args.get_int("document_limit") or DOCUMENT_LIMIT, DOCUMENT_LIMIT_MIN
    )

    # Offset in scanid
    min_scanid = get_args.get_int("min_scanid") or DEFAULT_MINSCANID

    return {
        "products": products,
        "min_pressure": min_pressure,
        "max_pressure": max_pressure,
        "min_altitude": min_altitude,
        "max_altitude": max_altitude,
        "start_time": start_time,
        "end_time": end_time,
        "areas": circles or area,
        "fields": fields,
        "document_limit": document_limit,
        "min_scanid": min_scanid,
    }


def get_level2view_paging_links(url, current_min_scanid, next_min_scanid):
    if "min_scanid" in url:
        first_link = url.replace(f"min_scanid={current_min_scanid}", "min_scanid=0")
        next_link = url.replace(
            f"min_scanid={current_min_scanid}", f"min_scanid={next_min_scanid}"
        )
    else:
        first_link = f"{url}&min_scanid=0"
        next_link = f"{url}&min_scanid={next_min_scanid}"
    return f'<{first_link}>; rel="first", <{next_link}>; rel="next"'
