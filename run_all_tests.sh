#!/bin/sh

# This script is run by jenkins jobs that uses the diff test template job or
# the build master template job.
set -e

./run_unittests.sh -- --runslow --junitxml=result.xml "$@"

npm install
npm update
npm test

./run_systemtests.sh -- --runslow --junitxml=result.xml "$@"
