"""help functions to display config data"""

from odinapi.odin_aws.s3 import s3_stat


def get_vds_file_status():
    """returns path to specified vds-file if exists"""
    ace_file = "s3://odin-vds-data/ACE_Level2/v2/2004-03/ss2969.nc"
    mipas_file = "s3://odin-vds-data/Envisat_MIPAS_Level2/O3/V5/2007/02/MIPAS-E_IMK.200702.V5R_O3_224.nc"
    mipas_esa_file = "s3://odin-vds-data/MIP_NL__2P/v7.03/2002/07/31/MIP_NL__2PWDSI20020731_121351_000060462008_00124_02182_1000_11.nc"
    mls_file = "s3://odin-vds-data/Aura_MLS_Level2/O3/v04/2009/11/MLS-Aura_L2GP-O3_v04-20-c01_2009d331.he5"
    smiles_file = "s3://odin-vds-data/ISS_SMILES_Level2/O3/v2.4/2009/11/SMILES_L2_O3_B_008-11-0502_20091112.he5"
    sageiii_file = (
        "s3://odin-vds-data/Meteor3M_SAGEIII_Level2/2002/09/v04/g3a.ssp.00386710v04.h5"
    )
    smr_file = "s3://odin-smr/SMRhdf/Qsmr-2-1/SM_AC2ab/SCH_5018_C11DC6_021.L2P"
    osiris_file = "s3://odin-osiris/Level2/Daily/201410/OSIRIS-Odin_L2-O3-Limb-MART_v5-07_2014m1027.he5"
    vds_files = {
        "ace": ace_file,
        "mipas": mipas_file,
        "mls": mls_file,
        "smiles": smiles_file,
        "sageIII": sageiii_file,
        "smr": smr_file,
        "osiris": osiris_file,
        "mipas_esa": mipas_esa_file,
    }

    for item in vds_files:
        if s3_stat(vds_files[item]):
            vds_files[item] = {"example-file": vds_files[item]}
        else:
            vds_files[item] = ""
    return vds_files


def get_ptz_file_status():
    """returns path to a specified ptz-file if exists"""
    era_file = "s3://odin-era5/2015/01/ei_pl_2015-01-12-00.nc"
    solar_file = "s3://odin-solar/spacedata_observed.parquet"
    ptz_files = {
        "era-interim": era_file,
        "solardata": solar_file,
    }
    for item in ptz_files:
        if s3_stat(ptz_files[item]):
            ptz_files[item] = {"example-file": ptz_files[item]}
        else:
            ptz_files[item] = {"example-file": []}
    return ptz_files


def get_apriori_file_status():
    """returns path to a specified apriori-file if exists"""
    ozone_file = "s3://odin-apriori/apriori_O3.mat"
    apriori_files = {
        "ozone": ozone_file,
    }
    for item in apriori_files:
        if s3_stat(ozone_file):
            apriori_files[item] = {"example-file": apriori_files[item]}
        else:
            apriori_files[item] = {"example-file": []}
    return apriori_files


def get_config_data_files():
    """get data for various file types"""
    data = dict()
    vds_files = get_vds_file_status()
    data["vds-files"] = vds_files
    ptz_files = get_ptz_file_status()
    data["ptz-files"] = ptz_files
    apriori_files = get_apriori_file_status()
    data["apriori-files"] = apriori_files
    return {"data": data}
