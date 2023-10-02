import os
from datetime import datetime

from netCDF4 import Dataset, chartostring, num2date


def read_mipas_file(
    file,
    date,
    species,
    file_index,
    basepath_pattern="/vds-data/Envisat_MIPAS_Level2/{0}/V5",
):
    file_index = int(file_index)

    mipas_datapath = basepath_pattern.format(species.upper())

    year = date[0:4]
    month = date[5:7]
    mipas_datapath = "{0}/{1}/{2}/".format(mipas_datapath, year, month)

    ifile = mipas_datapath + file

    data = dict()
    with Dataset(ifile, "r") as fgr:
        time = fgr.variables["time"][file_index]
        if fgr.variables["time"].units == "days since 1970-1-1 0:0:0":
            mjd_i = num2date(time, units=fgr.variables["time"].units) - datetime(
                1858, 11, 17
            )
            sec_per_day = 24 * 60 * 60.0
            data["MJD"] = mjd_i.total_seconds() / sec_per_day
        elif fgr.variables["time"].units == "julian days":
            data["MJD"] = time - 2400000.5

        # select data from the given index
        s1 = fgr.variables["time"].shape[0]
        for key in fgr.variables:
            shape = fgr.variables[key].shape
            if len(shape) == 1:
                entry = fgr.variables[key][file_index]
            elif len(shape) == 2 and shape[0] == s1:
                entry = fgr.variables[key][file_index, :]
            elif len(shape) == 2 and shape[1] == s1:
                entry = fgr.variables[key][:, file_index]
            else:
                entry = fgr.variables[key]

            try:
                data[key] = chartostring(entry).item()
            except ValueError:
                data[key] = entry.tolist()
            except AttributeError:
                data[key] = entry

    return data


def read_esa_mipas_file(
    file,
    date,
    species,
    basepath=os.path.join(
        "/vds-data",
        "MIP_NL__2P",
        "v7.03",
    ),
):
    current_date = datetime.strptime(date, "%Y-%m-%d")
    mipas_file = os.path.join(
        basepath,
        "{}".format(current_date.year),
        "{:02}".format(current_date.month),
        "{:02}".format(current_date.day),
        file,
    )
    data = {"{}_retrieval_mds".format(species.lower()): {}, "scan_geolocation_ads": {}}
    with Dataset(mipas_file, "r") as dataset:
        for group_name in data:
            group = dataset[group_name]
            for variable in group.variables:
                if len(group.variables[variable].shape) > 0:
                    data[group_name][variable] = group.variables[variable][:].tolist()
                else:
                    data[group_name][variable] = group.variables[variable][:].item()
    return data
