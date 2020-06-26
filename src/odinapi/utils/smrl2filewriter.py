#!/usr/bin/env python3
import os
import datetime as dt
import argparse
import attr
from typing import List, Dict, Any
from dateutil.relativedelta import relativedelta
from netCDF4 import Dataset, date2num

from odinapi.database import level2db
from odinapi.views.get_ancillary_data import get_ancillary_data
from odinapi.views.database import DatabaseConnector
from odinapi.utils import datamodel


@attr.s
class L2Getter:
    freqmode = attr.ib(type=int)
    product = attr.ib(type=str)
    db1 = attr.ib(type=DatabaseConnector)
    db2 = attr.ib(type=level2db.Level2DB)

    def get_l2i(self, scanid: int) -> datamodel.L2i:
        return datamodel.to_l2i(self.db2.get_L2i(self.freqmode, scanid))

    def get_l2anc(self, l2: Dict[str, Any]) -> datamodel.L2anc:
        return datamodel.to_l2anc(get_ancillary_data(self.db1, [l2])[0])

    def get_l2full(self, scanid: int) -> datamodel.L2Full:
        l2i = self.get_l2i(scanid)
        l2dict = self.db2.get_L2(self.freqmode, scanid, self.product)[0]
        l2anc = get_ancillary_data(self.db1, l2dict)
        return datamodel.L2Full(
            l2i=l2i, l2anc=l2anc, l2=datamodel.to_l2(l2dict, self.product)
        )

    def get_data(self, scanids: List[int]) -> List[datamodel.L2Full]:
        l2fulls = [self.get_l2full(scanid) for scanid in scanids]
        return [l2full for l2full in l2fulls if l2full.l2i.isvalid()]

    def get_scanids(self, start: dt.datetime, end: dt.datetime) -> List[int]:
        scans = []
        while start < end:
            currentscans = self.db2.get_scans(
                self.freqmode,
                start_time=start,
                end_time=start + relativedelta(days=1)
            )
            for scan in currentscans:
                scans.append(scan["ScanID"])
            start += relativedelta(days=1)
        return scans


@attr.s
class L2FileCreater:
    project = attr.ib(type=str)
    freqmode = attr.ib(type=int)
    product = attr.ib(type=str)
    parameters = attr.ib(type=datamodel.L2File)
    data = attr.ib(type=List[datamodel.L2Full])
    outdir = attr.ib(type=str)

    @property
    def start(self) -> dt.datetime:
        return self.data[0].l2.Time

    @property
    def end(self) -> dt.datetime:
        return self.data[-1].l2.Time

    @property
    def ntimes(self) -> int:
        return len(self.data)

    @property
    def nlevels(self) -> int:
        return len(self.data[0].l2.Profile)

    @property
    def invmode(self) -> str:
        return self.data[0].l2.InvMode

    def filename(self) -> str:
        if not os.path.isdir(self.outdir):
            os.makedirs(self.outdir)
        return os.path.join(
            self.outdir,
            datamodel.generate_filename(
                self.project, self.product, self.start
            )
        )

    @property
    def header(self) -> Dict[str, str]:
        return datamodel.get_file_header_data(
            self.freqmode, self.invmode, self.product, self.start, self.end
        )

    def write_to_file(self) -> None:
        with Dataset(self.filename(), "w", fomat="NETCFD4") as ds:
            ds.createDimension("time", self.ntimes)
            ds.createDimension('level', self.nlevels)
            for para in self.header:
                setattr(ds, para, self.header[para])
            for para in self.parameters:
                nc_var = ds.createVariable(
                    para.name,
                    para.dtype.value,
                    para.dimension.value,
                    zlib=True
                )
                istemp = datamodel.is_temperature(self.product)
                nc_var.description = para.get_description(istemp)
                nc_var.units = para.get_unit(istemp).value
                if para.unit == datamodel.Unit.time:
                    nc_var[:] = date2num(
                        [d.get_data(para) for d in self.data],
                        para.unit.value,
                        calendar='standard'
                    )
                else:
                    nc_var[:] = [d.get_data(para) for d in self.data]


def get_l2data(
    l2getter: L2Getter, start: dt.datetime, end: dt.datetime
) -> List[datamodel.L2Full]:
    scanids = l2getter.get_scanids(start, start + relativedelta(months=1))
    return l2getter.get_data(scanids)


def process_period(
    db1: DatabaseConnector,
    db2: level2db.Level2DB,
    project: str,
    freqmode: int,
    product: str,
    start: dt.datetime,
    end: dt.datetime,
    parameters: datamodel.L2File,
    outdir: str
) -> None:
    l2getter = L2Getter(freqmode, product, db1, db2)
    while start < end:
        data = get_l2data(l2getter, start, start + relativedelta(months=1))
        if len(data) == 0:
            start += relativedelta(months=1)
            continue
        l2writer = L2FileCreater(
            project, freqmode, product, parameters, data, outdir
        )
        l2writer.write_to_file()
        start += relativedelta(months=1)


def cli(argv: List = []) -> None:
    parser = argparse.ArgumentParser(
        description="Generates Odin/SMR level2 monthly product files.",
    )
    parser.add_argument(
        "project",
        type=str,
        help="project name",
    )
    parser.add_argument(
        "products",
        type=str,
        nargs='+',
        help="product name(s), can be more than one name",
    )
    parser.add_argument(
        "freqmode",
        type=str,
        help="frequency mode",
    )
    parser.add_argument(
        "date_start",
        type=str,
        help="start date: format: YYYY-MM-DD",
    )
    parser.add_argument(
        "date_end",
        type=str,
        help="end date: format: YYYY-MM-DD",
    )
    parser.add_argument(
        '-q',
        '--outdir',
        dest='outdir',
        type=str,
        default='/tmp',
        help='data directory for saving output default is /tmp',
    )
    args = parser.parse_args(argv)

    date_start = dt.datetime.strptime(args.date_start, '%Y-%m-%d')
    date_end = dt.datetime.strptime(args.date_end, '%Y-%m-%d')
    db1 = DatabaseConnector()
    db2 = level2db.Level2DB(args.project)
    for product in args.products:
        process_period(
            db1,
            db2,
            args.project,
            args.freqmode,
            product,
            date_start,
            date_end,
            datamodel.L2FILE.parameters,
            args.outdir,
        )


if __name__ == "__main__":
    cli()
