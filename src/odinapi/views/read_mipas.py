from datetime import datetime

from dateutil.relativedelta import relativedelta
from netCDF4 import Dataset
import numpy as np


def read_mipas_file(file, date, species, file_index):

    file_index = int(file_index)

    mipas_datapath = '/vds-data/Envisat_MIPAS_Level2/{0}/V5'.format(
        *[species.upper()])

    year = date[0:4]
    month = date[5:7]
    mipas_datapath = "{0}/{1}/{2}/".format(*[mipas_datapath, year, month])

    ifile = mipas_datapath + file

    data = dict()
    with Dataset(ifile, 'r') as fgr:

        for item in fgr.variables.keys():
            data[item] = np.array(fgr.variables[item][:])

        if fgr.variables['time'].units == 'days since 1970-1-1 0:0:0':
            t0_unit = 1
        elif fgr.variables['time'].units == 'julian days':
            t0_unit = 2

    # transform the mipas date to MJD and add to dict
    if t0_unit == 1:

        mjd = []
        mipas_date0 = datetime(1970, 1, 1)
        for time_i in data['time']:
            date_i = mipas_date0 + relativedelta(days=time_i)
            mjd_i = date_i - datetime(1858, 11, 17)
            sec_per_day = 24*60*60.0
            mjd.append(mjd_i.total_seconds()/sec_per_day)
        data['MJD'] = mjd
        data['MJD'] = np.array(data['MJD'])

    elif t0_unit == 2:

        data['MJD'] = np.array(data['time']) - 2400000.5

    # select data from the given index
    s1 = data['time'].shape[0]
    for item in data.keys():

        if len(data[item].shape) == 1:
            data[item] = data[item][file_index].tolist()

        elif len(data[item].shape) == 2 and data[item].shape[0] == s1:
            data[item] = data[item][file_index, :].tolist()

        elif len(data[item].shape) == 2 and data[item].shape[1] == s1:
            data[item] = data[item][:, file_index].tolist()

    return data
