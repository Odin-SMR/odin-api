import os
import numpy as N
import h5py 
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odinapi.database import DatabaseConnector


def read_mls_file(file):

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


if __name__ == "__main__":

    mls_datapath = '/home/bengt/work/odin_reprocessing/vds/data/mls/O3/v04'
    year = '2015'
    month = '01'
    datapath = "{0}/{1}/{2}/".format(*[mls_datapath,year,month])

    files = os.listdir(datapath)

    con = DatabaseConnector()

    for file in files:

        ifile = datapath + file
        data = read_mls_file(file)

        for ind, mjd in enumerate(data['geolocation_fields']['MJD']):

            temp = { 
                'species':     'O3',
                'file':         file,
                'file_index':   ind,
                'latitude':     data['geolocation_fields']['Latitude'][ind],
                'longitude':    data['geolocation_fields']['Longitude'][ind],
                'mjd':          data['geolocation_fields']['MJD'][ind], 
               }

            tempkeys = [temp['species'],temp['file'],temp['file_index']]

            con.query('''delete from mls_scan 
                     where species='{0}' and file='{1}' and file_index='{2}'
                     '''.format(*tempkeys))

            con.insert('mls_scan',temp)


    con.close()

