import os
import numpy as N
import h5py 
from datetime import datetime
from dateutil.relativedelta import relativedelta

def read_mls_file(file, species):

    data = dict()
    data_fields = dict()
    geolocation_fields = dict()

    f = h5py.File(ifile, 'r')
    fdata = f['HDFEOS']['SWATHS'][species]

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

    for species in ['CO', 'ClO', 'H2O', 'HNO3', 'N2O', 'O3']:

        mls_datapath = '/odin/external/vds-data/Aura_MLS_Level2/{0}/v04'.format(*[species])
        mls_datapath = '/vds-data/Aura_MLS_Level2/{0}/v04'.format(*[species])
   
        for year in range(2004,2016):
            for month in range(1,13):
                scaninfo = []
                datapath = "{0}/{1}/{2:02}/".format(*[mls_datapath,year,month])
                files = os.listdir(datapath)
                if len(files)==0: 
                    continue

                for file in files:
                    ifile = datapath + file
                    data = read_mls_file(ifile, species)
    
                    for ind, mjd in enumerate(data['geolocation_fields']['MJD']):
                        temp = [ 
                             species, 
                             file, 
                             ind, 
                             data['geolocation_fields']['Latitude'][ind],
                             data['geolocation_fields']['Longitude'][ind],
                             data['geolocation_fields']['MJD'][ind],
                               ]
                        line = "{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}\n".format(*temp)                 
                        scaninfo.append(line)
           
                outfile ="/vds-data/scanpos/Aura_MLS_scanpos_{0}_{1}{2:02}.txt".format(*[species,year,month])
                print outfile
                f = open(outfile, 'w')
                f.writelines(scaninfo)
                f.close() 
