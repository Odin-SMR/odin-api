#! /usr/bin/env python
"""
Part of odin-api, tools to make it happen
"""

from requests import get
from requests.exceptions import HTTPError
from datetime import date, timedelta
from psycopg2 import connect
from argparse import ArgumentParser
from dateutil import parser as date_parser


def odin_connection():
    """Connects to the database, returns a connection"""
    connection_string = (
        "host='malachite.rss.chalmers.se' "
        "dbname='odin' "
        "user='odinop' "
        "password='***REMOVED***'"
        )
    connection = connect(connection_string)
    return connection


def add_to_database(cursor, day, freqmode, backend, altend, altstart, datetime,
                    latend, latstart, lonend, lonstart, mjdend, mjdstart,
                    numspec, scanid, sunzd):
    """Add an entry to the database, delete the oldone first"""
    cursor.execute(
        """
        delete from scans_cache
        where freqmode=%s and scanid=%s
        """,
        (freqmode, scanid))
    cursor.execute(
        'insert into scans_cache values(%s,%s,%s,%s,%s,%s,%s,%s,'
        '%s,%s,%s,%s,%s,%s,%s)',
        (day, freqmode, backend, scanid, altend, altstart, latend, latstart,
         lonend, lonstart, mjdend, mjdstart, numspec, sunzd, datetime))


def setup_arguments():
    parser = ArgumentParser(description="Repopulate the cached data table")
    parser.add_argument("-s", "--start", dest="start_date", action="store",
                        default=(date.today()-timedelta(days=31)).isoformat(),
                        help="start of period to look for new data "
                        "(default: one month back)")
    parser.add_argument("-e", "--end", dest="end_date", action="store",
                        default=date.today().isoformat(),
                        help="end of period to look for new data "
                        "(default: today)")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="use verbose output")
    return parser


def main(start_date=date.today()-timedelta(days=31), end_date=date.today(),
         verbose=False):
    """Script to populate database with 'cached'info.

    Walks backwards from end_date to start_date."""
    step = timedelta(days=-1)
    current_date = end_date
    earliest_date = start_date
    db_connection = odin_connection()
    db_cursor = db_connection.cursor()
    while current_date >= earliest_date:
        url_day = (
            'http://odin.rss.chalmers.se/'
            'rest_api/v4/freqmode_raw/{}/'.format(current_date.isoformat())
            )
        response = get(url_day)
        try:
            response.raise_for_status()
        except HTTPError, msg:
            print current_date, msg, url_day
            continue
        json_data_day = response.json()
        for freqmode in json_data_day['Info']:
            url_scan = (
                '{0}/{1}/{2}/'.format(url_day, freqmode['Backend'],
                                      freqmode['FreqMode'])
                )
            response = get(url_scan)
            try:
                response.raise_for_status()
            except HTTPError, msg:
                print current_date, msg, url_scan
                continue
            json_data_scan = response.json()
            for scan in json_data_scan['Info']:
                add_to_database(
                    db_cursor,
                    json_data_scan['Date'],
                    freqmode['FreqMode'],
                    freqmode['Backend'],
                    scan["AltEnd"],
                    scan["AltStart"],
                    scan["DateTime"],
                    scan["LatEnd"],
                    scan["LatStart"],
                    scan["LonEnd"],
                    scan["LonStart"],
                    scan["MJDEnd"],
                    scan["MJDStart"],
                    scan["NumSpec"],
                    scan["ScanID"],
                    scan["SunZD"],
                    )
        db_connection.commit()
        if verbose:
            print current_date, "OK"
        current_date = current_date + step
    db_cursor.close()
    db_connection.close()

if __name__ == '__main__':
    parser = setup_arguments()
    args = parser.parse_args()

    try:
        start_date = date_parser.parse(args.start_date).date()
    except TypeError:
        print "Could not understand start date {0}".format(args.start_date)
        exit(1)

    try:
        end_date = date_parser.parse(args.end_date).date()
    except TypeError:
        print "Could not understand end date {0}".format(args.end_date)
        exit(1)

    try:
        assert(end_date > start_date)
    except AssertionError:
        print "End date must be after start date!"
        print "Got: start {0}, end {1}".format(args.start_date, args.end_date)
        exit(1)

    exit(main(start_date, end_date, args.verbose))
