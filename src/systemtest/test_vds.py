# pylint: skip-file
import unittest

import pytest
import requests as R

import numpy as np
from .testdefs import system


URL_ROOT = 'http://localhost:5000/'
URL_DATA_FILES = (
    URL_ROOT + 'rest_api/v4/config_data/data_files/'
)
URL_VDS_EXTERNAL = (
    URL_ROOT + 'rest_api/v4/vds_external/'
)


@system
@pytest.mark.usefixtures('dockercompose')
class TestVds(unittest.TestCase):

    def test_vds_file4ace_exists(self):
        """Check that ace file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['vds-files']['ace']['example-file'] ==
            '/vds-data/ACE_Level2/v2/2004-03/ss2969.nc'
        )

    def test_vds_file4mipas_exists(self):
        """Check that mipas file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['vds-files']['mipas']['example-file'] ==
            '/vds-data/Envisat_MIPAS_Level2/' +
            'O3/V5/2007/02/MIPAS-E_IMK.200702.V5R_O3_224.nc'
        )

    def test_vds_file4mls_exists(self):
        """Check that mls file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['vds-files']['mls']['example-file'] ==
            '/vds-data/Aura_MLS_Level2/' +
            'O3/v04/2009/11/MLS-Aura_L2GP-O3_v04-20-c01_2009d331.he5'
        )

    def test_vds_file4osiris_exists(self):
        """Check that osiris file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['vds-files']['osiris']['example-file'] ==
            '/osiris-data/201410/' +
            'OSIRIS-Odin_L2-O3-Limb-MART_v5-07_2014m1027.he5'
        )

    def test_vds_file4sageIII_exists(self):
        """Check that ace file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['vds-files']['sageIII']['example-file'] ==
            '/vds-data/Meteor3M_SAGEIII_Level2/' +
            '2002/09/v04/g3a.ssp.00386710v04.h5'
        )

    def test_vds_file4smiles_exists(self):
        """Check that smiles file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['vds-files']['smiles']['example-file'] ==
            '/vds-data/ISS_SMILES_Level2/' +
            'O3/v2.4/2009/11/SMILES_L2_O3_B_008-11-0502_20091112.he5'
        )

    def test_vds_file4smr_exists(self):
        """Check that smr file exists"""
        data = R.get(URL_DATA_FILES).json()
        self.assertTrue(
            data['data']['vds-files']['smr']['example-file'] ==
            '/odin-smr-2-1-data/SM_AC2ab/SCH_5018_C11DC6_021.L2P'
        )

    def test_vds_file4ace_is_readable(self):
        """Check that odin-api can read ace-file"""
        url_string = (
            URL_VDS_EXTERNAL +
            'ace/T/2004-03-01/ss2969.nc/0/'
        )
        data = R.get(url_string).json()
        t0 = data['Data-L2_retreival_grid']['T'][0]
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 214.420)

    def test_vds_file4mipas_is_readable(self):
        """Check that odin-api can read mipas-file"""
        url_string = (
            URL_VDS_EXTERNAL +
            'mipas/O3/2007-02-01/MIPAS-E_IMK.200702.V5R_O3_224.nc/0/'
        )
        data = R.get(url_string).json()
        t0 = data['target'][0]
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 0.098)

    def test_vds_file4mls_is_readable(self):
        """Check that odin-api can read mls-file"""
        url_string = (
            URL_VDS_EXTERNAL +
            'mls/O3/2009-11-01/MLS-Aura_L2GP-O3_v04-20-c01_2009d331.he5/0/'
        )
        data = R.get(url_string).json()
        t0 = data['data_fields']['L2gpValue'][0] * 1e8
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 1.909)

    def test_vds_file4smiles_is_readable(self):
        """Check that odin-api can read smiles-file"""
        url_string = (
            URL_VDS_EXTERNAL +
            'smiles/O3/2009-11-01/SMILES_L2_O3_B_008-11-0502_20091112.he5/0/'
        )
        data = R.get(url_string).json()
        t0 = data['data_fields']['L2Value'][0] * 1e7
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 1.310)

    def test_vds_file4sageIII_is_readable(self):
        """Check that odin-api can read sageIII-file"""
        url_string = (
            URL_VDS_EXTERNAL +
            'sageIII/O3/2002-09-01/g3a.ssp.00386710v04.h5/0/'
        )
        data = R.get(url_string).json()
        t0 = data['Temperature'][0]
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 274.028)

    def test_vds_file4osiris_is_readable(self):
        """Check that odin-api can read osiris-file"""
        url_string = (
            URL_VDS_EXTERNAL +
            'osiris/O3/2014-10-01/' +
            'OSIRIS-Odin_L2-O3-Limb-MART_v5-07_2014m1027.he5/0/'
        )
        data = R.get(url_string).json()
        t0 = data['data_fields']['O3'][12] * 1e7
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 1.717)

    def test_vds_file4smr_is_readable(self):
        """Check that odin-api can read smr-file"""
        url_string = (
            URL_VDS_EXTERNAL +
            'smr/O3/2002-09-01/SM_AC2ab-SCH_5018_C11DC6_021.L2P/0/'
        )
        data = R.get(url_string).json()
        t0 = data['Data']['Profiles'][0] * 1e11
        t0 = np.around(t0, decimals=3).tolist()
        self.assertTrue(t0 == 1.250)
