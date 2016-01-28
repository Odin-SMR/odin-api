import os
import numpy as N
import netCDF4 as NC 
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pg import DB

class db(DB):
    def __init__(self):
        DB.__init__(self,dbname='odin',user='odinop',host='localhost')

def read_mipas_file(file):

    data = dict()
    fgr = NC.Dataset(file, mode='r')

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
    data['MJD'] = mjd


    return data


if __name__ == "__main__":

    mipas_datapath = '/home/bengt/work/odin_reprocessing/vds/data/mipas/O3/V5R'
    year = '2012'
    month = '01'
    datapath = "{0}/{1}/{2}/".format(*[mipas_datapath,year,month])

    files = os.listdir(datapath)

    con = db()

    for file in files:

        ifile = datapath + file
        data = read_mipas_file(ifile)

        for ind, mjd in enumerate(data['MJD']):

            temp = { 
                'species':     'O3',
                'file':         file,
                'file_index':   ind,
                'latitude':     data['latitude'][ind],
                'longitude':    data['longitude'][ind],
                'mjd':          data['MJD'][ind], 
               }
            tempkeys = [temp['species'],temp['file'],temp['file_index']]

            con.query('''delete from mipas_scan 
                     where species='{0}' and file='{1}' and file_index='{2}'
                     '''.format(*tempkeys))

            con.insert('mipas_scan',temp)


    con.close()

