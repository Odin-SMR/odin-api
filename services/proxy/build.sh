#!/bin/sh -eux

docker build -t docker2.molflow.com/odin_redo/proxy .
docker push docker2.molflow.com/odin_redo/proxy
