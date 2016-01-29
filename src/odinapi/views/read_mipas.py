import os
import numpy as N
import netCDF4 as NC 
from datetime import datetime
from dateutil.relativedelta import relativedelta


def read_mipas_file(file, file_index):

    file_index = int(file_index)

    mipas_datapath = '/var/lib/odindata/MIPAS/'
    #mipas_datapath = '/home/bengt/work/odin-api/data/MIPAS/'
    ifile = mipas_datapath + file

    data = dict()
    fgr = NC.Dataset(ifile, mode='r')

    data = dict()
    for item in fgr.variables.keys():
        data[item] = N.array(fgr.variables[item][:])
    fgr.close()

    # transform the mipas date to MJD and add to dict
    mjd = []
    mipas_date0 = datetime(1970,1,1)
    mjd0 = datetime(1858,11,17)
    for time_i in data['time']:
        date_i = mipas_date0 + relativedelta(days = time_i)
        mjd_i = date_i - datetime(1858,11,17)
        sec_per_day = 24*60*60.0
        mjd.append( mjd_i.total_seconds()/sec_per_day )
    data['MJD'] = N.array(mjd)

    # select data from the given index
    s1 = data['time'].shape[0]
    for item in data.keys():

        if len(data[item].shape) == 1:
            data[item] = data[item][file_index].tolist()

        elif len(data[item].shape) == 2 and data[item].shape[0]==s1:
            data[item] = data[item][file_index,:].tolist()

        elif len(data[item].shape) == 2 and data[item].shape[1]==s1:
            data[item] = data[item][:,file_index].tolist()

    return data


if 0:
    file = 'MIPAS-E_IMK.201201.V5R_O3_225.nc'
    file_index = '502'  
    data = read_mipas_file(file, file_index)
    #print data
