'''read  mls level2 file'''
from datetime import datetime
from dateutil.relativedelta import relativedelta
from h5py import File
import numpy as np


def read_mls_file(mlsfile, date, species, file_index):
    ''' read mls level2 file'''
    file_index = int(file_index)
    mls_datapath = '/vds-data/Aura_MLS_Level2/{0}/v04'.format(*[species])
    mls_datapath = "{0}/{1}/{2}/".format(*[mls_datapath, date[0:4], date[5:7]])
    data = dict()
    data_fields = dict()
    geolocation_fields = dict()
    with File(mls_datapath + mlsfile, 'r') as fgr:
        if species == 'T':
            fdata = fgr['HDFEOS']['SWATHS']['Temperature']
        else:
            fdata = fgr['HDFEOS']['SWATHS'][species]
        for item in fdata['Data Fields']:
            data_fields[item] = np.array(fdata['Data Fields'][item])

        for item in fdata['Geolocation Fields']:
            geolocation_fields[item] = np.array(
                fdata['Geolocation Fields'][item])

    # transform the mls date to MJD and add to dict
    mjd = []
    mls_date0 = datetime(1993, 1, 1)
    for time_i in geolocation_fields['Time']:
        date_i = mls_date0 + relativedelta(seconds=time_i)
        mjd_i = date_i - datetime(1858, 11, 17)
        sec_per_day = 24*60*60.0
        mjd.append(mjd_i.total_seconds() / sec_per_day)
    geolocation_fields['MJD'] = np.array(mjd)

    data['data_fields'] = data_fields
    data['geolocation_fields'] = geolocation_fields

    # select data from the given index
    for item in data['data_fields']:
        data['data_fields'][item] = data['data_fields'][
            item][file_index].tolist()
    for item in data['geolocation_fields']:
        if item not in ['Pressure']:
            data['geolocation_fields'][item] = data[
                'geolocation_fields'][item][file_index].tolist()
        else:
            data['geolocation_fields'][item] = data[
                'geolocation_fields'][item].tolist()
    return data
