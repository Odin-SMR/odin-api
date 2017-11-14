#!/bin/sh

# This script is run by jenkins jobs that uses the build master template job.

set -e

docker build -t docker2.molflow.com/odin_redo/odin_api .
docker push docker2.molflow.com/odin_redo/odin_api
cd services/proxy/
./build.sh
cd -
