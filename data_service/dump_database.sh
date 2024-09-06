#!/usr/bin/env bash

# Dump the non-PostgreSQL default tables, but only their schemas (so we don't end up dumping loads of data)
sudo -u postgres pg_dump --exclude-schema="(pg_catalog|pg_toast|information_schema)" --no-owner --schema-only elementaldb > elementaldb_tables.sql 
# and dump the minimal client data we need as well
sudo -u postgres pg_dump -t "client_info.*" -t "optimisation.optimisers" -t "heating.interventions" --data-only --attribute-inserts elementaldb --no-comments > elementaldb_client_info.sql
sudo -u postgres pg_dump -t "client_meters.*" --data-only elementaldb --no-comments > elementaldb_client_meters.sql