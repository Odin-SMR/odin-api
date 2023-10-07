import os
import re
import datetime as DT
from datetime import datetime
import tempfile
from typing import TypedDict

from netCDF4 import Dataset

from odinapi.odin_aws.s3 import s3_fileobject, s3_stat

from odinapi.utils.time_util import mjd2datetime, datetime2mjd


AVOGADRO = 6.02282e23  # [mol^-1] aovogadros number
Ro = 8.3143  # [J * mol^-1 * K^-1] ideal gas constant


class ZPT(TypedDict):
    ScanID: int
    Z: list[float]
    P: list[float]
    T: list[float]
    latitude: float
    longitude: float
    mjd: float


def load_zptfile(filepath: str, scanid: int):
    with tempfile.NamedTemporaryFile(suffix=".nc") as tmp:
        buffer = s3_fileobject(filepath)
        if not buffer:
            return None
        tmp.write(buffer.read())
        with Dataset(tmp.name) as dataset:
            data = dataset.groups["Data"]
            mjd = datetime2mjd(
                datetime.strptime(dataset.geoloc_datetime, "%Y-%m-%dT%H:%M:%S")
            )
            zpt = ZPT(
                ScanID=scanid,
                Z=data.variables["Z"][:],
                P=data.variables["P"][:],
                T=data.variables["T"][:],
                latitude=float(data.variables["latitude"][:]),
                longitude=float(data.variables["longitude"][:]),
                mjd=mjd,
            )
        return zpt


def get_filename(basedir, date, scanid):
    return os.path.join(basedir, date.strftime("%Y/%m/"), "ZPT_{0}.nc".format(scanid))


def run_donaletty(
    mjd,
    midlat,
    midlon,
    scanid,
    ecmwfpath="s3://odin-era5",
    solardatafile="s3://odin-solar",
    zptpath="s3://odin-zpt",
):
    date = mjd2datetime(mjd)
    filepath = get_filename(zptpath, date, scanid)
    if not s3_stat(filepath):
        pass
    zpt = load_zptfile(filepath, scanid)
    return zpt


def get_latest_ecmf_file():
    """Return the file name of the latest ecmf file"""
    basedir = "/var/lib/odindata/ECMWF"

    def is_digit_dir(name):
        if not os.path.isdir(os.path.join(basedir, name)):
            return False
        if not name.isdigit():
            return False
        return True

    latest_year = list(filter(is_digit_dir, sorted(os.listdir(basedir))))
    if not latest_year:
        return None
    latest_year = latest_year[-1]
    latest_month = sorted(os.listdir(os.path.join(basedir, latest_year)))[-1]
    latest_file = sorted(os.listdir(os.path.join(basedir, latest_year, latest_month)))[
        -1
    ]
    return latest_file


def get_latest_ecmf_date():
    return get_ecmf_file_date(get_latest_ecmf_file())


def get_ecmf_file_date(file_name):
    if not file_name:
        return
    ecmf_pattern = r"\w+_\w+_(?P<date>\d\d\d\d-\d\d-\d\d)-\d\d.nc$"
    match = re.match(ecmf_pattern, file_name)
    if not match:
        raise ValueError("Could not recognize ecmf file: %r" % file_name)
    return match.group("date")
