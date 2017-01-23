#!/usr/bin/env python
# pylint: disable=C0411, C0413
'''preprocess ptz data for a given freqmode and date range'''


from sys import argv
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # this is neededd to import run_donaletty
from odinapi.views.newdonalettyERANC import run_donaletty  # nopep8
from scripts.ptz_util import PrecalcPTZ  # nopep8
import os  # nopep8


def execute_donaletty(midmjd, midlat, midlon, scanid):
    '''run donaletty'''
    try:
        print scanid
        run_donaletty(midmjd, midlat, midlon, scanid)
    except IOError:
        pass


def usage():
    '''usage function'''
    print '''usage: ./ptz_script.py fmode date_start date_stop prod'''
    print '''fmode: integer, if -1, ptz for all fmodes are calculated'''
    print '''date_start format: 2015-01-12'''
    print '''date_end format: 2015-01-31'''
    print '''prod format: 0 or 1'''
    exit(0)

if __name__ == "__main__":
    try:
        FREQMODE = int(argv[1])
        DATE_START = datetime.strptime(argv[2], '%Y-%m-%d')
        DATE_END = datetime.strptime(argv[3], '%Y-%m-%d')
        if DATE_START > DATE_END:
            usage()
        if len(argv) == 5:
            if argv[4] not in ['0', '1']:
                usage()
            if argv[4] == '1':
                # the files are saved with read
                # and write properties for root,
                # otherwise all users have this
                os.environ['ODIN_API_PRODUCTION'] = '1'
                URL_ROOT = 'http://malachite.rss.chalmers.se/rest_api/v5'
            else:
                URL_ROOT = 'http://localhost:5000/rest_api/v5'
    except(IndexError, ValueError):
        usage()
    FPTZ = PrecalcPTZ(URL_ROOT, FREQMODE, DATE_START, DATE_END)
    FPTZ.get_date_range()
    for date_i in FPTZ.date_range:
        print date_i
        for freqmode in FPTZ.get_freqmodes4date(date_i):
            print date_i, freqmode
            FPTZ.get_scandata4dateandfreqmode(date_i, freqmode)
            for scandata in FPTZ.scanlist:
                execute_donaletty(scandata[0],
                                  scandata[1],
                                  scandata[2],
                                  scandata[3])
