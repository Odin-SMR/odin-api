from datetime import datetime, timedelta

import yaml
from dateutil.parser import parse as parse_datetime

from flask import request, abort, jsonify
from flask.views import MethodView

from pymongo.errors import DuplicateKeyError

from odinapi.utils.encrypt_util import decode_level2_target_parameter
from odinapi.utils.jsonmodels import (
    l2_prototype, l2i_prototype, check_json, JsonModelError)
from odinapi.utils.defs import FREQMODE_TO_BACKEND

from odinapi.views import level2db

SWAGGER_DEFINITIONS = yaml.load("""
 Level2Data:
   required:
     - Info
   properties:
     Info:
       required:
         - Nr
         - Results
       properties:
         Nr:
           type: integer
         Results:
           type: array
           items:
             properties:
               Product:
                 type: string
               FreqMode:
                 type: integer
               ScanID:
                 type: integer
               InvMode:
                 type: string
               MJD:
                 type: number
               Lat1D:
                 type: number
               Lon1D:
                 type: number
               Quality:
                 type: number
               Altitude:
                 type: number
               Pressure:
                 type: number
               Latitude:
                 type: number
               Longitude:
                 type: number
               Temperature:
                 type: number
               ErrorTotal:
                 type: number
               ErrorNoise:
                 type: number
               MeasResponse:
                 type: number
               Apriori:
                 type: number
               VMR:
                 type: number
               AVK:
                 type: array
                 items:
                   type: number""")

SWAGGER_RESPONSES = yaml.load("""
    Level2BadRequest:
      description: Unsupported query.
      schema:
        required:
          - Error
        properties:
          Error:
            type: string""")

SWAGGER_PARAMETERS = yaml.load("""
   version:
     name: version
     in: path
     type: string
     default: v4
   project:
     name: project
     in: path
     type: string
     required: true
   freqmode:
     name: freqmode
     in: path
     type: integer
     required: true
   scanno:
     name: scanno
     in: path
     type: integer
     required: true
   date:
     name: date
     in: path
     type: string
     format: date
     required: true
   radius:
     name: radius
     required: true
     in: query
     description: Return data within this radius from the provided
                  locations (km).
     type: number
   location:
     name: location
     required: true
     in: query
     description: "Return data close to these locations (lat,lon).
                   Example location: '-10.1,300.3'."
     type: array
     collectionFormat: multi
     uniqueItems: true
     items:
       type: string
   min_lat:
     name: min_lat
     in: query
     description: Min latitude (-90 to 90).
     type: number
   max_lat:
     name: max_lat
     in: query
     description: Max latitude (-90 to 90).
     type: number
   min_lon:
     name: min_lon
     in: query
     description: Min longitude (0 to 360).
     type: number
   max_lon:
     name: max_lon
     in: query
     description: Max longitude (0 to 360).
     type: number
   product:
     name: product
     in: query
     description: Return data only for these products.
     type: array
     collectionFormat: multi
     uniqueItems: true
     items:
       type: string
   min_pressure:
     name: min_pressure
     in: query
     description: Min pressure (Pa).
     type: number
   max_pressure:
     name: max_pressure
     in: query
     description: Max pressure (Pa).
     type: number
   min_altitude:
     name: min_altitude
     in: query
     description: Min altitude (m).
     type: number
   max_altitude:
     name: max_altitude
     in: query
     description: Max altitude (m).
     type: number
   start_time:
     name: start_time
     in: query
     description: Return data after this time (inclusive).
     type: string
     format: date-time
   end_time:
     name: end_time
     in: query
     description: Return data before this time (exclusive).
     type: string
     format: date-time""")


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
        if not isinstance(L2, list):
            abort(400)
        for nr, species in enumerate(L2):
            try:
                check_json(species, prototype=l2_prototype)
            except JsonModelError as e:
                return jsonify(
                    {'error': 'L2 species %d: %s' % (nr, e)}), 400
        L2i = data.pop('L2I')
        if not isinstance(L2i, dict):
            abort(400)
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
        """
        Get data for one scan and freqmode

        ---
        tags:
          - level2
        parameters:
          - $ref: '#/parameters/version'
          - $ref: '#/parameters/project'
          - $ref: '#/parameters/freqmode'
          - $ref: '#/parameters/scanno'
        responses:
          200:
            description: L2i and L2 on the same format as returned by
                         the processing.
          404:
            description: The scan does not exist in this project.
        """
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


class Level2ViewProducts(MethodView):
    """GET available products"""
    def get(self, version, project):
        """
        Get available products

        Return product names and number of occurences of each product.
        ---
        tags:
          - level2
        parameters:
          - $ref: '#/parameters/version'
          - $ref: '#/parameters/project'
        responses:
          200:
            description: Dict with product name as key and count as value.
            schema:
              required:
                - Info
              properties:
                Info:
                  required:
                    - Products
                  properties:
                    Products:
                      type: object
                      additionalProperties:
                        type: integer
        """
        db = level2db.Level2DB(project)
        products = db.get_product_count()
        return jsonify({'Info': {'Products': products}})


class Level2ViewLocations(MethodView):
    """GET data close to provided locations."""
    def get(self, version, project):
        """
        Get data close to provided locations

        Provide one or more locations and a radius to get data within the
        resulting circles on the earth surface.

        Choose between min/max altitude and min/max pressure.

        Example query:

            product=p1&product=p2&min_pressure=100&max_pressure=1000&
            start_time=2015-10-11&end_time=2016-02-20&radius=100&
            location=-24.0,200.0&location=-30.0,210.0
        ---
        tags:
          - level2
        parameters:
          - $ref: '#/parameters/version'
          - $ref: '#/parameters/project'
          - $ref: '#/parameters/radius'
          - $ref: '#/parameters/location'
          - $ref: '#/parameters/product'
          - $ref: '#/parameters/min_pressure'
          - $ref: '#/parameters/max_pressure'
          - $ref: '#/parameters/min_altitude'
          - $ref: '#/parameters/max_altitude'
          - $ref: '#/parameters/start_time'
          - $ref: '#/parameters/end_time'
        responses:
          200:
            description: List of level2 data.
            schema:
               $ref: '#/definitions/Level2Data'
          400:
            $ref: '#/responses/Level2BadRequest'
        """
        if not get_list('location'):
            return jsonify({'Error': 'No locations specified'}), 400
        try:
            param = parse_parameters()
        except ValueError as e:
            return jsonify({'Error': str(e)}), 400
        db = level2db.Level2DB(project)
        meas = db.get_measurements(param.pop('products'), **param)
        # TODO: Limit/paging
        results = list(meas)
        return jsonify({'Info': {'Nr': len(results), 'Results': results}})


class Level2ViewDay(MethodView):
    """Get data for a certain day"""
    def get(self, version, project, date):
        """
        Get data for a certain day

        Choose between min/max altitude and min/max pressure.

        Example query:

            product=p1&product=p2&min_pressure=1000&max_pressure=1000
        ---
        tags:
          - level2
        parameters:
          - $ref: '#/parameters/version'
          - $ref: '#/parameters/project'
          - $ref: '#/parameters/date'
          - $ref: '#/parameters/product'
          - $ref: '#/parameters/min_pressure'
          - $ref: '#/parameters/max_pressure'
          - $ref: '#/parameters/min_altitude'
          - $ref: '#/parameters/max_altitude'
        responses:
          200:
            description: List of level2 data.
            schema:
                $ref: '#/definitions/Level2Data'
          400:
            $ref: '#/responses/Level2BadRequest'
        """
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
        results = list(meas)
        return jsonify({'Info': {'Nr': len(results), 'Results': results}})


class Level2ViewArea(MethodView):
    """GET data for a certain area"""
    def get(self, version, project):
        """
        Get data for a certain area

        Provide latitude and/or longitude limits to get data for a certain
        area of the earth.

        If no latitude or longitude limits are provided, data for the whole
        earth is returned.

        Choose between min/max altitude and min/max pressure.

        Example url parameters:

            product=p1&product=p2&min_pressure=100&max_pressure=100&
            start_time=2015-10-11&end_time=2016-02-20&min_lat=-80&
            max_lat=-70&min_lon=150&max_lon=200
        ---
        tags:
          - level2
        parameters:
          - $ref: '#/parameters/version'
          - $ref: '#/parameters/project'
          - $ref: '#/parameters/min_lat'
          - $ref: '#/parameters/max_lat'
          - $ref: '#/parameters/min_lon'
          - $ref: '#/parameters/max_lon'
          - $ref: '#/parameters/product'
          - $ref: '#/parameters/min_pressure'
          - $ref: '#/parameters/max_pressure'
          - $ref: '#/parameters/min_altitude'
          - $ref: '#/parameters/max_altitude'
          - $ref: '#/parameters/start_time'
          - $ref: '#/parameters/end_time'
        responses:
          200:
            description: List of level2 data.
            schema:
                $ref: '#/definitions/Level2Data'
          400:
            $ref: '#/responses/Level2BadRequest'
        """
        try:
            param = parse_parameters()
        except ValueError as e:
            return jsonify({'Error': str(e)}), 400
        db = level2db.Level2DB(project)
        meas = db.get_measurements(param.pop('products'), **param)
        # TODO: Limit/paging
        results = list(meas)
        return jsonify({'Info': {'Nr': len(results), 'Results': results}})


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
