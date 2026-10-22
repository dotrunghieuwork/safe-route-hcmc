"""
Logic tinh rui ro ngap (Threshold-based Risk Scoring). Khong phu thuoc database,
nen test duoc rieng bang CSV (xem test_risk_logic.py).
"""
import numpy as np
import pandas as pd

# Nguong mua theo cuong do 1 gio (mm/1h): <20 | 20-50 | >=50
RAIN_BINS = [20, 50]
# Nguong dH = dinh trieu - cao do duong (m): <=0 | 0-0.2 | >0.2
DH_BINS = [0.0, 0.2]

# Bang quyet dinh: hang = muc dH, cot = muc mua
DECISION_TABLE = np.array([
    [0.0, 0.3, 0.6],   # dH <= 0       (duong cao hon nuoc)
    [0.4, 0.6, 0.8],   # 0 < dH <= 0.2 (xam xap)
    [0.8, 0.9, 1.0],   # dH > 0.2      (ngap sau)
])

CONFIDENCE_M = 5000   # qua 5km thi bat dau giam
DECAY_RANGE_M = 5000  # giam tuyen tinh ve 0 khi qua them 5km (tuc 10km)


def rain_level(mm_1h):
    return np.digitize(mm_1h, RAIN_BINS, right=False)


def dh_level(dh_m):
    return np.digitize(dh_m, DH_BINS, right=True)


def decay(d_m):
    """1.0 neu tram trong 5km, giam tuyen tinh ve 0 tai 10km."""
    return np.clip(1 - np.maximum(np.asarray(d_m, dtype=float) - CONFIDENCE_M, 0) / DECAY_RANGE_M, 0, 1)


def flood_risk(mm_1h, dh_m, d_rain_m):
    """Vectorized: moi tham so la array cung do dai (1 phan tu / doan duong)."""
    base = DECISION_TABLE[dh_level(dh_m), rain_level(mm_1h)]
    # Chi giam theo khoang cach tram MUA (mua mang tinh cuc bo).
    # Trieu coi la gia tri vung (lan theo song Sai Gon) -> khong giam theo khoang cach.
    return base * decay(d_rain_m)


def rain_1h_table(rain10: pd.DataFrame, start, end) -> pd.DataFrame:
    """
    rain10: cot tram, ts, mua_10phut_mm (ban goc chi ghi khoang CO mua).
    Tra ve: index = moc 10 phut tu start..end, cot = tram, gia tri = tong mua 60 phut gan nhat.
    """
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    idx = pd.date_range(start - pd.Timedelta("60min"), end, freq="10min")
    wide = (rain10.pivot_table(index="ts", columns="tram", values="mua_10phut_mm", aggfunc="sum")
                  .reindex(idx, fill_value=0.0)      # dien 0 cho khoang khong mua
                  .fillna(0.0))
    return wide.rolling("60min").sum().loc[start:]
