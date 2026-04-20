#!/bin/bash
set -e

VPS_IP="178.104.239.190"
PRICES_FILE="/tmp/pumpr_prices_sync.sql"
STATIONS_FILE="/tmp/pumpr_stations_sync.sql"

echo "$(date) - Starting incremental sync to VPS"

# Export recent prices
docker exec pumpr_db psql -U pumpr pumpr -c \
  "COPY (SELECT station_id, fuel_type, price_pence, recorded_at, source_updated_at, price_flagged 
         FROM price_history 
         WHERE recorded_at > NOW() - INTERVAL '2 hours') 
   TO STDOUT WITH CSV HEADER" > "$PRICES_FILE"

# Export stations
docker exec pumpr_db psql -U pumpr pumpr -c \
  "COPY stations TO STDOUT WITH CSV HEADER" > "$STATIONS_FILE"

echo "$(date) - Exported $(wc -l < $PRICES_FILE) prices, $(wc -l < $STATIONS_FILE) stations"

# Copy to VPS
scp -q "$PRICES_FILE" "$STATIONS_FILE" root@$VPS_IP:/tmp/

# Import stations first (prices have FK dependency)
ssh root@$VPS_IP "docker cp /tmp/pumpr_stations_sync.sql pumpr_db:/tmp/pumpr_stations_sync.sql"
ssh root@$VPS_IP "docker exec pumpr_db psql -U pumpr pumpr -c \"
  CREATE TEMP TABLE st_tmp (LIKE stations INCLUDING ALL);
  COPY st_tmp FROM '/tmp/pumpr_stations_sync.sql' WITH CSV HEADER;
  INSERT INTO stations SELECT * FROM st_tmp ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = EXCLUDED.updated_at, permanent_closure = EXCLUDED.permanent_closure, temporary_closure = EXCLUDED.temporary_closure;
\""

# Then import prices
ssh root@$VPS_IP "docker cp /tmp/pumpr_prices_sync.sql pumpr_db:/tmp/pumpr_prices_sync.sql"
ssh root@$VPS_IP "docker exec pumpr_db psql -U pumpr pumpr -c \"
  CREATE TEMP TABLE ph_tmp (station_id TEXT, fuel_type TEXT, price_pence FLOAT, recorded_at TIMESTAMP, source_updated_at TIMESTAMP, price_flagged BOOLEAN);
  COPY ph_tmp FROM '/tmp/pumpr_prices_sync.sql' WITH CSV HEADER;
  INSERT INTO price_history (station_id, fuel_type, price_pence, recorded_at, source_updated_at, price_flagged) SELECT * FROM ph_tmp ON CONFLICT DO NOTHING;
\""

# Cleanup
ssh root@$VPS_IP "rm /tmp/pumpr_prices_sync.sql /tmp/pumpr_stations_sync.sql"
rm "$PRICES_FILE" "$STATIONS_FILE"

echo "$(date) - Sync complete"
