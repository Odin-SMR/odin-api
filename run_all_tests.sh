#!/bin/sh

# This script is run by jenkins jobs that uses the diff test template job or
# the build master template job.
set -e

echo "--- JAVASCRIPT TESTS ---"
npm install
npm update
npm test
echo "--- UNIT AND INTEGRATION TESTS ---"
virtualenv env --python=python2
export VIRTUAL_ENV="${PWD}/env"
export PATH="${PWD}/env/bin:${PATH}"
pip install -r test-requirements.txt
xvfb-run -a py.test --runslow --junitxml=result.xml src/test $*
echo "--- ODIN SYSTEMTESTS ---"
export PATH="/usr/lib/chromium-browser:${PATH}"
xvfb-run -a py.test --runslow --junitxml=result.xml src/systemtest $*
echo "--- PROXY SYSTEMTESTS ---"
xvfb-run -a py.test --runslow --junitxml=result.xml services/proxy/tests $*
