#!/usr/bin/env bash
set -eu
find . -type d -name __pycache__ \
     -o \( -type f -name '*.py[co]' \) -print0 \
    | xargs -0 rm -rf
docker build --build-arg uid=$UID -t odinapi-testenv -f ./unittests/Dockerfile .
docker run -u $UID -v "$PWD:/odinapi" -w /odinapi --rm odinapi-testenv ./unittests/test.sh "$@"
