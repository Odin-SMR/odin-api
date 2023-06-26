"""read ace level2 file"""
import tempfile

import boto3
import numpy as np
from netCDF4 import Dataset  # type: ignore


def read_ace_file(acefile, date, file_index):
    """read ace level2 file"""
    file_index = int(file_index)
    ace_datapath = "/ACE_Level2/v2/{0}-{1}/".format(*[date[0:4], date[5:7]])
    s3 = boto3.client("s3")

    with tempfile.NamedTemporaryFile(suffix=".nc") as tmp:
        s3.download_fileobj("odin-vdc-data", ace_datapath + acefile, tmp)
        tmp.seek(0)

        with Dataset(tmp.name, "r") as fgr:
            data = dict()
            for group in fgr["ACE-FTS-v2.2"].groups:
                if group in ["Geometry"]:
                    continue
                data[group] = dict()
                for variable in fgr["ACE-FTS-v2.2"][group].variables:
                    if variable in [
                        "H2O",
                        "H2O_err",
                        "CO",
                        "CO_err",
                        "NO",
                        "NO_err",
                        "N2O",
                        "N2O_err",
                        "O3",
                        "O3_err",
                        "P",
                        "T",
                        "T_fit",
                        "dens",
                        "z",
                    ]:
                        data[group][variable] = np.array(
                            fgr["ACE-FTS-v2.2"][group][variable],
                        ).tolist()
            data["Attributes"] = dict()
            for att in fgr["ACE-FTS-v2.2"].ncattrs():
                data["Attributes"][att] = np.array(
                    getattr(fgr["ACE-FTS-v2.2"], att)
                ).tolist()

    return data
