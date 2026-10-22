"""
Lam sach du lieu Mua.xls va MucNuoc.xls -> data/clean/*.csv

Cach chay (tu thu muc goc repo):
    pip install pandas xlrd
    python data-ingestion-service/clean_data.py data/raw/Mua.xls data/raw/MucNuoc.xls

Output 
    data/clean/stations.csv
    data/clean/rain_daily_1995_2021.csv
    data/clean/rain_10min_2022_2023.csv
    data/clean/tide_daily_1995_2022.csv
"""
import sys
import unicodedata
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "clean"


def bo_dau(s: str) -> str:
    """'Thủ Đức' -> 'Thu Duc'"""
    s = str(s).replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def main(mua_path: str, mucnuoc_path: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    m = pd.read_excel(mua_path, engine="xlrd")
    n = pd.read_excel(mucnuoc_path, engine="xlrd")
    m["tram"] = m["tenTram"].map(bo_dau)
    n["tram"] = n["tenTram"].map(bo_dau)

    # 1. Danh sach tram (toa do WGS84). toaDoX/toaDoY trong file goc toan bang 0 -> bo.
    st = pd.concat([
        m.groupby("tram")[["kinhDo", "viDo"]].first().assign(loai="mua"),
        n.groupby("tram")[["kinhDo", "viDo"]].first().assign(loai="trieu"),
    ]).reset_index()
    st.to_csv(OUT / "stations.csv", index=False, encoding="utf-8-sig")

    # 2. Tach mua theo ngay (cot gio rong) va mua 10 phut (cot gio co gia tri)
    co_gio = m["gio"].astype(str).str.strip() != ""

    daily = m.loc[~co_gio, ["tram", "ngay", "luongMua"]]
    daily = daily.rename(columns={"luongMua": "mua_ngay_mm"})
    daily.to_csv(OUT / "rain_daily_1995_2021.csv", index=False, encoding="utf-8-sig")

    g = m.loc[co_gio].copy()
    g["ts"] = pd.to_datetime(
        g["ngay"].dt.strftime("%Y-%m-%d") + " " + g["gio"].astype(str).str.strip()
    )
    g = g[["tram", "ts", "luongMua"]].rename(columns={"luongMua": "mua_10phut_mm"})

    g.sort_values(["tram", "ts"]).to_csv(
        OUT / "rain_10min_2022_2023.csv", index=False, encoding="utf-8-sig"
    )

    # 3. Trieu: cot mucNuoc toan bang 0 -> bo, dung doCaoDinhT (dinh trieu trong ngay).
    t = n[["tram", "ngay", "doCaoDinhT", "doCaoChanT",
           "baoDongI", "baoDongII", "baoDongIII"]].copy()
    t = t.rename(columns={"doCaoDinhT": "dinh_trieu_m", "doCaoChanT": "chan_trieu_m"})
    # Muc bao dong 0-3 (co 0/1 trong file goc loai tru nhau: chi bat muc cao nhat)
    t["muc_bao_dong"] = t["baoDongIII"] * 3 + t["baoDongII"] * 2 + t["baoDongI"] * 1
    t = t.drop(columns=["baoDongI", "baoDongII", "baoDongIII"])
    # Danh dau dong bat thuong thay vi xoa, de nguoi dung tu quyet dinh
    t["nghi_van"] = (
        (t["dinh_trieu_m"] == 0)
        | (t["chan_trieu_m"] < -5)
        | (t["chan_trieu_m"] > t["dinh_trieu_m"])
    )
    t.to_csv(OUT / "tide_daily_1995_2022.csv", index=False, encoding="utf-8-sig")

    print("Xong:", sorted(p.name for p in OUT.glob("*.csv")))
    print("So dong nghi van (trieu):", int(t["nghi_van"].sum()))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Cach dung: python clean_data.py <Mua.xls> <MucNuoc.xls>")
    main(sys.argv[1], sys.argv[2])
