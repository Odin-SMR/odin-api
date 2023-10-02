from datetime import datetime

from dateutil.relativedelta import relativedelta
from h5py import File
import numpy as np


def read_smiles_file(
    file,
    date,
    species,
    file_index,
    smiles_basepath_pattern="/vds-data/ISS_SMILES_Level2/{0}/v2.4",
):
    file_index = int(file_index)
    smiles_datapath = smiles_basepath_pattern.format(species)

    year = date[0:4]
    month = date[5:7]
    smiles_datapath = "{0}/{1}/{2}/".format(smiles_datapath, year, month)

    ifile = smiles_datapath + file
    data = dict()
    data_fields = dict()
    geolocation_fields = dict()

    with File(ifile, "r") as f:
        fdata = f["HDFEOS"]["SWATHS"][species]

        for key in fdata["Data Fields"]:
            data_fields[key] = np.array(fdata["Data Fields"][key])

        for key in fdata["Geolocation Fields"]:
            geolocation_fields[key] = np.array(fdata["Geolocation Fields"][key])

    # transform the mls date to MJD and add to dict
    mjd = []
    smiles_date0 = datetime(1958, 1, 1)
    for time_i in geolocation_fields["Time"]:
        date_i = smiles_date0 + relativedelta(seconds=time_i)
        mjd_i = date_i - datetime(1858, 11, 17)
        sec_per_day = 24 * 60 * 60.0
        mjd.append(mjd_i.total_seconds() / sec_per_day)
    geolocation_fields["MJD"] = np.array(mjd)

    data["data_fields"] = data_fields
    data["geolocation_fields"] = geolocation_fields

    # select data from the given index
    for key in data["data_fields"]:
        data["data_fields"][key] = data["data_fields"][key][file_index].tolist()

    geoloc = data["geolocation_fields"]
    for key in geoloc:
        if key not in ["Altitude"]:
            try:
                geoloc[key] = geoloc[key][file_index].tolist()
            except AttributeError:
                geoloc[key] = geoloc[key][file_index]
                if isinstance(geoloc[key], bytes):
                    geoloc[key] = geoloc[key].decode()
        else:
            geoloc[key] = geoloc[key].tolist()
    return data
