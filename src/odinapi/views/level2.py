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


class Level2View(MethodView):

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
