'''help functions to display config data'''
import os


def get_ace_data():
    '''returns path to a specified ace-file if exists'''
    ace_dir = 'vds-data/'
    ace_file = os.path.join(
        ace_dir,
        'ACE_Level2',
        'v2',
        '2004-03',
        'ss2969.nc'
    )
    ace = dict()
    if os.path.isfile(ace_file):
        ace = {
            'example-file': ace_file,
            }
    else:
        ace = {
            'example-file': [],
            }
    return ace


def get_ecmwf_data():
    '''returns path to a specified ecmwf-file if exists'''
    ecmwf = dict()
    return ecmwf


def get_config_data_files():
    '''get data for various file types'''
    config = dict()
    ace = get_ace_data()
    config['ace-data'] = ace
    ecmwf = get_ecmwf_data()
    config['ecmwf-data'] = ecmwf
    return config
