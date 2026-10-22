"""
Routing API. Mo http://localhost:8000 de xem web, http://localhost:8000/docs de thu API.

Chi phi moi doan duong (an toan):  cost = thoi_gian * (1 + beta * risk)
  - beta = 0  -> tuyen nhanh nhat
  - beta lon  -> doan rui ro cao bi "dat" len, thuat toan tu di vong
  Dang nhan (thay vi cong) de chi phi khong phu thuoc doan duong bi cat dai hay ngan.
"""
import json
import os
from datetime import datetime

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from psycopg import sql

DB = os.environ["DATABASE_URL"]
RISKY = 0.7  # nguong "doan rui ro cao" (khop tieu chi thanh cong trong proposal)
app = FastAPI(title="Safe-Route HCMC")


def risk_time(cur, t: datetime):
    """Moc rui ro gan nhat <= t (prediction-service tinh theo buoc 30 phut)."""
    cur.execute("SELECT max(thoi_diem) FROM road_segment_risk WHERE thoi_diem <= %s", (t,))
    return cur.fetchone()[0]


def nearest_vertex(cur, lat, lon):
    cur.execute("""SELECT id FROM ways_vertices_pgr
                   ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1""", (lon, lat))
    return cur.fetchone()[0]


def edges_sql(beta: float, t):
    q = """
    SELECT w.gid AS id, w.source, w.target,
           w.cost_s * (1 + {beta} * COALESCE(k.risk, 0)) AS cost,
           CASE WHEN w.reverse_cost_s < 0 THEN -1
                ELSE w.reverse_cost_s * (1 + {beta} * COALESCE(k.risk, 0)) END AS reverse_cost,
           w.x1, w.y1, w.x2, w.y2
    FROM ways w
    LEFT JOIN road_segment_risk k ON k.segment_id = w.gid AND k.thoi_diem = {t}
    """
    return sql.SQL(q).format(beta=sql.Literal(float(beta)), t=sql.Literal(t))


def find_route(cur, src, dst, beta, t):
    cur.execute(sql.SQL("""
        SELECT w.gid, w.length_m, w.cost_s, COALESCE(k.risk, 0) AS risk, ST_AsGeoJSON(w.the_geom)
        FROM pgr_aStar({edges}, %s, %s, directed := true) r
        JOIN ways w ON w.gid = r.edge
        LEFT JOIN road_segment_risk k ON k.segment_id = w.gid AND k.thoi_diem = %s
        ORDER BY r.seq
    """).format(edges=sql.Literal(edges_sql(beta, t).as_string(cur))), (src, dst, t))
    rows = cur.fetchall()
    if not rows:
        return None
    return {
        "time_min": round(sum(r[2] for r in rows) / 60, 1),
        "length_km": round(sum(r[1] for r in rows) / 1000, 2),
        "risky_km": round(sum(r[1] for r in rows if r[3] > RISKY) / 1000, 2),
        "max_risk": round(max(r[3] for r in rows), 2),
        "geojson": {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": json.loads(r[4]), "properties": {"risk": r[3]}}
            for r in rows]},
    }


def explain(fast, safe):
    """TODO (Nguoi B): thay bang Explainability Engine day du (rule + template)."""
    if fast["risky_km"] == 0:
        return "Tuyen nhanh nhat khong di qua doan rui ro cao, co the di binh thuong."
    if safe["risky_km"] >= fast["risky_km"]:
        return "Khong tim duoc duong vong tranh ngap tot hon trong khu vuc nay."
    dt = round(safe["time_min"] - fast["time_min"], 1)
    return (f"Tuyen an toan lau hon {dt} phut nhung tranh duoc "
            f"{round(fast['risky_km'] - safe['risky_km'], 2)} km duong co rui ro ngap cao.")


@app.get("/api/route")
def route(from_lat: float, from_lon: float, to_lat: float, to_lon: float,
          t: datetime = datetime(2022, 10, 24, 22, 0), beta: float = 20):
    with psycopg.connect(DB) as conn, conn.cursor() as cur:
        tr = risk_time(cur, t)
        if tr is None:
            raise HTTPException(404, "Chua co du lieu rui ro truoc thoi diem nay (chay compute_risk.py)")
        src, dst = nearest_vertex(cur, from_lat, from_lon), nearest_vertex(cur, to_lat, to_lon)
        fast = find_route(cur, src, dst, 0, tr)
        safe = find_route(cur, src, dst, beta, tr)
        if not fast or not safe:
            raise HTTPException(404, "Khong tim duoc duong giua 2 diem")
        return {"risk_time": tr, "fastest": fast, "safest": safe, "explanation": explain(fast, safe)}


@app.get("/api/risk")
def risk_map(t: datetime = datetime(2022, 10, 24, 22, 0), min_risk: float = 0.3):
    """Heatmap: cac doan duong co risk >= min_risk tai moc gan nhat <= t."""
    with psycopg.connect(DB) as conn, conn.cursor() as cur:
        tr = risk_time(cur, t)
        cur.execute("""SELECT k.risk, ST_AsGeoJSON(w.the_geom) FROM road_segment_risk k
                       JOIN ways w ON w.gid = k.segment_id
                       WHERE k.thoi_diem = %s AND k.risk >= %s""", (tr, min_risk))
        return {"risk_time": tr, "geojson": {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": json.loads(g), "properties": {"risk": r}}
            for r, g in cur.fetchall()]}}


app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="frontend")
