'''read ace level2 file'''
import numpy as N
from netCDF4 import Dataset  # pylint: disable=E0401


def read_ace_file(acefile, date, file_index):
    '''read ace level2 file'''
    file_index = int(file_index)
    ace_datapath = "/vds-data/ACE_Level2/v2/{0}-{1}/".format(
        *[date[0:4], date[5:7]])
    fgr = Dataset(ace_datapath + acefile, mode='r')
    data = dict()
    for group in fgr['ACE-FTS-v2.2'].groups.keys():
        if group in ['Geometry']:
            continue
        data[group] = dict()
        for variable in fgr['ACE-FTS-v2.2'][group].variables.keys():
            if variable in ['H2O',
                            'H2O_err',
                            'CO',
                            'CO_err',
                            'NO',
                            'NO_err',
                            'N2O',
                            'N2O_err',
                            'O3',
                            'O3_err',
                            'P',
                            'T',
                            'T_fit',
                            'dens',
                            'z']:
                data[group][variable] = N.array(
                    fgr['ACE-FTS-v2.2'][group][variable]).tolist()
    data['Attributes'] = dict()
    for att in fgr['ACE-FTS-v2.2'].ncattrs():
        data['Attributes'][att] = N.array(
            getattr(fgr['ACE-FTS-v2.2'], att)).tolist()
    fgr.close()
    return data
