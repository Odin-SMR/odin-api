#!/usr/bin/env python
"""
A script that retrieves era-interim data
from ECMWF data server. Note that a file
named .ecmwfapirc, containg a key, should 
be available in the user home directory.
"""

import os
from sys import argv
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from ecmwfapi import ECMWFDataServer

# command for retrieving parameters on pressure levels
#
# Parameter id reference: http://apps.ecmwf.int/codes/grib/param-db
# 60.128   : Potential vorticity
# 129.128  : Geopotential
# 130.128  : Temperature
# 133.128  : Specific humidity
# 138.128  : Vorticity (relative)
# 203.128  : Ozone mass mixing ratio
# 246.128  : Specific cloud liquid water content

cmd_pl={
    "class": "ei",
    "dataset": "interim",
    "date": "2015-09-29",
    "expver": "1",
    "grid": "0.75/0.75",
    "levelist": "1/2/3/5/7/10/20/30/50/70/100/125/150/175/200/225/250/300/350/400/450/500/550/600/650/700/750/775/800/825/850/875/900/925/950/975/1000",
    "levtype": "pl",
    "param": "60.128/129.128/130.128/133.128/138.128/203.128/246.128",
    "step": "0",
    "stream": "oper",
    "target": "./mydocs/2015-09-29.grib",
    "time": "00/06/12/18",
    "type": "an",
    "format": "netcdf",
}

# command for retrieving parameters on surface level
#
# Parameter id reference: http://apps.ecmwf.int/codes/grib/param-db
#
# 134 : Surface pressure          
# 165 : 10 metre U wind component 
# 166 : 10 metre V wind component 
# 235 : Skin temperature          

cmd_sfc={
    "class": "ei",
    "dataset": "interim",
    "date": "2015-09-29",
    "expver": "1",
    "grid": "0.75/0.75",
    "levtype": "sfc",
    "param": "134.128/165.128/166.128/235.128",
    "step": "0",
    "stream": "oper",
    "target": "./mydocs/2015-09-29.grib",
    "time": "00/06/12/18",
    "type": "an",
    "format": "netcdf",
}


def usage():
    print 'Usage: python testecmwf.py levtype date time'
    print 'Examples:'
    print 'retrieve data on pressure levels'
    print 'python get_erainterim_data.py pl 2015-09-29 00/06/12/18'
    print 'retrieve data on surface level'
    print 'python get_erainterim_data.py sfc 2015-09-29 00/06/12/18'
    exit(0)

if __name__ == "__main__":

    #data_basedir = "/misc/pearl/extdata/ERA-Interim/"
    data_basedir = "/ecmwf-data/"

    if len(argv)<4:
        usage()

    levtype = argv[1]
    if levtype == 'pl':
        cmd = cmd_pl
    elif levtype == 'sfc':
        cmd = cmd_sfc
    else:
        usage()

    hours = argv[3].split('/')
    for hour in hours:
        if not hour in ['00','06','12','18']:
            usage()


    date_start = datetime(2001,8,1).date()
    # data time delay is three months
    date_end = datetime.now().date() - relativedelta(months=2)
    date_end = (datetime(date_end.year,date_end.month,1) - timedelta(days=1)).date()
    n = 1000    

    dates = []
    if argv[2]=='?':
        # retrieve data from n days
        ni = 0
        i = 0
        while ni < n:
            candidate_date = date_end - timedelta(days=i)
            # check if file already exists
            year = "{0}".format(candidate_date.year)
            month = "{0:02}".format(candidate_date.month)
            target_dir = os.path.join( data_basedir,year,month )
            date_string = str(candidate_date)[0:10]
            file_already_exists = 0
            for hour in hours:
                target_file = "{0}_{1}_{2}-{3}.nc".format(*[cmd['class'], cmd['levtype'], date_string, hour])
                fullfile = os.path.join( target_dir, target_file)
                if os.path.exists(fullfile):
                    file_already_exists = 1
            i = i + 1
            if candidate_date >= date_start and not file_already_exists:
                ni = ni + 1
                dates.append(candidate_date)
            if candidate_date < date_start:
                break
    else:
        try:
            dates.append(datetime.strptime(argv[2], '%Y-%m-%d'))
        except:
            usage()

    # loop over dates
    for date in dates:
        year = "{0}".format(date.year)
        month = "{0:02}".format(date.month)
        date_string = str(date)[0:10]
        cmd['date'] = date_string
    
    
        # create target directory if not exists
        target_dir = os.path.join( data_basedir,year,month )
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        # loop ove hours 
        for hour in hours:    

            cmd['time'] = hour
            target_file = "{0}_{1}_{2}-{3}.nc".format(*[cmd['class'], cmd['levtype'], cmd['date'], cmd['time']])
            cmd['target'] = os.path.join( target_dir, target_file)
            print cmd['target']

            # check if desired file already exists
            # retrieve data if file not exists
            if not os.path.exists( cmd['target'] ):
                pass
                server = ECMWFDataServer()
                server.retrieve(cmd)



