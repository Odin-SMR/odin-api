#!/bin/sh

# This script is run by jenkins jobs that uses the diff test template job or
# the build master template job.
set -e

xvfb-run -a tox -- --runslow --junitxml=result.xml $*
npm install
npm update
npm test
