#!/bin/bash
set -e

VPS_HOST="root@178.104.239.190"
VPS_CONTAINER="pumpr_db"
LOCAL_CONTAINER="pumpr_db"
DB_NAME="pumpr"
DB_USER="pumpr"
DUMP_FILE="/tmp/pumpr_vps_dump.sql"

echo "[$(date)] Starting DB sync from VPS..."

# Dump from VPS
ssh $VPS_HOST "docker exec $VPS_CONTAINER pg_dump -U $DB_USER $DB_NAME" > $DUMP_FILE

echo "[$(date)] Dump complete ($(du -sh $DUMP_FILE | cut -f1)). Restoring locally..."

# Drop and recreate local DB
docker exec $LOCAL_CONTAINER psql -U $DB_USER -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" $DB_NAME

# Restore
cat $DUMP_FILE | docker exec -i $LOCAL_CONTAINER psql -U $DB_USER $DB_NAME

rm -f $DUMP_FILE
echo "[$(date)] Sync complete."
