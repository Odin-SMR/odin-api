import argparse
import attr
import json
import os
import sys
import datetime as dt
from dateutil.relativedelta import relativedelta
from typing import List, Optional

from odinapi.utils import smrl2filewriter


MONTHS = 3  # generate files until now - MONTHS


@attr.s
class ProductConf:
    project = attr.ib(type=str)
    product = attr.ib(type=str)
    freqmode = attr.ib(type=int)
    start = attr.ib(type=dt.datetime)
    end = attr.ib(type=dt.datetime)
    outdir = attr.ib(type=str)
    product_label = attr.ib(type=str)


def set_end(end: Optional[str]) -> dt.datetime:
    if end is not None:
        return dt.datetime.strptime(end, '%Y-%m-%d')
    now = dt.datetime.utcnow()
    return (
        dt.datetime(now.year, now.month, 1)
        - relativedelta(months=MONTHS)
        - relativedelta(days=1)
    )


def load_config(configfile: str) -> List[ProductConf]:
    with open(configfile, 'r') as jsonfile:
        data = json.load(jsonfile)
    return [
        ProductConf(
            product["project"],
            product["product"],
            int(product["freqmode"]),
            dt.datetime.strptime(product["start"], '%Y-%m-%d'),
            set_end(product["end"]),
            product["outdir"],
            product.get("product_label", product["product"]),
        )
        for product in data["products"]
    ]


def cli(argv: List = []) -> None:
    parser = argparse.ArgumentParser(
        description="Generates Odin/SMR level2 monthly product files.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "configfile",
        type=str,
        help=(
            'config file in json format specifying what products to process,\n'
            'format example:\n'
            '{\n'
            '    "products": [\n'
            '        {\n'
            '            "project": "ALL-Strat-v3.0.0",\n'
            '            "product": "ClO / 501 GHz / 20 to 55 km",\n'
            '            "freqmode": "1",\n'
            '            "start": "2002-01-01",\n'
            '            "end": null,\n'
            '            "outdir": "ALL-Strat-v3.0.0"\n'
            '        }\n'
            '    ]\n'
            '}\n'
            'end will be set to 4 months from now if end is given as null'
        )
    )
    parser.add_argument(
        "baseoutdir",
        type=str,
        help=(
            "base data directory for saving output,\n"
            "datafiles will end up in the product specific outdir "
            "under the baseoutdir directory"
        )
    )
    args = parser.parse_args(argv)
    products_config = load_config(args.configfile)
    for conf in products_config:
        smrl2filewriter.cli([
            conf.project,
            conf.product,
            str(conf.freqmode),
            conf.start.strftime("%Y-%m-%d"),
            conf.end.strftime("%Y-%m-%d"),
            conf.product_label,
            "-q",
            os.path.join(args.baseoutdir, conf.outdir),
        ])


if __name__ == "__main__":
    cli(sys.argv[1:])
