#!/bin/sh
# Runs once on first start of the postgres container: one database per service (RIO_DATABASES="api,catalog,orders").
set -eu
for db in $(echo "${RIO_DATABASES:-}" | tr ',' ' '); do
  echo "creating database $db"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -c "CREATE DATABASE \"$db\" OWNER \"$POSTGRES_USER\""
done
