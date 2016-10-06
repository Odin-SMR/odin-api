from datetime import datetime, timedelta
from dateutil.parser import parse as parse_datetime

from flask import request, abort, jsonify
from flask.views import MethodView

from pymongo.errors import DuplicateKeyError

from odinapi.utils.encrypt_util import decode_level2_target_parameter
from odinapi.utils.jsonmodels import (
    l2_prototype, l2i_prototype, check_json, JsonModelError)
from odinapi.utils.defs import FREQMODE_TO_BACKEND

from odinapi.views import level2db


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
        if 'L2' not in data or 'L2I' not in data:
            abort(400)
        L2 = data.pop('L2')
        for nr, species in enumerate(L2):
            try:
                check_json(species, prototype=l2_prototype)
            except JsonModelError as e:
                return jsonify(
                    {'error': 'L2 species %d: %s' % (nr, e)}), 400
        L2i = data.pop('L2I')
        try:
            check_json(L2i, prototype=l2i_prototype)
        except JsonModelError as e:
            return jsonify({'error': 'L2i: %s' % e}), 400
        if scanid != L2i['ScanID']:
            return jsonify(
                {'error': 'ScanID missmatch (%r != %r)' % (
                    scanid, L2i['ScanID'])}), 400
        if freqmode != L2i['FreqMode']:
            return jsonify(
                {'error': 'FreqMode missmatch (%r != %r)' % (
                    scanid, L2i['FreqMode'])}), 400
        db = level2db.Level2DB(project)
        try:
            db.store(L2, L2i)
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


class Level2ViewScan(MethodView):
    """GET data for one scan and freqmode"""

    def get(self, version, project, freqmode, scanno):
        db = level2db.Level2DB(project)
        L2i, L2 = db.get_scan(freqmode, scanno)
        if not L2i:
            abort(404)
        backend = FREQMODE_TO_BACKEND[freqmode]
        info = {'L2': L2, 'L2i': L2i, 'URLS': {
            'URL-log': '{0}rest_api/{1}/l1_log/{2}/{3}/'.format(
                request.url_root, version, freqmode, scanno),
            'URL-level2': '{0}rest_api/{1}/level2/{2}/{3}/{4}/'.format(
                request.url_root, version, project, freqmode, scanno),
            'URL-spectra': '{0}rest_api/{1}/scan/{2}/{3}/{4}/'.format(
                request.url_root, version, backend, freqmode, scanno)
        }}
        return jsonify({'Info': info})


class Level2ViewLocations(MethodView):
    """
    Example url parameters:

        product=p1&product=p2&min_pressure=100&max_pressure=1000&
        start_time=2015-10-11&end_time=2016-02-20&radius=100&
        location=-24.0,200.0&location=-30.0,210.0
    """
    def get(self, version, project):
        if not get_list('location'):
            return jsonify({'Error': 'No locations specified'}), 400
        try:
            param = parse_parameters()
        except ValueError as e:
            return jsonify({'Error': str(e)}), 400
        db = level2db.Level2DB(project)
        meas = db.get_measurements(param.pop('products'), **param)
        # TODO: Limit/paging
        return jsonify({'Info': {'Results': list(meas)}})


class Level2ViewDay(MethodView):
    """
    Example url parameters:

        product=p1&product=p2&min_pressure=1000&max_pressure=1000
    """
    def get(self, version, project, date):
        try:
            start_time = get_datetime(val=date)
        except ValueError as e:
            return jsonify({'Error': str(e)}), 400
        end_time = start_time + timedelta(hours=24)
        try:
            param = parse_parameters(start_time=start_time, end_time=end_time)
        except ValueError as e:
            return jsonify({'Error': str(e)})
        db = level2db.Level2DB(project)
        meas = db.get_measurements(param.pop('products'), **param)
        return jsonify({'Info': {'Results': list(meas)}})


class Level2ViewArea(MethodView):
    """
    Example url parameters:

        product=p1&product=p2&min_pressure=100&max_pressure=100&
        start_time=2015-10-11&end_time=2016-02-20&min_lat=-80&
        max_lat=-70&min_lon=150&max_lon=200
    """
    def get(self, version, project):
        try:
            param = parse_parameters()
        except ValueError as e:
            return jsonify({'Error': str(e)}), 400
        db = level2db.Level2DB(project)
        meas = db.get_measurements(param.pop('products'), **param)
        # TODO: Limit/paging
        return jsonify({'Info': {'Results': list(meas)}})


def parse_parameters(**kwargs):
    products = get_list('product')

    # Altitude or pressure
    min_pressure = get_float('min_pressure')
    max_pressure = get_float('max_pressure')
    if min_pressure and max_pressure and min_pressure > max_pressure:
        raise ValueError('Min pressure must not be larger than max pressure')

    min_altitude = get_float('min_altitude')
    max_altitude = get_float('max_altitude')
    if min_altitude and max_altitude and min_altitude > max_altitude:
        raise ValueError('Min altitude must not be larger than max altitude')

    if (min_pressure or max_pressure) and (min_altitude or max_altitude):
        raise ValueError(
            'Not supported to filter by altitude and pressure at the same time'
        )

    # Time
    start_time = get_datetime('start_time', kwargs.get('start_time'))
    end_time = get_datetime('end_time', kwargs.get('end_time'))
    if start_time and end_time and start_time > end_time:
        raise ValueError('Start time must not be after end time')

    # Geographic
    radius = get_float('radius')
    locations = get_list('location') or []
    if locations and not radius:
        raise ValueError('Missing parameter radius')
    circles = [
        loc.split(',') + [radius] for loc in locations]
    circles = [level2db.GeographicCircle(*c) for c in circles]

    area = [get_string(arg) for arg in [
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
    fields = get_list('field')

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


def get_string(arg):
    return request.args.get(arg)


def get_float(arg=None, val=None):
    if not val:
        val = request.args.get(arg)
    if not val:
        return
    try:
        return float(val)
    except ValueError:
        raise ValueError('Could not convert to number: %r' % val)


def get_list(arg):
    return request.args.getlist(arg) or None


def get_datetime(arg=None, val=None):
    if not val:
        val = request.args.get(arg)
    if not val:
        return
    if isinstance(val, datetime):
        return val
    try:
        return parse_datetime(val)
    except ValueError:
        raise ValueError('Bad time format: %r' % val)
