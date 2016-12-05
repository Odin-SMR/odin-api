import numpy as N
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odinapi.utils.hdf5_util import thread_safe_h5py_file


def read_smiles_file(file, date, species, file_index):

    file_index = int(file_index)
    smiles_datapath = '/vds-data/ISS_SMILES_Level2/{0}/v2.4'.format(*[species])

    year = date[0:4]
    month = date[5:7]
    smiles_datapath = "{0}/{1}/{2}/".format(*[smiles_datapath, year, month])

    ifile = smiles_datapath + file
    data = dict()
    data_fields = dict()
    geolocation_fields = dict()

    with thread_safe_h5py_file(ifile) as f:
        fdata = f['HDFEOS']['SWATHS'][species]

        for item in fdata['Data Fields'].keys():
            data_fields[item] = N.array(fdata['Data Fields'][item])

        for item in fdata['Geolocation Fields'].keys():
            geolocation_fields[item] = N.array(
                fdata['Geolocation Fields'][item])

    # transform the mls date to MJD and add to dict
    mjd = []
    smiles_date0 = datetime(1958, 1, 1)
    for time_i in geolocation_fields['Time']:
        date_i = smiles_date0 + relativedelta(seconds=time_i)
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
        if item not in ['Altitude']:
            data['geolocation_fields'][item] = data[
                'geolocation_fields'][item][file_index].tolist()
        else:
            data['geolocation_fields'][item] = data[
                'geolocation_fields'][item].tolist()
    return data
