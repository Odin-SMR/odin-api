""" doc
"""
from flask import jsonify, abort
from flask.views import MethodView
from database import DatabaseConnector


class TotalFreqmodeStatistics(MethodView):
    """Statistics of total number of scans per freqmode"""
    def get(self, version):
        """GET"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        query_str = self.gen_query()
        info_list = self.gen_data(query_str)
        return jsonify(Data=info_list)

    def gen_data(self, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        con.close()
        return result

    def gen_query(self):
        query_str = (
            "select freqmode, sum(nscans) "
            "from measurements_cache "
            "group by freqmode "
            "order by freqmode "
            )
        return query_str


class AnnualNscanStatistics(MethodView):
    """Statistics of total number of scans per year"""
    def get(self, version):
        """GET"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        query_str = self.gen_query()
        info_list = self.gen_data(query_str)
        return jsonify(Data=info_list)

    def gen_data(self, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        con.close()
        return result

    def gen_query(self):
        query_str = (
            "select freqmode, sum(nscans) "
            "from measurements_cache "
            "group by freqmode "
            "order by freqmode "
            )
        return query_str
