#! /usr/bin/env python
"""File for batch running L2 NetCDF creation"""
import sys
from argparse import ArgumentParser
import itertools

import requests

import scripts.smrl2filewriter as smrl2filewriter


GRID_TYPES = {
    'nominal': [False],
    'cci': [True],
    'both': [False, True]
}


def setup_arguments():
    """setup command line arguments"""
    parser = ArgumentParser(description="Create odin/smr level2 file")
    parser.add_argument("-r", "--project", dest="project",
                        action="store",
                        type=str,
                        default='meso',
                        help="level2 processing project "
                        "(default: meso)")
    parser.add_argument("-p", "--product", dest="product",
                        action="store",
                        type=str,
                        default='all',
                        help="level2 product of project or 'all'"
                        "(default: 'all')")
    parser.add_argument("-f", "--freqmode", dest="freqmode",
                        action="store",
                        type=int,
                        default=13,
                        help="frequency mode of observation "
                        "(default: 13)")
    parser.add_argument("-y", "--start_year", dest="start_year",
                        action="store",
                        type=int,
                        default=2007,
                        help="start year of observation "
                        "(default: 2007)")
    parser.add_argument("-Y", "--end_year", dest="end_year",
                        action="store",
                        type=int,
                        default=2007,
                        help="start year of observation "
                        "(inclusive, default: 2007)")
    parser.add_argument("-m", "--start_month", dest="start_month",
                        action="store",
                        type=int,
                        default=5,
                        help="start month of observations "
                        "(default: 1)")
    parser.add_argument("-M", "--end_month", dest="end_month",
                        action="store",
                        type=int,
                        default=12,
                        help="end month of observations "
                        "(inclusive, default: 12)")
    parser.add_argument("-t", "--pgrid_type", dest="pgrid_type",
                        action="store",
                        default='nominal',
                        choices=['nominal', 'cci', 'both'],
                        help="pressure grid type "
                        "(default: 'both')")
    parser.add_argument("-d", "--debug", dest="debug",
                        action="store_true",
                        default=False,
                        help="option for testing that script works "
                        "(default: False)")

    args = parser.parse_args()
    return args


def get_products(args):
    """Get list of products to include"""
    url = (
        'http://malachite.rss.chalmers.se/' +
        'rest_api/v5/level2/development/' +
        '{0}/products/'.format(args.project)
    )
    products = requests.get(url).json()['Data']
    if args.product == 'all':
        return products
    else:
        if args.product in products:
            return [args.product]
        else:
            print(
                "Specified product not found, pick one of "
                "\n{products}\n"
                "or 'all'!".format(products=products)
            )
            sys.exit(1)


def loop_generator(args):
    """Convenience loop function"""
    years = range(args.start_year, args.end_year+1)
    months = range(args.start_month, args.end_month+1)
    grids = GRID_TYPES[args.pgrid_type]
    products = get_products(args)
    return itertools.product(years, months, grids, products)


def main(args):
    """Loop over period, products and gridtypes as requested and produce files
    """
    dbcon = smrl2filewriter.Dbcon()
    for year, month, grid, product in loop_generator(args):
        print "Creating file for {year}-{month}: {prod} (CCI: {cci})".format(
            year=year, month=month, prod=product, cci=grid)
        smrl2filewriter.create_l2_file(
            dbcon, args.project, args.freqmode, product, year, month,
            use_pgrid_cci=grid, debug=False
        )
    dbcon.close()


if __name__ == "__main__":

    ARGS = setup_arguments()
    sys.exit(main(ARGS))
