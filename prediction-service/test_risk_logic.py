"""
Chay: python prediction-service/test_risk_logic.py
Kiem tra logic tren data that, khong can database: tram Thu Duc, ngay 24/10/2022 (kich ban 3).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from risk_logic import flood_risk, rain_1h_table, decay

ROOT = Path(__file__).resolve().parent.parent / "data" / "clean"

# Bang quyet dinh: vai o kiem tra
assert flood_risk([10], [-0.5], [0])[0] == 0.0
assert flood_risk([20], [0.1], [0])[0] == 0.6
assert flood_risk([60], [0.5], [0])[0] == 1.0
assert decay([3000])[0] == 1.0 and decay([7500])[0] == 0.5 and decay([12000])[0] == 0.0

rain10 = pd.read_csv(ROOT / "rain_10min_2022_2023.csv", parse_dates=["ts"])
tide = pd.read_csv(ROOT / "tide_daily_1995_2022.csv", parse_dates=["ngay"])

day = "2022-10-24"
r1h = rain_1h_table(rain10, f"{day} 00:00", f"{day} 23:50")
dinh = tide[(tide.tram == "Phu An") & (tide.ngay == day)].dinh_trieu_m.iloc[0]
elev = 1.5  # placeholder
print(f"Ngay {day} | dinh trieu Phu An = {dinh}m | cao do placeholder = {elev}m | dH = {dinh-elev:.2f}m")
print("Mua 1h lon nhat tram Thu Duc:", r1h["Thu Duc"].max(), "mm")

s = r1h["Thu Duc"]
out = pd.DataFrame({"mua_1h_mm": s.round(1),
                    "risk": flood_risk(s.values, np.full(len(s), dinh - elev), np.zeros(len(s)))})
print(out[out.mua_1h_mm > 0].iloc[::3].to_string())
print("OK")
