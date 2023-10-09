"""read osiris level2 file"""
from datetime import datetime
from os.path import join

import numpy as np
import s3fs  # type: ignore
from dateutil.relativedelta import relativedelta
from h5py import File  # type: ignore

from odinapi.odin_aws.s3 import s3_stat  # type:ignore


def read_osiris_file(osiris_file, date, species, file_index):
    """read osiris level2 file"""
    file_index = int(file_index)
    osiris_file = f"s3://odin-osiris/Level2/Daily/{date[0:4]}{date[5:7]}/{osiris_file}"
    data = dict()
    data_fields = dict()
    geolocation_fields = dict()
    s3 = s3fs.S3FileSystem()
    if s3_stat(osiris_file):
        with s3.open(osiris_file) as f:
            with File(f) as fgr:
                fdata = fgr["HDFEOS"]["SWATHS"][  # type: ignore
                    r"OSIRIS\Odin {0}MART".format(species)
                ]
                for key in fdata["Data Fields"]:  # type: ignore
                    data_fields[key] = np.array(fdata["Data Fields"][key])  # type: ignore
                for key in fdata["Geolocation Fields"]:  # type: ignore
                    geolocation_fields[key] = np.array(
                        fdata["Geolocation Fields"][key]  # type: ignore
                    )  # type: ignore
    # transform the mls date to MJD and add to dict
    mjd = []
    for time_i in geolocation_fields["Time"]:
        date_i = datetime(1993, 1, 1) + relativedelta(seconds=time_i)
        mjd_i = date_i - datetime(1858, 11, 17)
        sec_per_day = 24 * 60 * 60.0
        mjd.append(mjd_i.total_seconds() / sec_per_day)
    geolocation_fields["MJD"] = np.array(mjd)
    data["data_fields"] = data_fields
    data["geolocation_fields"] = geolocation_fields
    # select data from the given index
    for key in data["data_fields"]:
        data["data_fields"][key] = data["data_fields"][key][file_index].tolist()
    for key in data["geolocation_fields"]:
        if key not in ["Altitude", "RTModel_Altitude"]:
            data["geolocation_fields"][key] = data["geolocation_fields"][key][
                file_index
            ].tolist()
        else:
            data["geolocation_fields"][key] = data["geolocation_fields"][key].tolist()
    return data
