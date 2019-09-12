import pytest
import requests


def test_vds_file4ace_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['ace']['example-file']
        == '/vds-data/ACE_Level2/v2/2004-03/ss2969.nc'
    )


def test_vds_file4mipas_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['mipas']['example-file']
        == '/vds-data/Envisat_MIPAS_Level2/O3/V5/2007/02/MIPAS-E_IMK.200702.V5R_O3_224.nc'  # noqa
    )


def test_vds_file4mipas_esa_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['mipas_esa']['example-file']
        == '/vds-data/MIP_NL__2P/v7.03/2002/07/31/MIP_NL__2PWDSI20020731_121351_000060462008_00124_02182_1000_11.nc'  # noqa
    )


def test_vds_file4mls_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['mls']['example-file']
        == '/vds-data/Aura_MLS_Level2/O3/v04/2009/11/MLS-Aura_L2GP-O3_v04-20-c01_2009d331.he5'  # noqa
    )


def test_vds_file4osiris_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['osiris']['example-file']
        == '/osiris-data/201410/OSIRIS-Odin_L2-O3-Limb-MART_v5-07_2014m1027.he5'  # noqa
    )


def test_vds_file4sageIII_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['sageIII']['example-file']
        == '/vds-data/Meteor3M_SAGEIII_Level2/2002/09/v04/g3a.ssp.00386710v04.h5'  # noqa
    )


def test_vds_file4smiles_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['smiles']['example-file']
        == '/vds-data/ISS_SMILES_Level2/O3/v2.4/2009/11/SMILES_L2_O3_B_008-11-0502_20091112.he5'  # noqa
    )


def test_vds_file4smr_exists(odinapi_service):
    url = '{}/rest_api/v4/config_data/data_files/'.format(odinapi_service)
    data = requests.get(url).json()
    assert (
        data['data']['vds-files']['smr']['example-file']
        == '/odin-smr-2-1-data/SM_AC2ab/SCH_5018_C11DC6_021.L2P'
    )


def test_vds_file4ace_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'ace/T/2004-03-01/ss2969.nc/0/'
    )
    data = requests.get(url).json()
    t0 = data['Data-L2_retreival_grid']['T'][0]
    assert t0 == pytest.approx(214.420, abs=0.001)


def test_vds_file4mipas_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'mipas/O3/2007-02-01/MIPAS-E_IMK.200702.V5R_O3_224.nc/0/'
    )
    data = requests.get(url).json()
    t0 = data['target'][0]
    assert t0 == pytest.approx(0.098, abs=0.001)


def test_vds_file4mipas_esa_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'mipas_esa/O3/2002-07-31/MIP_NL__2PWDSI20020731_121351_000060462008_00124_02182_1000_11.nc/0/'  # noqa
    )
    data = requests.get(url).json()
    assert data['o3_retrieval_mds']['dsr_time'] == pytest.approx(
        81433778.551209, abs=0.001)


def test_vds_file4mls_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'mls/O3/2009-11-01/MLS-Aura_L2GP-O3_v04-20-c01_2009d331.he5/0/'
    )
    data = requests.get(url).json()
    t0 = data['data_fields']['L2gpValue'][0] * 1e8
    assert t0 == pytest.approx(1.909, abs=0.001)


def test_vds_file4smiles_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'smiles/O3/2009-11-01/SMILES_L2_O3_B_008-11-0502_20091112.he5/0/'
    )
    data = requests.get(url).json()
    t0 = data['data_fields']['L2Value'][0] * 1e7
    assert t0 == pytest.approx(1.310, abs=0.001)


def test_vds_file4sageIII_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'sageIII/O3/2002-09-01/g3a.ssp.00386710v04.h5/0/'
    )
    data = requests.get(url).json()
    t0 = data['Temperature'][0]
    assert t0 == pytest.approx(274.028, abs=0.001)


def test_vds_file4osiris_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'osiris/O3/2014-10-01/OSIRIS-Odin_L2-O3-Limb-MART_v5-07_2014m1027.he5/0/'  # noqa
    )
    data = requests.get(url).json()
    t0 = data['data_fields']['O3'][12] * 1e7
    assert t0 == pytest.approx(1.717, abs=0.001)


def test_vds_file4smr_is_readable(odinapi_service):
    url = (
        '{}/rest_api/v4/vds_external/'.format(odinapi_service)
        + 'smr/O3/2002-09-01/SM_AC2ab-SCH_5018_C11DC6_021.L2P/0/'
    )
    data = requests.get(url).json()
    t0 = data['Data']['Profiles'][0] * 1e11
    assert t0 == pytest.approx(1.250, abs=0.001)
