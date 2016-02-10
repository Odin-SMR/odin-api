#! /usr/bin/env python
"""
Part of odin-api, tools to make it happen
"""

import numpy as np
from requests import get
from requests.exceptions import HTTPError
from datetime import date, timedelta
from argparse import ArgumentParser
from dateutil import parser as date_parser
from time import sleep


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
    """Script to look for double scans in the 'cached' info table."""

    max_retries = 3
    nstd = 3
    scale = np.sqrt(2)
    sleep_time = 60
    step = timedelta(days=1)
    current_date = start_date
    dataDict = {}

    while (current_date <= end_date):
        url_day = (
            'http://odin.rss.chalmers.se/'
            'rest_api/v4/freqmode_info/{}/'.format(current_date.isoformat())
            )
        response = get(url_day, timeout=666)
        retries = max_retries
        while (retries > 0):
            try:
                response.raise_for_status()
                break
            except HTTPError, msg:
                print current_date, msg, url_day
                retries -= 1
                print "# Retries left {0}".format(retries)
                sleep(sleep_time * 2 ** (max_retries - retries - 1))

        if (retries == 0):
            print "# FAILED:", current_date, url_day
            continue

        json_data_day = response.json()
        for freqmode in json_data_day['Info']:
            try:
                dataDict[freqmode]
            except KeyError:
                dataDict[freqmode] = {}

            url_scan = (
                'http://odin.rss.chalmers.se/'
                'rest_api/v4/freqmode_info/{0}/{1}/{2}/'.format(
                    current_date.isoformat(),
                    freqmode['Backend'],
                    freqmode['FreqMode'])
                )
            retries = max_retries
            while (retries > 0):
                response = get(url_scan, timeout=666)
                try:
                    response.raise_for_status()
                    break
                except HTTPError, msg:
                    print current_date, msg, url_scan
                    retries -= 1
                    print "# Retries left {0}".format(retries)
                    sleep(sleep_time * 2 ** (max_retries - retries - 1))
            if (retries == 0):
                print "# FAILED:", current_date, url_day
                continue

            json_data_scan = response.json()
            numspecs = []
            for scan in json_data_scan['Info']:
                numspecs.append(scan["NumSpec"])
            numspecs = np.array(numspecs)
            median = np.median(numspecs)
            std = np.std(numspecs)
            outliers_hi_std = np.where(numspecs > median + nstd * std)[0]
            outliers_lo_std = np.where(numspecs < median - nstd * std)[0]
            outliers_hi_scale = np.where(numspecs > median * scale)[0]
            outliers_lo_scale = np.where(numspecs < median / scale)[0]
            try:
                dataDict[freqmode]['Dates'].append(current_date.isoformat())
                dataDict[freqmode]['NumSpec'].append(numspecs.size)
                dataDict[freqmode]['OutliersHiStd'].append(
                    outliers_hi_std.size)
                dataDict[freqmode]['OutliersLoStd'].append(
                    outliers_lo_std.size)
                dataDict[freqmode]['OutliersHiScale'].append(
                    outliers_hi_scale.size)
                dataDict[freqmode]['OutliersLoScale'].append(
                    outliers_lo_scale.size)
            except KeyError:
                dataDict[freqmode]['Dates'] = [current_date.isoformat()]
                dataDict[freqmode]['NumSpec'] = [numspecs.size]
                dataDict[freqmode]['OutliersHiStd'] = [outliers_hi_std.size]
                dataDict[freqmode]['OutliersLoStd'] = [outliers_lo_std.size]
                dataDict[freqmode]['OutliersHiScale'] = [
                    outliers_hi_scale.size]
                dataDict[freqmode]['OutliersLoScale'] = [
                    outliers_lo_scale.size]

        if verbose:
            print current_date, "# OK"
        current_date += step

    save(dataDict)

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
