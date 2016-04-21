#!/usr/bin/env python
import os
from sys import argv
from datetime import datetime
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
    print 'python testecmwf.py pl 2015-09-29 00/06/12/18'
    print 'retrieve data on surface level'
    print 'python testecmwf.py sfc 2015-09-29 00/06/12/18'
    exit(0)

if __name__ == "__main__":
    
    data_basedir = "/home/bengt/Downloads/"

    if len(argv)<4:
        usage()

    levtype = argv[1] 
    if levtype == 'pl':
        cmd = cmd_pl
    elif levtype == 'sfc':
        cmd = cmd_sfc
    else:
        usage()
  
    try:
        date=datetime.strptime(argv[2], '%Y-%m-%d')
        year = "{0}".format(date.year)
        month = "{0:02}".format(date.month)
        date_string = str(date)[0:10]

    except:
        usage()

    cmd['date'] = date_string
    cmd['time'] = argv[3]

    target_dir = os.path.join( data_basedir,year,month )
    target_file = "{0}_{1}_{2}.nc".format(*[cmd['class'], cmd['levtype'], cmd['date']])   
    cmd['target'] = os.path.join( target_dir, target_file)
    print cmd['target'] 
       
    # create target directory if not exists
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # check if desired file already exists
    # retrieve data if file not exists
    if not os.path.exists( cmd['target'] ):
        server = ECMWFDataServer()
        server.retrieve(cmd)
