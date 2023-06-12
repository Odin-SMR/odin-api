#!/bin/sh -eux
# Compiles c and python bindings
# and then copies them to the expected directory
# it only requires numpy
DIRECTORY=$(find . -name msis90.py)
VIEWS=$(dirname $DIRECTORY)
cd $VIEWS \
    && python3.8 -m numpy.f2py nrlmsise00/nrlmsise00_sub.for -m nrlmsis -h nrlmsis.pyf --overwrite-signature \
    && python3.8 -m numpy.f2py -c nrlmsis.pyf nrlmsise00/nrlmsise00_sub.for
