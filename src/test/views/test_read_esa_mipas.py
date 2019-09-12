from pathlib import Path
import pytest
import numpy as np

from odinapi.views.read_mipas import read_esa_mipas_file


@pytest.fixture
def mipas_basepath():
    p = Path(__file__)
    for p in p.parents:
        if p.name == 'src':
            p = p.parent
            break
    return p / 'data' / 'vds-data' / 'MIP_NL__2P' / 'v7.03'


@pytest.fixture
def get_mipas_data_o3(mipas_basepath):
    return read_esa_mipas_file(
        'MIP_NL__2PWDSI20020731_121351_000060462008_00124_02182_1000_11.nc',
        '2002-07-31',
        'O3',
        basepath=str(mipas_basepath)
    )


def get_mipas_data(mipas_basepath, species):
    return read_esa_mipas_file(
        'MIP_NL__2PWDSI20020731_121351_000060462008_00124_02182_1000_11.nc',
        '2002-07-31',
        species,
        basepath=str(mipas_basepath)
    )


@pytest.mark.parametrize('species,expect', (
    ('O3', ('o3_retrieval_mds', 'scan_geolocation_ads')),
    ('H2O', ('h2o_retrieval_mds', 'scan_geolocation_ads')),
    ('HNO3', ('hno3_retrieval_mds', 'scan_geolocation_ads')),
    ('N2O', ('n2o_retrieval_mds', 'scan_geolocation_ads')),
))
def test_read_esa_mipas_get_correct_group(mipas_basepath, species, expect):
    data = get_mipas_data(mipas_basepath, species)
    assert set(data.keys()) == set(expect)


@pytest.mark.parametrize('group,expect', (
    ('o3_retrieval_mds',
        (
            'dsr_time',
            'dsr_length',
            'quality_flag',
            'conv_id',
            'last_chi2',
            'ig_flag',
            'error_p_t_prop_flag',
            'cond_param',
            'vmr',
            'vmr_var_cov',
            'conc_alt',
            'conc_var_cov',
            'vert_col',
            'vert_col_var_cov',
            'error_p_t_vcm',
            'base_alt',
            'base_vmr',
            'avg_kernel',
        )),
    ('scan_geolocation_ads',
        (
            'dsr_time',
            'attach_flag',
            'loc_first_latitude',
            'loc_first_longitude',
            'loc_last_latitude',
            'loc_last_longitude',
            'loc_mid_latitude',
            'loc_mid_longitude',
            'first_alt',
            'last_alt',
            'local_solar_time',
            'sat_target_azi',
            'target_sun_azi',
            'target_sun_elev',
        )),
))
def test_read_esa_mipas_get_correct_variables(
        get_mipas_data_o3, group, expect):
    assert set(get_mipas_data_o3[group].keys()) == set(expect)


@pytest.mark.parametrize('group,variable,expect', (
    ('o3_retrieval_mds', 'dsr_time', 81433778.551209),
    ('o3_retrieval_mds', 'dsr_length', 5525),
    ('o3_retrieval_mds', 'quality_flag', 0),
    ('o3_retrieval_mds', 'conv_id', 0),
    ('o3_retrieval_mds', 'last_chi2', 1.8843111991882324),
    ('o3_retrieval_mds', 'ig_flag', 15),
    ('o3_retrieval_mds', 'error_p_t_prop_flag', 69),
    ('o3_retrieval_mds', 'cond_param', 1683313152.0),
    ('scan_geolocation_ads', 'dsr_time', 81433778.551209),
    ('scan_geolocation_ads', 'attach_flag', 0),
    ('scan_geolocation_ads', 'loc_first_latitude', 32.753809),
    ('scan_geolocation_ads', 'loc_first_longitude', 146.934238),
    ('scan_geolocation_ads', 'loc_last_latitude', 35.662611),
    ('scan_geolocation_ads', 'loc_last_longitude', 146.685716),
    ('scan_geolocation_ads', 'loc_mid_latitude', 34.190825),
    ('scan_geolocation_ads', 'loc_mid_longitude', 146.818068),
    ('scan_geolocation_ads', 'first_alt', 68.8042029133376),
    ('scan_geolocation_ads', 'last_alt', 8.019649395933623),
    ('scan_geolocation_ads', 'local_solar_time', 22.175346),
    ('scan_geolocation_ads', 'sat_target_azi', 145.155098),
    ('scan_geolocation_ads', 'target_sun_azi', 329.211774),
    ('scan_geolocation_ads', 'target_sun_elev', -31.460635),
))
def test_read_esa_mipas_scalars(get_mipas_data_o3, group, variable, expect):
    assert get_mipas_data_o3[group][variable] == expect


@pytest.mark.parametrize('group,variable,expect', (
    ('o3_retrieval_mds', 'vmr', (16,)),
    ('o3_retrieval_mds', 'vmr_var_cov', (136,)),
    ('o3_retrieval_mds', 'conc_alt', (16,)),
    ('o3_retrieval_mds', 'conc_var_cov', (136,)),
    ('o3_retrieval_mds', 'vert_col', (16,)),
    ('o3_retrieval_mds', 'vert_col_var_cov', (136,)),
    ('o3_retrieval_mds', 'error_p_t_vcm', (16, 16)),
    ('o3_retrieval_mds', 'base_alt', (67,)),
    ('o3_retrieval_mds', 'base_vmr', (67,)),
    ('o3_retrieval_mds', 'avg_kernel', (16, 16)),
))
def test_read_esa_mipas_arrays(get_mipas_data_o3, group, variable, expect):
    assert np.array(get_mipas_data_o3[group][variable]).shape == expect
