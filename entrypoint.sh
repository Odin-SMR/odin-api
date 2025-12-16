#!/bin/sh
set -e

# Download PostgreSQL certificates from S3
mkdir -p /root/.postgresql

if ! aws s3 cp s3://odin-psql/postgresql.crt /root/.postgresql/postgresql.crt; then
    echo "Error: Failed to download postgresql.crt" >&2
    exit 1
fi

if ! aws s3 cp s3://odin-psql/postgresql.key /root/.postgresql/postgresql.key; then
    echo "Error: Failed to download postgresql.key" >&2
    exit 1
fi

if ! aws s3 cp s3://odin-psql/root.crt /root/.postgresql/root.crt; then
    echo "Error: Failed to download root.crt" >&2
    exit 1
fi

chmod 0640 /root/.postgresql/postgresql.key

exec "$@"