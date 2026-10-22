# SAFE-ROUTE HCMC

He thong dinh tuyen tranh ngap cho TP.HCM (do an chuyen nganh).
Khu vuc MVP: TP. Thu Duc. Du lieu: mua 10 phut (2022-2023), trieu theo ngay (Phu An, Nha Be).

## Kien truc

    data/raw/*.xls --clean_data.py--> data/clean/*.csv --COPY--> PostGIS
    OpenStreetMap --osm2pgrouting--> bang ways --KNN--> segment_station
    compute_risk.py --> road_segment_risk   (HOP DONG giua cac service)
    routing-service (FastAPI + pgr_aStar) --> frontend (Leaflet)

## Chay lan dau (can Docker Desktop)

```bash
# 1. Dung DB + API (lan dau build mat vai phut)
docker compose up -d --build

# 2. Tai duong pho Thu Duc + tao do thi pgRouting + gan tram gan nhat
docker compose exec db bash /work/load_osm.sh

# 3a. Rui ro GIA (de test nhanh giao dien)
docker compose exec db psql -U saferoute -d saferoute -f /work/seed_fake_risk.sql

# 3b. Hoac rui ro THAT tu du lieu (kich ban 3: mua to + trieu cao)
docker compose run --rm api python /app/prediction/compute_risk.py --date 2022-10-24

# 4. Mo trinh duyet
#    http://localhost:8000        -> web ban do
#    http://localhost:8000/docs   -> thu API
```

Reset toan bo DB: `docker compose down -v` roi chay lai tu buoc 1.

Test logic tinh rui ro (khong can Docker): `python prediction-service/test_risk_logic.py`

## Cau truc thu muc

| Thu muc | Noi dung | Phu trach |
|---|---|---|
| data/ | raw (file goc), clean (CSV da lam sach), osm (file OSM tai ve) | A |
| data-ingestion-service/ | clean_data.py | A |
| geospatial-db/ | Dockerfile, schema, nap CSV, nap OSM, KNN | A |
| prediction-service/ | risk_logic.py (bang quyet dinh), compute_risk.py | B |
| routing-service/ | app.py: API /api/route, /api/risk | C |
| frontend/ | index.html (Leaflet) | C |
| docs/ | proposal, data-profile, phan cong | chung |

## Quy uoc chung

- Toa do: WGS84 (SRID 4326). Khoang cach: ep sang geography de ra met.
- Bang road_segment_risk(segment_id = ways.gid, thoi_diem, risk 0..1) la diem giao duy nhat
  giua prediction va routing. Muon doi cau truc bang nay phai bao ca nhom.
- Moi nguoi lam tren branch rieng, merge vao main qua Pull Request.
