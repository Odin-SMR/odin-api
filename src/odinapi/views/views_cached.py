""" doc
"""
from flask import request
from flask import jsonify, abort
from flask.views import MethodView
from datetime import date as dateclass
from datetime import datetime
from database import DatabaseConnector


class DateInfoCached(MethodView):
    """DateInfo using a cached table"""
    def get(self, version, date):
        """GET"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        try:
            date1 = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            date1 = datetime(2015, 1, 3)
        date_iso_str = date1.date().isoformat()
        query_str = self.gen_query(date_iso_str)
        info_list = self.gen_data(date_iso_str, version, query_str)
        return jsonify(Date=date_iso_str, Info=info_list)

    def gen_data(self, date, version, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        info_list = []
        for row in result:
            info_dict = {}
            info_dict['Backend'] = row['backend']
            info_dict['FreqMode'] = row['freqmode']
            info_dict['NumScan'] = row['nscans']
            info_dict['URL'] = (
                '{0}rest_api/{1}/freqmode_info/{2}/{3}/{4}').format(
                    request.url_root, version, date, row['backend'],
                    row['freqmode'])
            info_list.append(info_dict)
        con.close()
        return info_list

    def gen_query(self, date):
        query_str = (
            "select freqmode, backend, nscans "
            "from measurements_cache "
            "where date = '{0}' "
            "order by backend, freqmode "
            ).format(date)
        return query_str
