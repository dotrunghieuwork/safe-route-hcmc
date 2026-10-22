"""
Tinh rui ro cho MOI doan duong tai cac moc thoi gian trong 1 ngay, ghi vao road_segment_risk.
Chay: docker compose run --rm api python /app/prediction/compute_risk.py --date 2022-10-24
"""
import argparse
import io
import os

import numpy as np
import pandas as pd
import psycopg

from risk_logic import flood_risk, rain_1h_table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)                  # vd 2022-10-24
    ap.add_argument("--step", type=int, default=30)           # phut giua 2 moc
    args = ap.parse_args()
    day = pd.Timestamp(args.date)

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        seg = pd.read_sql("SELECT * FROM segment_station", conn)
        rain10 = pd.read_sql(
            "SELECT tram, ts, mua_10phut_mm FROM rain_10min WHERE ts >= %s AND ts < %s",
            conn, params=(day - pd.Timedelta("1h"), day + pd.Timedelta("1D")))
        tide = pd.read_sql(
            "SELECT tram, dinh_trieu_m FROM tide_daily WHERE ngay = %s AND NOT nghi_van",
            conn, params=(day.date(),))

        dinh = seg.tram_trieu.map(tide.set_index("tram").dinh_trieu_m)
        dh = (dinh - seg.elevation_m).fillna(-99).values   # thieu so lieu trieu -> coi nhu khong ngap do trieu

        r1h = rain_1h_table(rain10, day, day + pd.Timedelta("23h50min"))
        moc = pd.date_range(day, day + pd.Timedelta("23h50min"), freq=f"{args.step}min")

        buf = io.StringIO()
        for t in moc:
            mm = seg.tram_mua.map(r1h.loc[t]).fillna(0).values if t in r1h.index else np.zeros(len(seg))
            risk = flood_risk(mm, dh, seg.d_mua_m.values)
            pd.DataFrame({"segment_id": seg.segment_id, "thoi_diem": t, "risk": risk.round(3)}) \
              .to_csv(buf, index=False, header=False)
        buf.seek(0)

        with conn.cursor() as cur:
            cur.execute("DELETE FROM road_segment_risk WHERE thoi_diem >= %s AND thoi_diem < %s",
                        (day, day + pd.Timedelta("1D")))
            with cur.copy("COPY road_segment_risk (segment_id, thoi_diem, risk) FROM STDIN WITH (FORMAT csv)") as cp:
                cp.write(buf.read())
        conn.commit()
    print(f"Da ghi {len(moc)} moc x {len(seg)} doan duong cho ngay {args.date}")


if __name__ == "__main__":
    main()
