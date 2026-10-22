#!/bin/bash
# Chay: docker compose exec db bash /work/load_osm.sh
# Tai duong pho khu Thu Duc tu OpenStreetMap -> bang ways (pgRouting) -> gan tram gan nhat
set -e
BBOX="10.80,106.72,10.88,106.80"   # (nam, tay, bac, dong) quanh tram mua Thu Duc
OSM=/osm/thuduc.osm

if [ ! -s "$OSM" ]; then
  echo ">> Tai OSM tu Overpass (1-3 phut)..."
  curl -sS -o "$OSM" --data-urlencode \
    "data=[out:xml][timeout:300];(way[\"highway\"]($BBOX);>;);out body;" \
    https://overpass-api.de/api/interpreter
fi

CONF=$(ls /usr/share/osm2pgrouting/mapconfig_for_cars.xml 2>/dev/null \
       || find / -name 'mapconfig_for_cars.xml' 2>/dev/null | head -1)
echo ">> osm2pgrouting voi config: $CONF"
osm2pgrouting -f "$OSM" -c "$CONF" -d "$POSTGRES_DB" -U "$POSTGRES_USER" \
  -h localhost -W "$POSTGRES_PASSWORD" --clean

echo ">> Gan tram gan nhat (KNN) cho tung doan duong..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -f /work/after_osm.sql
echo ">> Xong."
