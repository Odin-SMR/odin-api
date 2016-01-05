""" doc
"""
from flask import jsonify, abort
from flask.views import MethodView
from database import DatabaseConnector
import datetime
now = datetime.datetime.now


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
        info_list = []
        for year in xrange(2001, now().year+1):
            first_date = "{0}-01-01".format(year)
            last_date = "{0}-12-31".format(year)
            query_str = self.gen_query(first_date, last_date)
            result = self.gen_data(query_str)[0]
            result["year"] = year
            info_list.append(result)
        return jsonify(Data=info_list)

    def gen_data(self, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        con.close()
        return result

    def gen_query(self, first_date, last_date):
        query_str = (
            "select sum(nscans) "
            "from measurements_cache "
            "where date between '{0}' and '{1}'"
            ).format(first_date, last_date)
        return query_str


class SeasonalNscanStatistics(MethodView):
    """Statistics of total number of scans per month, by default for
    all years summed up."""
    def get(self, version, year=None):
        """GET"""
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        info_list = []
        for year in xrange(2001, now().year+1):
            first_date = "{0}-01-01".format(year)
            last_date = "{0}-12-31".format(year)
            query_str = self.gen_query(first_date, last_date)
            result = self.gen_data(query_str)[0]
            result["year"] = year
            info_list.append(result)
        return jsonify(Data=info_list)

    def gen_data(self, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        con.close()
        return result

    def gen_query(self, first_date, last_date):
        query_str = (
            "select sum(nscans) "
            "from measurements_cache "
            "where date between '{0}' and '{1}'"
            ).format(first_date, last_date)
        return query_str
