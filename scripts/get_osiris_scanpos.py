# type: ignore
import os
from datetime import datetime

import h5py
import numpy as N
from dateutil.relativedelta import relativedelta


def read_osiris_file(file, species):

    data = dict()
    data_fields = dict()
    geolocation_fields = dict()

    f = h5py.File(ifile, "r")
    fdata = f["HDFEOS"]["SWATHS"][r"OSIRIS\Odin O3MART"]

    for item in fdata["Data Fields"].keys():
        data_fields[item] = N.array(fdata["Data Fields"][item])

    for item in fdata["Geolocation Fields"].keys():
        geolocation_fields[item] = N.array(fdata["Geolocation Fields"][item])

    f.close()
    # transform the mls date to MJD and add to dict
    mjd = []
    mls_date0 = datetime(1993, 1, 1)
    # mjd0 = datetime(1858, 11, 17)
    for time_i in geolocation_fields["Time"]:
        date_i = mls_date0 + relativedelta(seconds=time_i)
        mjd_i = date_i - datetime(1858, 11, 17)
        sec_per_day = 24 * 60 * 60.0
        mjd.append(mjd_i.total_seconds() / sec_per_day)
    geolocation_fields["MJD"] = mjd

    data["data_fields"] = data_fields
    data["geolocation_fields"] = geolocation_fields

    return data


if __name__ == "__main__":

    for species in ["O3"]:

        # osiris_datapath = '/odin/osiris/Level2/Daily'.format(*[species])
        osiris_datapath = "/osiris-data".format(*[species])

        for year in range(2001, 2015):
            for month in range(1, 13):
                scaninfo = []
                datapath = f"{osiris_datapath}/{year}{month:02d}/"
                try:
                    files = os.listdir(datapath)
                except Exception:
                    continue
                if len(files) == 0:
                    continue

                for file in files:
                    if not file.startswith("OSIRIS-Odin_L2-O3-Limb-MART_v5-07"):
                        continue
                    print(file)
                    ifile = datapath + file
                    try:
                        data = read_osiris_file(ifile, species)
                    except Exception:
                        pass

                    for ind, mjd in enumerate(data["geolocation_fields"]["MJD"]):
                        temp = [
                            species,
                            file,
                            ind,
                            data["geolocation_fields"]["Latitude"][ind],
                            data["geolocation_fields"]["Longitude"][ind],
                            data["geolocation_fields"]["MJD"][ind],
                        ]
                        line = "{0}\t{1}\t{2}\t{3:7.2f}\t{4:7.2f}\t{5:7.4f}\n".format(
                            *temp
                        )
                        scaninfo.append(line)

                outfile = "/vds-data/scanpos/Odin_OSIRIS_scanpos_{species}_{year}{month:02d}.txt"
                print(outfile)
                f = open(outfile, "w")
                f.writelines(scaninfo)
                f.close()
