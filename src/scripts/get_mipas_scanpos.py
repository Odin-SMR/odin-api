import os
import numpy as N
import netCDF4 as NC 
from datetime import datetime
from dateutil.relativedelta import relativedelta

def read_mipas_file(file):

    data = dict()
    fgr = NC.Dataset(file, mode='r')

    data = dict()
    for item in fgr.variables.keys():
        data[item] = N.array(fgr.variables[item][:])
    
    if fgr.variables['time'].units == 'days since 1970-1-1 0:0:0':
        t0_unit = 1
    elif fgr.variables['time'].units == 'julian days':
        t0_unit =2 
    else:
        print file
        print 'unknown t0 format'
        exit(0)

    fgr.close()

    # transform the mipas date to MJD and add to dict
    if t0_unit == 1:
 
        mjd = []
        mjd0 = datetime(1858,11,17)
        mipas_date0 = datetime(1970,1,1)
        for time_i in data['time']:
            date_i = mipas_date0 + relativedelta(days = time_i)
            mjd_i = date_i - datetime(1858,11,17)
            sec_per_day = 24*60*60.0
            mjd.append( mjd_i.total_seconds()/sec_per_day )
        data['MJD'] = mjd

    elif t0_unit == 2:

        data['MJD'] =  data['time'] - 2400000.5


    return data


if __name__ == "__main__":

    mipas_datapath = '/vds-data/Envisat_MIPAS_Level2/{0}/V5'

    for species in ['CLO', 'CO', 'H2O', 'HNO3', 'N2O', 'NO', 'O3']:

        mipas_datapath = '/vds-data/Envisat_MIPAS_Level2/{0}/V5'.format(*[species])
   
        for year in range(2002,2013):
            for month in range(1,13):
                scaninfo = []
                datapath = "{0}/{1}/{2:02}/".format(*[mipas_datapath,year,month])
                files = os.listdir(datapath)
                if len(files)==0: 
                    continue

                for file in files:
                    ifile = datapath + file
                    data = read_mipas_file(ifile)
    
                    for ind, mjd in enumerate(data['MJD']):
                        temp = [ 
                             species, 
                             file, 
                             ind, 
                             data['latitude'][ind],
                             data['longitude'][ind],
                             data['MJD'][ind],
                               ]
                        line = "{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}\n".format(*temp)                 
                        scaninfo.append(line)
           
                outfile ="/vds-data/scanpos/Envisat_MIPAS_scanpos_{0}_{1}{2:02}.txt".format(*[species,year,month])
                print outfile
                f = open(outfile, 'w')
                f.writelines(scaninfo)
                f.close() 

