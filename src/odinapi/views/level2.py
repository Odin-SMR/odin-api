from flask import request, abort, jsonify
from flask.views import MethodView

from pymongo.errors import DuplicateKeyError

from odinapi.utils.encrypt_util import decode_level2_target_parameter
from odinapi.utils.jsonmodels import (
    l2_prototype, l2i_prototype, check_json, JsonModelError)

from odinapi.views import level2db


class Level2Data(MethodView):

    def __init__(self):
        self.level2db = level2db.Level2DB()

    def post(self, version):
        """Insert level2 data for a scan id and freq mode"""
        msg = request.args.get('d')
        if not msg:
            abort(400)
        try:
            scanid, freqmode = decode_level2_target_parameter(msg)
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
        try:
            self.level2db.store(L2, L2i)
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
            scanid, freqmode = decode_level2_target_parameter(msg)
        except:
            abort(400)
        self.level2db.delete(scanid, freqmode)
        return '', 204
