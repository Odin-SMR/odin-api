#!/bin/sh
mkdir -p /root/.postgresql
aws s3 cp s3://odin-psql/postgresql.crt /root/.postgresql/postgresql.crt
aws s3 cp s3://odin-psql/postgresql.key /root/.postgresql/postgresql.key
aws s3 cp s3://odin-psql/root.crt /root/.postgresql/root.crt
chmod 0640 /root/.postgresql/postgresql.key
exec "$@"