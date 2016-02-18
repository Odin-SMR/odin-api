import os
import numpy as N
import h5py 
from datetime import datetime
from dateutil.relativedelta import relativedelta

def read_smiles_file(file, species):

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
    smiles_date0 = datetime(1958,1,1)
    mjd0 = datetime(1858,11,17)
    for time_i in geolocation_fields['Time']:
        date_i = smiles_date0 + relativedelta(seconds = time_i)
        mjd_i = date_i - datetime(1858,11,17)
        sec_per_day = 24*60*60.0
        mjd.append( mjd_i.total_seconds()/sec_per_day )
    geolocation_fields['MJD'] = mjd

    data['data_fields'] = data_fields
    data['geolocation_fields'] = geolocation_fields

    return data


if __name__ == "__main__":

    for species in ['ClO', 'HNO3', 'O3']:

        smiles_datapath = '/vds-data/ISS_SMILES_Level2/{0}/v2.4'.format(*[species])
   
        for year in range(2009,2011):
            for month in range(1,13):
                scaninfo = []
                datapath = "{0}/{1}/{2:02}/".format(*[smiles_datapath,year,month])
                try:
                    files = os.listdir(datapath)
                except:
                    continue

                if len(files)==0: 
                    continue
                for band in ['A','B','C']:
                    scaninfo = []
                    for file in files:
                        if not '_{0}_'.format(*[band]) in file:
                            continue
                        ifile = datapath + file
                        data = read_smiles_file(ifile, species)
    
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
                    if not len(scaninfo) == 0:
                        outfile ="/vds-data/scanpos/ISS_SMILES_scanpos_{0}_{1}_{2}{3:02}.txt".format(*[species,band,year,month])
                        print outfile
                        f = open(outfile, 'w')
                        f.writelines(scaninfo)
                        f.close() 
