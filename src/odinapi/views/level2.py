# pylint: skip-file
"""Views for getting Level 2 data"""
import urllib
from datetime import timedelta
from operator import itemgetter
from itertools import groupby

from flask import request, abort, jsonify
from flask.views import MethodView

from pymongo.errors import DuplicateKeyError

from odinapi.utils.encrypt_util import decode_level2_target_parameter
from odinapi.utils.jsonmodels import (
    l2_prototype, l2i_prototype, check_json, JsonModelError)
from odinapi.utils.defs import FREQMODE_TO_BACKEND
from odinapi.utils import time_util

from odinapi.views import level2db
from odinapi.views.views import get_L2_collocations
from odinapi.views.baseview import BaseView, register_versions, BadRequest
from odinapi.utils.swagger import SWAGGER
import odinapi.utils.get_args as get_args

SWAGGER.add_response('Level2BadQuery', "Unsupported query", {"Error": str})

SWAGGER.add_parameter('project', 'path', str)
SWAGGER.add_parameter(
    'radius', 'query', float, required=True,
    description=(
        "Return data within this radius from the provided locations (km).")
)
SWAGGER.add_parameter(
    'location', 'query', [str], required=True, collection_format="multi",
    description=(
        "Return data close to these locations (lat,lon). "
        "Example location: '-10.1,300.3'.")
)
SWAGGER.add_parameter(
    'min_lat', 'query', float, description="Min latitude (-90 to 90).")
SWAGGER.add_parameter(
    'max_lat', 'query', float, description="Max latitude (-90 to 90).")
SWAGGER.add_parameter(
    'min_lon', 'query', float, description="Min longitude (0 to 360).")
SWAGGER.add_parameter(
    'max_lon', 'query', float, description="Max longitude (0 to 360).")
SWAGGER.add_parameter(
    'product', 'query', [str], collection_format='multi',
    description="Return data only for these products.")
SWAGGER.add_parameter(
    'min_pressure', 'query', float, description="Min pressure (Pa).")
SWAGGER.add_parameter(
    'max_pressure', 'query', float, description="Max pressure (Pa).")
SWAGGER.add_parameter(
    'min_altitude', 'query', float, description="Min altitude (m).")
SWAGGER.add_parameter(
    'max_altitude', 'query', float, description="Max altitude (m).")
SWAGGER.add_parameter(
    'comment', 'query', str, description="Return scans with this comment.")


def is_development_request(version):
    """Return True if the endpoint targets development projects"""
    if version <= 'v4':
        return None
    return '/development/' in request.path


class Level2ProjectBaseView(BaseView):
    """With version v5 and above development projects should only be
    accessible from endpoints that have '/development/' in the path.
    """

    def get(self, version, project, *args, **kwargs):
        is_dev = is_development_request(version)
        if is_dev is not None:
            projects = level2db.ProjectsDB()
            project_obj = projects.get_project(project)
            if not project_obj:
                abort(404)
            if project_obj['development'] != is_dev:
                abort(404)
        return super(Level2ProjectBaseView, self).get(
            version, project, *args, **kwargs)


def get_base_url(version):
    if is_development_request(version):
        return '{}rest_api/{}/level2/development'.format(
            request.url_root, version)
    else:
        return '{}rest_api/{}/level2'.format(
            request.url_root, version)


class Level2Write(MethodView):

    def post(self, version):
        """Insert level2 data for a scan id and freq mode"""
        msg = request.args.get('d')
        if not msg:
            abort(400)
        try:
            scanid, freqmode, project = decode_level2_target_parameter(msg)
        except:
            abort(400)
        data = request.json
        if not data:
            abort(400)
        if any(k not in data for k in ('L2', 'L2I', 'L2C')):
            abort(400)
        L2c = data.pop('L2C') or ''
        if not isinstance(L2c, basestring):
            abort(400)
        L2 = data.pop('L2') or []
        if not isinstance(L2, list):
            abort(400)
        for nr, species in enumerate(L2):
            try:
                check_json(species, prototype=l2_prototype)
            except JsonModelError as e:
                return jsonify(
                    {'error': 'L2 species %d: %s' % (nr, e)}), 400
        L2i = data.pop('L2I') or {}
        if not isinstance(L2i, dict):
            abort(400)
        if L2i:
            try:
                check_json(L2i, prototype=l2i_prototype)
            except JsonModelError as e:
                return jsonify({'error': 'L2i: %s' % e}), 400
            L2i['ProcessingError'] = False
        else:
            # Processing error, L2i is empty, we have to trust the provided
            # scanid and freqmode.
            L2i['ScanID'] = scanid
            L2i['FreqMode'] = freqmode
            L2i['ProcessingError'] = True
        if scanid != L2i['ScanID']:
            return jsonify(
                {'error': 'ScanID missmatch (%r != %r)' % (
                    scanid, L2i['ScanID'])}), 400
        if freqmode != L2i['FreqMode']:
            return jsonify(
                {'error': 'FreqMode missmatch (%r != %r)' % (
                    scanid, L2i['FreqMode'])}), 400
        projects = level2db.ProjectsDB()
        projects.add_project_if_not_exists(project)
        db = level2db.Level2DB(project)
        try:
            db.store(L2, L2i, L2c)
        except DuplicateKeyError:
            return jsonify(
                {'error': ('Level2 data for this scan id and freq mode '
                           'already exist')}), 400
        return '', 201

    def delete(self, version):
        """Delete level2 data for a scan id and freq mode"""
        msg = request.args.get('d')
        if not msg:
            abort(400)
        try:
            scanid, freqmode, project = decode_level2_target_parameter(msg)
        except:
            abort(400)
        db = level2db.Level2DB(project)
        db.delete(scanid, freqmode)
        return '', 204


SWAGGER.add_type('level2_project', {
    "Name": str,
    "FreqModes": [{
        "FreqMode": int,
        "URLS": {
            "URL-project": str,
        }
    }]
})


class Level2ViewProjects(BaseView):
    """Get list of existing projects"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version'],
            {"200": SWAGGER.get_type_response('level2_project', is_list=True)},
            summary="Get list of existing projects"
        )

    @register_versions('fetch')
    def _get_projects(self, version):
        db = level2db.ProjectsDB()
        projects = db.get_projects(development=is_development_request(version))
        base_url = get_base_url(version)
        return [{
            'Name': p['name'],
            'URLS': {
                'URL-project': '{}/{}/'.format(base_url, p['name'])
            }} for p in projects]

    @register_versions('return', ['v4'])
    def _return_data(self, version, projects):
        return {'Info': {'Projects': projects}}

    @register_versions('return', ['v5'])
    def _return_data_v5(self, version, projects):
        return {'Data': projects, 'Type': 'level2_project',
                'Count': len(projects)}


SWAGGER.add_type('level2_project_freqmode', {
    "FreqMode": int,
    "URLS": {
        "URL-scans": str,
        "URL-failed": str,
        "URL-comment": str
    }
})


class Level2ViewProject(Level2ProjectBaseView):
    """Get project information"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project'],
            {"200": SWAGGER.get_type_response('level2_project_freqmode')},
            summary="Get project information"
        )

    @register_versions('fetch')
    def _get_freqmodes(self, version, project):
        db = level2db.Level2DB(project)
        freqmodes = db.get_freqmodes()
        base_url = get_base_url(version)
        info = {
            'Name': project,
            'FreqModes': [{
                'FreqMode': freqmode,
                'URLS': {
                    'URL-scans': '{}/{}/{}/scans'.format(
                        base_url, project, freqmode),
                    'URL-failed': '{}/{}/{}/failed'.format(
                        base_url, project, freqmode),
                    'URL-comments': '{}/{}/{}/comments'.format(
                        base_url, project, freqmode)
                }} for freqmode in freqmodes]}
        return info

    @register_versions('return', ['v4'])
    def _return(self, version, info, project):
        return {'Info': info}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, info, project):
        return {
            'Data': info['FreqModes'],
            'Type': 'level2_project_freqmode',
            'Count': len(info['FreqModes'])
        }


SWAGGER.add_type('level2_scan_comment', {
    "Comment": str,
    "URLS": {
        "URL-scans": str,
        "URL-failed": str
    }
})


class Level2ViewComments(Level2ProjectBaseView):
    """GET list of comments for a freqmode"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode'],
            {"200": SWAGGER.get_type_response(
                'level2_scan_comment', is_list=True)},
            summary="Get list of comments for a freqmode"
        )

    @register_versions('fetch')
    def _fetch(self, version, project, freqmode):
        db = level2db.Level2DB(project)
        comments = db.get_comments(freqmode)
        base_url = get_base_url(version)
        info = {
            'Comments': [{
                'Comment': comment,
                'URLS': {
                    'URL-scans': '{}/{}/{}/scans?{}'.format(
                        base_url, project, freqmode,
                        urllib.urlencode([('comment', comment)])),
                    'URL-failed': '{}/{}/{}/failed?{}'.format(
                        base_url, project, freqmode,
                        urllib.urlencode([('comment', comment)]))
                }
            } for comment in comments]
        }
        return info

    @register_versions('return', ['v4'])
    def _return(self, version, info, project, freqmode):
        return {'Info': info}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, info, project, freqmode):
        return {
            'Data': info['Comments'],
            'Type': 'level2_scan_comment',
            'Count': len(info['Comments'])}


SWAGGER.add_type('level2_scan_info', {
    "ScanID": int,
    "Date": str,
    "URLS": {
        "URL-level2": str,
        "URL-spectra": str,
        "URL-log": str,
    }
})


class Level2ViewScans(Level2ProjectBaseView):
    """GET list of matching scans"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode', 'start_time', 'end_time',
             'comment'],
            {"200": SWAGGER.get_type_response(
                'level2_scan_info', is_list=True)},
            summary="Get list of matching scans"
        )

    @register_versions('fetch')
    def _fetch(self, version, project, freqmode):
        start_time = get_args.get_datetime('start_time')
        end_time = get_args.get_datetime('end_time')
        if start_time and end_time and start_time > end_time:
            abort(400)
        param = {
            'start_time': start_time,
            'end_time': end_time,
            'comment': get_args.get_string('comment')}
        db = level2db.Level2DB(project)
        scans = list(db.get_scans(freqmode, **param))
        for scan in scans:
            scan['Date'] = time_util.stw2datetime(
                scan['ScanID']).date().isoformat()
            scan['URLS'] = get_scan_urls(
                version, project, freqmode, scan['ScanID'])
        return scans

    @register_versions('return', ['v4'])
    def _return(self, version, scans, project, freqmode):
        return {'Info': {'Count': len(scans), 'Scans': scans}}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, scans, project, freqmode):
        return {'Data': scans, 'Type': 'level2_scan_info', 'Count': len(scans)}


SWAGGER.add_type('level2_failed_scan_info', {
    "ScanID": int,
    "Date": str,
    "Error": str,
    "URLS": {
        "URL-level2": str,
        "URL-spectra": str,
        "URL-log": str,
    }
})


class Level2ViewFailedScans(Level2ProjectBaseView):
    """GET list of matching scans that failed the level2 processing"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode', 'start_time', 'end_time',
             'comment'],
            {"200": SWAGGER.get_type_response(
                'level2_failed_scan_info', is_list=True)},
            summary=(
                "Get list of matching scans that failed the level2 processing")
        )

    @register_versions('fetch')
    def _fetch(self, version, project, freqmode):
        start_time = get_args.get_datetime('start_time')
        end_time = get_args.get_datetime('end_time')
        if start_time and end_time and start_time > end_time:
            abort(400)
        param = {
            'start_time': start_time,
            'end_time': end_time,
            'comment': get_args.get_string('comment')}
        db = level2db.Level2DB(project)
        scans = list(db.get_failed_scans(freqmode, **param))
        for scan in scans:
            scan['URLS'] = get_scan_urls(
                version, project, freqmode, scan['ScanID'])
            scan['Error'] = scan.pop('Comments')[0]
            scan['Date'] = time_util.stw2datetime(
                scan['ScanID']).date().isoformat()
        return scans

    @register_versions('return', ['v4'])
    def _return(self, version, scans, project, freqmode):
        return {'Info': {'Count': len(scans), 'Scans': scans}}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, scans, project, freqmode):
        return {'Data': scans, 'Type': 'level2_failed_scan_info',
                'Count': len(scans)}


class Level2ViewScan(Level2ProjectBaseView):
    """GET level2 data, info and comments for one scan and freqmode"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode', 'scanno'],
            {"200": SWAGGER.get_mixed_type_response(
                [('L2', True), ('L2i', False), ('L2c', True)])},
            summary=(
                "Get level2 data, info and comments for one scan and freqmode")
        )

    @register_versions('fetch')
    def _fetch(self, version, project, freqmode, scanno):
        db = level2db.Level2DB(project)
        L2i, L2, L2c = db.get_scan(freqmode, scanno)
        if not L2i:
            abort(404)
        urls = get_scan_urls(version, project, freqmode, scanno)
        info = {'L2': L2, 'L2i': L2i, 'L2c': L2c, 'URLS': urls}
        if version <= 'v4':
            collocations = get_L2_collocations(
                request.url_root, version, freqmode, scanno)
            info['Collocations'] = collocations
        return info

    @register_versions('return', ['v4'])
    def _return(self, version, info, project, freqmode, scanno):
        return {'Info': info}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, info, project, freqmode, scanno):
        L2i = info['L2i']
        L2i['URLS'] = info['URLS']
        data = {
            'L2i': {'Data': L2i, 'Type': 'L2i', 'Count': None},
            'L2': {'Data': info['L2'], 'Type': 'L2', 'Count': len(info['L2'])},
            'L2c': {
                'Data': info['L2c'], 'Type': 'L2c', 'Count': len(info['L2c'])},
        }
        return {'Data': data, 'Type': 'mixed',
                'Count': None}


SWAGGER.add_type('L2i', {
    "InvMode": str,
    "FreqMode": int,
    "ScanID": int,
    "ChannelsID": [int],
    "STW": [int],
    "FreqOffset": float,
    "MinLmFactor": float,
    "PointOffset": float,
    "Residual": float,
    "LOFreq": [float],
    "BlineOffset": [[float]],
    "FitSpectrum": [[float]],
})


class L2iView(Level2ProjectBaseView):
    """Get level2 info for one scan and freqmode"""
    SUPPORTED_VERSIONS = ['v5']

    @register_versions('swagger')
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode', 'scanno'],
            {"200": SWAGGER.get_type_response('L2i')},
            summary=(
                "Get level2 info for one scan and freqmode")
        )

    @register_versions('fetch')
    def _get(self, version, project, freqmode, scanno):
        db = level2db.Level2DB(project)
        L2i = db.get_L2i(freqmode, scanno)
        if not L2i:
            abort(404)
        L2i['URLS'] = get_scan_urls(version, project, freqmode, scanno)
        return L2i

    @register_versions('return')
    def _return(self, version, L2i, project, freqmode, scanno):
        return {'Data': L2i, 'Type': 'L2i', 'Count': None}


SWAGGER.add_type('L2c', str)


class L2cView(Level2ProjectBaseView):
    """Get level2 comments for one scan and freqmode"""
    SUPPORTED_VERSIONS = ['v5']

    @register_versions('swagger')
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode', 'scanno'],
            {"200": SWAGGER.get_type_response('L2c', is_list=True)},
            summary=(
                "Get level2 comments for one scan and freqmode")
        )

    @register_versions('fetch')
    def _get(self, version, project, freqmode, scanno):
        db = level2db.Level2DB(project)
        L2c = db.get_L2c(freqmode, scanno)
        if not L2c:
            abort(404)
        return L2c

    @register_versions('return')
    def _return(self, version, L2c, project, freqmode, scanno):
        return {'Data': L2c, 'Type': 'L2c', 'Count': len(L2c)}


SWAGGER.add_type('L2', {
    "Product": str,
    "InvMode": str,
    "FreqMode": int,
    "ScanID": int,
    "MJD": float,
    "Lat1D": float,
    "Lon1D": float,
    "Quality": float,
    "Altitude": [float],
    "Pressure": [float],
    "Latitude": [float],
    "Longitude": [float],
    "Temperature": [float],
    "ErrorTotal": [float],
    "ErrorNoise": [float],
    "MeasResponse": [float],
    "Apriori": [float],
    "VMR": [float],
    "AVK": [[float]],
})


class L2View(Level2ProjectBaseView):
    """Get level2 data for one scan and freqmode"""
    # TODO: Choose if AVK should be included
    SUPPORTED_VERSIONS = ['v5']

    @register_versions('swagger')
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode', 'scanno', 'product'],
            {"200": SWAGGER.get_type_response('L2', is_list=True)},
            summary=(
                "Get level2 data for one scan and freqmode")
        )

    @register_versions('fetch')
    def _get(self, version, project, freqmode, scanno):
        product = get_args.get_string('product')
        db = level2db.Level2DB(project)
        L2 = db.get_L2(freqmode, scanno, product=product)
        if not L2:
            abort(404)
        return L2

    @register_versions('return')
    def _return(self, version, L2, project, freqmode, scanno):
        return {'Data': L2, 'Type': 'L2', 'Count': len(L2)}


def get_scan_urls(version, project, freqmode, scanno):
    try:
        backend = FREQMODE_TO_BACKEND[freqmode]
    except KeyError:
        abort(404)
    if version <= 'v4':
        return {
            'URL-log': '{0}rest_api/{1}/l1_log/{2}/{3}/'.format(
                request.url_root, version, freqmode, scanno),
            'URL-level2': '{0}/{1}/{2}/{3}/'.format(
                get_base_url(version), project, freqmode, scanno),
            'URL-spectra': '{0}rest_api/{1}/scan/{2}/{3}/{4}/'.format(
                request.url_root, version, backend, freqmode, scanno)
        }
    else:
        return {
            'URL-log': '{0}rest_api/{1}/level1/{2}/{3}/Log/'.format(
                request.url_root, version, freqmode, scanno),
            'URL-level2': (
                '{0}/{1}/{2}/{3}/').format(
                    get_base_url(version), project, freqmode, scanno),
            'URL-spectra': '{0}rest_api/{1}/level1/{2}/{3}/L1b/'.format(
                request.url_root, version, freqmode, scanno)
        }


SWAGGER.add_type('level2_product_name', str)


class Level2ViewProducts(Level2ProjectBaseView):
    """GET available products"""

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'freqmode'],
            {"200": SWAGGER.get_type_response(
                'level2_product_name', is_list=True)},
            summary=(
                "Get available products")
        )

    @register_versions('fetch', ['v4'])
    def _get(self, version, project, freqmode=None):
        if freqmode:
            abort(404)
        db = level2db.Level2DB(project)
        return db.get_product_count()

    @register_versions('return', ['v4'])
    def _return(self, version, products, project, freqmode=None):
        return {'Info': {'Products': products}}

    @register_versions('fetch', ['v5'])
    def _get_v5(self, version, project, freqmode=None):
        db = level2db.Level2DB(project)
        return db.get_products(freqmode=freqmode)

    @register_versions('return', ['v5'])
    def _return_v5(self, version, products, project, freqmode=None):
        return {'Data': products, 'Type': 'level2_product_name',
                'Count': len(products)}


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

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'product', 'location', 'radius',
             'min_pressure', 'max_pressure', 'min_altitude', 'max_altitude',
             'start_time', 'end_time'],
            {
                "200": SWAGGER.get_type_response('L2', is_list=True),
                "400": SWAGGER.get_response('Level2BadQuery')
            },
            summary=(
                "Get data close to provided location"),
            description=(
                "Provide one or more locations and a radius to get "
                "data within the resulting circles on the earth surface.\n"
                "\n"
                "Choose between min/max altitude and min/max pressure.\n"
                "\n"
                "Example query:\n"
                "\n"
                "   product=p1&product=p2&min_pressure=100&max_pressure=1000&"
                "start_time=2015-10-11&end_time=2016-02-20&radius=100&"
                "location=-24.0,200.0&location=-30.0,210.0")
        )

    @register_versions('fetch')
    def _fetch(self, version, project):
        if not get_args.get_list('location'):
            raise BadRequest('No locations specified')
        try:
            param = parse_parameters()
        except ValueError as err:
            raise BadRequest(str(err))
        db = level2db.Level2DB(project)
        # TODO: Limit/paging
        meas_iter = db.get_measurements(param.pop('products'), **param)
        return meas_iter

    @register_versions('return', ['v4'])
    def _return(self, version, results, _):
        results = list(results)
        return {'Info': {'Nr': len(results), 'Results': results}}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, results, _):
        scans = []
        for _, scan in groupby(results, itemgetter('ScanID')):
            scans.extend(level2db.collapse_products(list(scan)))
        return {'Data': scans, 'Type': 'L2', 'Count': len(scans)}


class Level2ViewDay(Level2ProjectBaseView):
    """Get data for a certain day

    Choose between min/max altitude and min/max pressure.

    Example query:

        product=p1&product=p2&min_pressure=1000&max_pressure=1000
    """
    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'date', 'product',
             'min_pressure', 'max_pressure', 'min_altitude', 'max_altitude'],
            {
                "200": SWAGGER.get_type_response('L2', is_list=True),
                "400": SWAGGER.get_response('Level2BadQuery')
            },
            summary=(
                "Get data for provided day"),
            description=(
                "Get data for a certain day\n"
                "\n"
                "Choose between min/max altitude and min/max pressure.\n"
                "\n"
                "Example query:\n"
                "\n"
                "    product=p1&product=p2&min_pressure=1000&max_pressure=1000"
            )
        )

    @register_versions('fetch')
    def _fetch(self, version, project, date):
        try:
            start_time = get_args.get_datetime(val=date)
        except ValueError as e:
            abort(400)
        end_time = start_time + timedelta(hours=24)
        try:
            param = parse_parameters(start_time=start_time, end_time=end_time)
        except ValueError as e:
            return jsonify({'Error': str(e)})
        db = level2db.Level2DB(project)
        meas_iter = db.get_measurements(param.pop('products'), **param)
        return meas_iter

    @register_versions('return', ['v4'])
    def _return(self, version, results, *args, **kwargs):
        results = list(results)
        return {'Info': {'Nr': len(results), 'Results': results}}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, results, *args, **kwargs):
        scans = []
        for _, scan in groupby(results, itemgetter('ScanID')):
            scans.extend(level2db.collapse_products(list(scan)))
        return {'Data': scans, 'Type': 'L2', 'Count': len(scans)}


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

    @register_versions('swagger', ['v5'])
    def _swagger_def(self, version):
        return SWAGGER.get_path_definition(
            ['level2'],
            ['version', 'project', 'product', 'min_lat', 'max_lat',
             'min_lon', 'max_lon', 'min_pressure', 'max_pressure',
             'min_altitude', 'max_altitude', 'start_time', 'end_time'],
            {
                "200": SWAGGER.get_type_response('L2', is_list=True),
                "400": SWAGGER.get_response('Level2BadQuery')
            },
            summary=(
                "Get data in provided area"),
            description=(
                "Get data for a certain area\n"
                "\n"
                "Provide latitude and/or longitude limits to get data for a "
                "certain area of the earth.\n"
                "\n"
                "If no latitude or longitude limits are provided, data for "
                "the whole earth is returned.\n"
                "\n"
                "Choose between min/max altitude and min/max pressure."
                "\n"
                "Example url parameters:\n"
                "\n"
                "    product=p1&product=p2&min_pressure=100&max_pressure=100&"
                "start_time=2015-10-11&end_time=2016-02-20&min_lat=-80&"
                "max_lat=-70&min_lon=150&max_lon=200")
        )

    @register_versions('fetch')
    def _fetch(self, version, project):
        try:
            param = parse_parameters()
        except ValueError as e:
            raise BadRequest(str(e))
        db = level2db.Level2DB(project)
        meas_iter = db.get_measurements(param.pop('products'), **param)
        # TODO: Limit/paging
        return meas_iter

    @register_versions('return', ['v4'])
    def _return(self, version, results, _):
        results = list(results)
        return {'Info': {'Nr': len(results), 'Results': results}}

    @register_versions('return', ['v5'])
    def _return_v5(self, version, results, _):
        scans = []
        for _, scan in groupby(results, itemgetter('ScanID')):
            scans.extend(level2db.collapse_products(list(scan)))
        return {'Data': scans, 'Type': 'L2', 'Count': len(scans)}


def parse_parameters(**kwargs):
    """Parse parameters coming from the request"""
    products = get_args.get_list('product')

    # Altitude or pressure
    min_pressure = get_args.get_float(
        'min_pressure', kwargs.get('min_pressure'))
    max_pressure = get_args.get_float(
        'max_pressure', kwargs.get('max_pressure'))
    if min_pressure and max_pressure and min_pressure > max_pressure:
        raise ValueError('Min pressure must not be larger than max pressure')

    min_altitude = get_args.get_float(
        'min_altitude', kwargs.get('min_altitude'))
    max_altitude = get_args.get_float(
        'max_altitude', kwargs.get('max_altitude'))
    if min_altitude and max_altitude and min_altitude > max_altitude:
        raise ValueError('Min altitude must not be larger than max altitude')

    if (min_pressure or max_pressure) and (min_altitude or max_altitude):
        raise ValueError(
            'Not supported to filter by altitude and pressure at the same time'
        )

    # Time
    start_time = get_args.get_datetime('start_time', kwargs.get('start_time'))
    end_time = get_args.get_datetime('end_time', kwargs.get('end_time'))
    if start_time and end_time and start_time > end_time:
        raise ValueError('Start time must not be after end time')

    if not (any([min_pressure, max_pressure, min_altitude, max_altitude]) and
            any([start_time, end_time])):
        raise ValueError(
            'Too broad query, you must provide at least one of pressure or '
            'altitude max/min, and at least one of start_time and '
            'end_time.')

    # Geographic
    radius = get_args.get_float('radius')
    locations = get_args.get_list('location') or []
    if locations and not radius:
        raise ValueError('Missing parameter radius')
    circles = [
        loc.split(',') + [radius] for loc in locations]
    circles = [level2db.GeographicCircle(*c) for c in circles]

    area = [get_args.get_string(arg) for arg in [
        'min_lat', 'max_lat', 'min_lon', 'max_lon']]

    if circles and any(area):
        raise ValueError(
            ('Not supported to filter both by locations and area at the '
             'same time'))
    if any(area):
        area = level2db.GeographicArea(*area)
    else:
        area = None

    # Fields to return
    fields = get_args.get_list('field')

    return {
        'products': products,
        'min_pressure': min_pressure,
        'max_pressure': max_pressure,
        'min_altitude': min_altitude,
        'max_altitude': max_altitude,
        'start_time': start_time,
        'end_time': end_time,
        'areas': circles or area,
        'fields': fields
    }
