#!/usr/bin/env python3
"""
A script that retrieves era-interim data
from CDS data server. Note that a file
named .cdsapirc, containg a key, should
be available in the user home directory.
"""
import os
import argparse
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import cdsapi


DATA_BASEDIR = "/ecmwf-data"


# command for retrieving parameters on pressure levels
# Parameter id reference: http://apps.ecmwf.int/codes/grib/param-db
# 60.128   : Potential vorticity
# 129.128  : Geopotential
# 130.128  : Temperature
# 133.128  : Specific humidity
# 138.128  : Vorticity (relative)
# 203.128  : Ozone mass mixing ratio
# 246.128  : Specific cloud liquid water content
PL = {
    "class": "ea",
    "grid": "0.75/0.75",
    "levelist": "1/2/3/5/7/10/20/30/50/70/100/125/150/175/200/225/250/300/350/400/450/500/550/600/650/700/750/775/800/825/850/875/900/925/950/975/1000",  # noqa
    "levtype": "pl",
    "param": "60.128/129.128/130.128/133.128/138.128/203.128/246.128",
    "step": "0",
    "stream": "oper",
    "type": "an",
    "format": "netcdf",
}


# command for retrieving parameters on surface level
# Parameter id reference: http://apps.ecmwf.int/codes/grib/param-db
# 134 : Surface pressure
# 165 : 10 metre U wind component
# 166 : 10 metre V wind component
# 235 : Skin temperature
SFC = {
    "class": "ea",
    "grid": "0.75/0.75",
    "levtype": "sfc",
    "param": "134.128/165.128/166.128/235.128",
    "step": "0",
    "stream": "oper",
    "type": "an",
    "format": "netcdf",
}


def get_dataset_and_settings(levtype, date_start, hour):
    settings = {
        'date': date_start.strftime("%Y-%m-%d"),
        'time': hour,
    }
    if levtype == "pl":
        settings.update(PL)
        dataset = "reanalysis-era5-pressure-levels"
    else:
        settings.update(SFC)
        dataset = "reanalysis-era5-complete"
    return dataset, settings


def download_data(date_start, date_end, levtype, hours):
    while date_start <= date_end:
        target_dir = os.path.join(
            DATA_BASEDIR,
            f"{date_start.year}",
            "{0:02}".format(date_start.month)
        )
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        for hour in hours:
            dataset, settings = get_dataset_and_settings(
                levtype, date_start, hour)
            target_file = "{}_{}_{}-{}.nc".format(
                settings['class'],
                settings['levtype'],
                settings['date'],
                settings['time'],
            )
            target = os.path.join(target_dir, target_file)
            if not os.path.exists(target):
                server = cdsapi.Client()
                server.retrieve(dataset, settings, target)
                exit(0)
        date_start += timedelta(days=1)


def get_default_date_start():
    return (
        datetime.utcnow().date() - timedelta(days=1000)
    ).strftime("%Y-%m-%d")


def get_default_date_end():
    date_end = datetime.utcnow().date() - relativedelta(months=2)
    return (
        datetime(date_end.year, date_end.month, 1) - timedelta(days=1)
    ).strftime("%Y-%m-%d")


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "levtype",
        type=str,
        help="levtype: pl (pressure level) or sfc (surface)",
    )
    parser.add_argument(
        '-s',
        '--date-start',
        dest='date_start',
        type=str,
        default=get_default_date_start(),
        help='''
            start date to download, Format YYYY-MM-DD,
            default is 1000 days from now
        '''
    )
    parser.add_argument(
        '-e',
        '--date-end',
        dest='date_end',
        type=str,
        default=get_default_date_end(),
        help='''
            end date to download, Format YYYY-MM-DD,
            default is the last day in three months
            from now
        '''
    )
    parser.add_argument(
        '-t',
        '--time',
        dest='time',
        type=str,
        default='00/06/12/18',
        help='time to download, ',
    )
    args = parser.parse_args()
    assert args.levtype in ["pl", "sfc"]
    assert set(args.time.split('/')).issubset(
        set(['00', '06', '12', '18']))
    date_start = datetime.strptime(
        args.date_start, '%Y-%m-%d')
    date_end = datetime.strptime(
        args.date_end, '%Y-%m-%d')
    download_data(date_start, date_end, args.levtype, args.time)


if __name__ == "__main__":

    cli()
