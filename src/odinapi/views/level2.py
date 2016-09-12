from flask import request, abort, jsonify
from flask.views import MethodView

from odinapi.utils.encrypt_util import decode_level2_target_parameter
from odinapi.utils.jsonmodels import (
    l2_prototype, l2i_prototype, check_json, JsonModelError)

from level2_importer import store_level2_data


class Level2Data(MethodView):

    def post(self):
        """Insert level2 data for a scan and freq mode"""
        msg = request.args.get('d')
        if not msg:
            abort(400)
        try:
            scanid, freqmode = decode_level2_target_parameter(msg)
        except:
            abort(400)
        data = request.json
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
        store_level2_data(scanid, freqmode, L2, L2i)
        return '', 204
