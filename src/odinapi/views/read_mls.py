import os
import numpy as N
import h5py 
from datetime import datetime
from dateutil.relativedelta import relativedelta

def read_mls_file(file,file_index):

    mls_datapath = '/home/bengt/work/odin_reprocessing/vds/data/mls/O3/v04'
    mls_datapath = '/var/lib/odindata/MLS/'

    #ls '/var/lib/odindata/MLS/'
    #year = '2015'
    #month = '01'
    #datapath = "{0}/{1}/{2}/".format(*[mls_datapath,year,month])
    ifile = mls_datapath + file
    data = dict()
    data_fields = dict()
    geolocation_fields = dict()

    f = h5py.File(ifile, 'r')
    fdata = f['HDFEOS']['SWATHS']['O3']

    for item in fdata['Data Fields'].keys():
        data_fields[item] = N.array(fdata['Data Fields'][item])

    for item in fdata['Geolocation Fields'].keys():
        geolocation_fields[item] = N.array(fdata['Geolocation Fields'][item])

    f.close()
    # transform the mls date to MJD and add to dict
    mjd = []
    mls_date0 = datetime(1993,1,1)
    mjd0 = datetime(1858,11,17)
    for time_i in geolocation_fields['Time']:
        date_i = mls_date0 + relativedelta(seconds = time_i)
        mjd_i = date_i - datetime(1858,11,17)
        sec_per_day = 24*60*60.0
        mjd.append( mjd_i.total_seconds()/sec_per_day )
    geolocation_fields['MJD'] = mjd

    data['data_fields'] = data_fields
    data['geolocation_fields'] = geolocation_fields

    return data


