#!/bin/bash

# Execute only the upwards migrations, including the initial one.
# These are stored in the migrations directory
# We do it this way as the postgres init script will not allow us to copy
# SQL files (once it's detected this script, it stops!).
for fname in  /migrations/*.up.sql; do
    psql -U $POSTGRES_USER -d $POSTGRES_DB -a -f "$fname"
done