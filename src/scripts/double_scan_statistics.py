#! /usr/bin/env python
"""
Part of odin-api, tools to make it happen
"""

import json
import numpy as np
from requests import get
from requests.exceptions import HTTPError
from datetime import date, timedelta
from argparse import ArgumentParser
from dateutil import parser as date_parser
from time import sleep

freqmodeColours = {
    # Websafe colours:
    '0':  '#101010',  # 'Black',
    '1':  '#E6E6FA',  # 'Lavender',
    '2':  '#4169E1',  # 'RoyalBlue',
    '8':  '#800080',  # 'Purple',
    '13': '#B22222',  # 'FireBrick',
    '14': '#228B22',  # 'ForestGreen',
    '17': '#8B4513',  # 'SaddleBrown',
    '19': '#C0C0C0',  # 'Silver',
    '21': '#87CEEB',  # 'SkyBlue',
    '22': '#000080',  # 'Navy',
    '23': '#663399',  # 'RebeccaPurple',
    '24': '#008080',  # 'Teal',
    '25': '#FFD700',  # 'Gold',
    '29': '#4682B4',  # 'SteelBlue',
    '102': '#6495ED',  # 'CornFlowerBlue',
    '113': '#CD5C5C',  # 'IndianRed',
    '119': '#DCDCDC',  # 'Gainsboro',
    '121': '#B0E0E6',  # 'PowderBlue',
}


def make_plots(jsonfile):
    from matplotlib import pyplot as plt
    from matplotlib.dates import datestr2num

    with open(jsonfile, 'r') as fp:
        data = json.load(fp)

    fig1 = plt.figure(1)
    fig1.clf()
    ax1 = fig1.gca()
    ax1.set_title('Number of outliers over time')

    fig2 = plt.figure(2)
    fig2.clf()
    ax2 = fig2.gca()
    ax2.set_title('Fraction of outliers over time')

    outliers_max = 0
    ratios_max = 0
    for fm in data.keys():
        dates = datestr2num(data[fm]['Dates'])
        numspecs = np.array(data[fm]['NumSpec'])
        outliers = (np.array(data[fm]['OutliersHiStd']) +
                    np.array(data[fm]['OutliersLoStd']))
        ratios = (1.0 * outliers) / numspecs

        n_numspecs = numspecs.sum()
        n_outliers = outliers.sum()
        ratio = (1.0 * n_outliers) / n_numspecs

        if outliers.max() > outliers_max:
            outliers_max = outliers.max()

        if ratios.max() > ratios_max:
            ratios_max = ratios.max()

        colour = freqmodeColours[fm]
        ax1.plot(dates, outliers, '.-', color=colour,
                 label='FM {0}: {1}'.format(fm, n_outliers))

        ax2.plot(dates, ratios, '.-', color=colour,
                 label='FM {0}: {1:.2g}'.format(fm, ratio))

    ax1.set_ylim(ymax=2*outliers_max)
    ax2.set_ylim(ymax=2*ratios_max)
    ax1.legend(ncol=2)
    ax2.legend(ncol=2)

    return data


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

        if verbose:
            print "# Got data for {0}".format(current_date.isoformat())

        json_data_day = response.json()
        for freqmode in json_data_day['Info']:
            fm = freqmode["FreqMode"]
            try:
                dataDict[fm]
            except KeyError:
                dataDict[fm] = {}

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
            if verbose:
                print "# Got data for {0}: FM {1}".format(
                    current_date.isoformat(), fm)

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
                dataDict[fm]['Dates'].append(current_date.isoformat())
                dataDict[fm]['NumSpec'].append(numspecs.size)
                dataDict[fm]['OutliersHiStd'].append(outliers_hi_std.size)
                dataDict[fm]['OutliersLoStd'].append(outliers_lo_std.size)
                dataDict[fm]['OutliersHiScale'].append(outliers_hi_scale.size)
                dataDict[fm]['OutliersLoScale'].append(outliers_lo_scale.size)
            except KeyError:
                dataDict[fm]['Dates'] = [current_date.isoformat()]
                dataDict[fm]['NumSpec'] = [numspecs.size]
                dataDict[fm]['OutliersHiStd'] = [outliers_hi_std.size]
                dataDict[fm]['OutliersLoStd'] = [outliers_lo_std.size]
                dataDict[fm]['OutliersHiScale'] = [outliers_hi_scale.size]
                dataDict[fm]['OutliersLoScale'] = [outliers_lo_scale.size]

        if verbose:
            print "# {0} OK".format(current_date.isoformat())

        current_date += step

    filename = "double_scans_{0}_-_{1}_n{2}.json".format(
        start_date.isoformat(), end_date.isoformat(), nstd)
    if verbose:
        print "# All OK, will now write to file {0}".format(filename)

    with open(filename, 'w') as fp:
        json.dump(dataDict, fp)

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
