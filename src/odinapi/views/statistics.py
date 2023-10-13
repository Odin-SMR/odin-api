""" doc
"""
from odinapi.pg_database import squeeze_query
from flask import jsonify, abort, request
from flask.views import MethodView
from datetime import date, datetime, timedelta

from sqlalchemy import text
from ..pg_database import db


def find_last_day_of_month(year, month):
    month += 1
    if month == 13:
        year += 1
        month = 1
    return date(year, month, 1) - timedelta(1)


class FreqmodeStatistics(MethodView):
    """Statistics of total number of scans per freqmode"""

    query = text(
        squeeze_query(
            """\
        select freqmode, sum(nscans)
        from measurements_cache
        where date between :d1 and :d2
        group by freqmode
        order by freqmode"""
        )
    )

    def get(self, version):
        """GET"""
        year = request.args.get("year")
        if version not in ["v4", "v5"]:
            abort(404)
        if year is None or year == "":
            return self.get_all()
        else:
            return self.get_year(int(year))

    def get_all(self):
        """Get freqmode scans summed up for all years"""
        first_date = "2001-01-01"
        last_date = "{0}-12-31".format(datetime.now().year)
        info_list = self.gen_data(dict(d1=first_date, d2=last_date))
        return jsonify(Data=info_list)

    def get_year(self, year):
        """Get freqmode scans summed up for a single year"""
        first_date = "{0}-01-01".format(year)
        last_date = "{0}-12-31".format(year)
        info_list = self.gen_data(dict(d1=first_date, d2=last_date))
        return jsonify(Data=info_list)

    def gen_data(self, params):
        query = db.session.execute(self.query, params=params)
        result = [row._asdict() for row in query]
        return result


class TimelineFreqmodeStatistics(MethodView):
    """Statistics of number of scans per freqmode for different years"""

    query = text(
        """\
        select freqmode, sum(nscans)
        from measurements_cache
        where date between :d1 and :d2
        group by freqmode
        order by freqmode"""
    )

    def get(self, version):
        """GET"""
        year = request.args.get("year")
        if version not in ["v4", "v5"]:
            abort(404)
        if year is None or year == "":
            return self.get_years()
        else:
            return self.get_months(int(year))

    def get_years(self):
        """Get freqmode scans per year for all years"""
        info_dict = {}
        years = list(range(2001, datetime.now().year + 1))
        for year in years:
            first_date = "{0}-01-01".format(year)
            last_date = "{0}-12-31".format(year)
            result = db.session.execute(
                self.query, params=dict(d1=first_date, d2=last_date)
            )
            for row in result:
                try:
                    info_dict[row.freqmode].append([year, row.sum])
                except KeyError:
                    info_dict[row.freqmode] = [[year, row.sum]]
        info_dict = self._fill_blanks(years, info_dict)
        return jsonify(Data=info_dict, Years=years)

    def get_months(self, year):
        """Get freqmode scans per month for a single year"""
        info_dict = {}
        months = list(range(1, 13))
        for month in months:
            first_date = date(year, month, 1)
            last_date = find_last_day_of_month(year, month)
            result = db.session.execute(
                self.query, params=dict(d1=first_date, d2=last_date)
            )
            for row in result:
                try:
                    info_dict[row.freqmode].append([month, row.sum])
                except KeyError:
                    info_dict[row.freqmode] = [[month, row.sum]]
        info_dict = self._fill_blanks(months, info_dict)
        return jsonify(Data=info_dict, Months=months, Year=year)

    def _fill_blanks(self, indices, info_dict):
        for key in info_dict:
            for n, ind in enumerate(indices):
                try:
                    if info_dict[key][n][0] != ind:
                        info_dict[key].insert(n, [ind, 0])
                except IndexError:
                    info_dict[key].append([ind, 0])
        return info_dict
