'''read osiris level2 file'''
from datetime import datetime
from os.path import join
import numpy as N
from dateutil.relativedelta import relativedelta
from odinapi.utils.hdf5_util import thread_safe_h5py_file


def read_osiris_file(osiris_file, date, species, file_index):
    '''read osiris level2 file'''
    file_index = int(file_index)
    osiris_file = join(
        '/osiris-data',
        "{0}{1}".format(*[date[0:4], date[5:7]]),
        osiris_file)
    data = dict()
    data_fields = dict()
    geolocation_fields = dict()
    with thread_safe_h5py_file(osiris_file) as fgr:
        fdata = fgr['HDFEOS']['SWATHS'][
            r'OSIRIS\Odin {0}MART'.format(species)]
        for item in fdata['Data Fields'].keys():
            data_fields[item] = N.array(fdata['Data Fields'][item])
        for item in fdata['Geolocation Fields'].keys():
            geolocation_fields[item] = N.array(
                fdata['Geolocation Fields'][item])
    # transform the mls date to MJD and add to dict
    mjd = []
    for time_i in geolocation_fields['Time']:
        date_i = datetime(1993, 1, 1) + relativedelta(seconds=time_i)
        mjd_i = date_i - datetime(1858, 11, 17)
        sec_per_day = 24*60*60.0
        mjd.append(mjd_i.total_seconds()/sec_per_day)
    geolocation_fields['MJD'] = N.array(mjd)
    data['data_fields'] = data_fields
    data['geolocation_fields'] = geolocation_fields
    # select data from the given index
    for item in data['data_fields'].keys():
        data['data_fields'][item] = data[
            'data_fields'][item][file_index].tolist()
    for item in data['geolocation_fields'].keys():
        if item not in ['Altitude', 'RTModel_Altitude']:
            data['geolocation_fields'][item] = data[
                'geolocation_fields'][item][file_index].tolist()
        else:
            data['geolocation_fields'][item] = data[
                'geolocation_fields'][item].tolist()
    return data
