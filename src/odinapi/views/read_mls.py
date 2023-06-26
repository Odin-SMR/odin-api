"""read  mls level2 file"""
from datetime import datetime

import numpy as np
import s3fs
from dateutil.relativedelta import relativedelta
from h5py import File


def read_mls_file(mlsfile, date, species, file_index):
    """read mls level2 file"""
    file_index = int(file_index)
    mls_datapath = "s3://odin-vds-data/Aura_MLS_Level2/{0}/v04".format(*[species])
    mls_datapath = "{0}/{1}/{2}/".format(*[mls_datapath, date[0:4], date[5:7]])
    data = dict()
    data_fields = dict()
    geolocation_fields = dict()
    s3 = s3fs.S3FileSystem()
    with s3.open(mls_datapath + mlsfile, "r") as f:
        with File(f) as fgr:
            if species == "T":
                fdata = fgr["HDFEOS"]["SWATHS"]["Temperature"]  # type: ignore
            else:
                fdata = fgr["HDFEOS"]["SWATHS"][species]  # type: ignore
            for item in fdata["Data Fields"]:  # type: ignore
                data_fields[item] = np.array(fdata["Data Fields"][item])  # type: ignore

            for item in fdata["Geolocation Fields"]:  # type: ignore
                geolocation_fields[item] = np.array(fdata["Geolocation Fields"][item])  # type: ignore

    # transform the mls date to MJD and add to dict
    mjd = []
    mls_date0 = datetime(1993, 1, 1)
    for time_i in geolocation_fields["Time"]:
        date_i = mls_date0 + relativedelta(seconds=time_i)
        mjd_i = date_i - datetime(1858, 11, 17)
        sec_per_day = 24 * 60 * 60.0
        mjd.append(mjd_i.total_seconds() / sec_per_day)
    geolocation_fields["MJD"] = np.array(mjd)

    data["data_fields"] = data_fields
    data["geolocation_fields"] = geolocation_fields

    # select data from the given index
    for item in data["data_fields"]:
        data["data_fields"][item] = data["data_fields"][item][file_index].tolist()
    for item in data["geolocation_fields"]:
        if item not in ["Pressure"]:
            data["geolocation_fields"][item] = data["geolocation_fields"][item][
                file_index
            ].tolist()
        else:
            data["geolocation_fields"][item] = data["geolocation_fields"][item].tolist()
    return data
