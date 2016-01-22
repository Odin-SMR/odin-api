""" doc
"""
from flask import jsonify, abort, request
from flask.views import MethodView
from database import DatabaseConnector
from datetime import date, datetime, timedelta


def find_last_day_of_month(year, month):
    month += 1
    if month == 13:
        year += 1
        month = 1
    return date(year, month, 1) - timedelta(1)


class FreqmodeStatistics(MethodView):
    """Statistics of total number of scans per freqmode"""
    def get(self, version):
        """GET"""
        year = request.args.get('year')
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        if year is None or year == '':
            return self.get_all()
        else:
            return self.get_year(int(year))

    def get_all(self):
        """Get freqmode scans summed up for all years"""
        first_date = "2001-01-01"
        last_date = "{0}-12-31".format(datetime.now().year)
        query_str = self.gen_query(first_date, last_date)
        info_list = self.gen_data(query_str)
        return jsonify(Data=info_list)

    def get_year(self, year):
        """Get freqmode scans summed up for a single year"""
        first_date = "{0}-01-01".format(year)
        last_date = "{0}-12-31".format(year)
        query_str = self.gen_query(first_date, last_date)
        info_list = self.gen_data(query_str)
        return jsonify(Data=info_list)

    def gen_data(self, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        con.close()
        return result

    def gen_query(self, first_date, last_date):
        query_str = (
            "select freqmode, sum(nscans) "
            "from measurements_cache "
            "where date between '{0}' and '{1}' "
            "group by freqmode "
            "order by freqmode ".format(first_date, last_date)
            )
        return query_str


class TimelineFreqmodeStatistics(MethodView):
    """Statistics of number of scans per freqmode for different years"""
    def get(self, version):
        """GET"""
        year = request.args.get('year')
        if version not in ['v1', 'v2', 'v3', 'v4']:
            abort(404)
        if year is None or year == '':
            return self.get_years()
        else:
            return self.get_months(int(year))

    def get_years(self):
        """Get freqmode scans per year for all years"""
        info_dict = {}
        years = range(2001, datetime.now().year+1)
        for year in years:
            first_date = "{0}-01-01".format(year)
            last_date = "{0}-12-31".format(year)
            query_str = self.gen_query(first_date, last_date)
            result = self.gen_data(query_str)
            for row in result:
                try:
                    info_dict[row["freqmode"]].append([year, row["sum"]])
                except KeyError:
                    info_dict[row["freqmode"]] = [[year, row["sum"]]]
        info_dict = self._fill_blanks(years, info_dict)
        return jsonify(Data=info_dict, Years=years)

    def get_months(self, year):
        """Get freqmode scans per month for a single year"""
        info_dict = {}
        months = range(1, 13)
        for month in months:
            first_date = date(year, month, 1)
            last_date = find_last_day_of_month(year, month)
            query_str = self.gen_query(first_date.isoformat(),
                                       last_date.isoformat())
            result = self.gen_data(query_str)
            for row in result:
                try:
                    info_dict[row["freqmode"]].append([month, row["sum"]])
                except KeyError:
                    info_dict[row["freqmode"]] = [[month, row["sum"]]]
        info_dict = self._fill_blanks(months, info_dict)
        return jsonify(Data=info_dict, Months=months, Year=year)

    def _fill_blanks(self, indices, info_dict):
        for key in info_dict.keys():
            for n, ind in enumerate(indices):
                if info_dict[key][0] != ind:
                    info_dict[key].insert(n, [ind, 0])
        return info_dict

    def gen_data(self, query_string):
        con = DatabaseConnector()
        query = con.query(query_string)
        result = query.dictresult()
        con.close()
        return result

    def gen_query(self, first_date, last_date):
        query_str = (
            "select freqmode, sum(nscans) "
            "from measurements_cache "
            "where date between '{0}' and '{1}' "
            "group by freqmode "
            "order by freqmode "
            ).format(first_date, last_date)
        return query_str
