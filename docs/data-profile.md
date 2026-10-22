# Data Profile - Mua.xls & MucNuoc.xls

## Quy trinh du lieu

    data/raw/*.xls  --(clean_data.py)-->  data/clean/*.csv  --(import)-->  PostGIS

- `data/raw/`: file goc, KHONG sua tay.
- `data-ingestion-service/clean_data.py`: script lam sach, chay lai bat cu luc nao.
- `data/clean/`: output dung de code. Khong dau, UTF-8 co BOM (Excel mo khong loi font).

| File | Noi dung |
|---|---|
| stations.csv | 14 tram mua + 2 tram trieu, toa do WGS84 (kinhDo, viDo) |
| rain_daily_1995_2021.csv | Mua theo NGAY, 14 tram |
| rain_10min_2022_2023.csv | Mua theo 10 PHUT, 8 tram (chi ghi khoang co mua) |
| tide_daily_1995_2022.csv | Dinh/chan trieu theo ngay, 2 tram, muc_bao_dong 0-3, cot nghi_van |

## Van de cua file goc va cach xu ly

| Van de | Xu ly |
|---|---|
| Cot mucNuoc toan bang 0 | Bo, dung doCaoDinhT (dinh trieu trong ngay) -> dinh_trieu_m |
| toaDoX, toaDoY toan bang 0 | Bo, dung kinhDo/viDo |
| baoDongI/II/III la co 0/1, loai tru nhau | Gop thanh 1 cot muc_bao_dong (0-3). Nguong suy ra: BDI >= 1.4m, BDII >= 1.5m, BDIII >= 1.6m |
| 1 file mua tron 2 loai: theo ngay (gio rong) va theo 10 phut (2022-2023) | Tach thanh 2 file rieng |
| ngay va gio nam 2 cot rieng, gio dang chuoi | Gop thanh 1 cot timestamp ts |
| Ban 10 phut chi ghi khoang co mua | Khoang trong = 0mm, dien 0 khi tinh rolling window (prediction-service) |
| 38 dong trieu bat thuong (dinh = 0, chan < -5m, chan > dinh) | Danh dau nghi_van = True, khong xoa |
| Ten tram co dau | Bo dau (Thu Duc, Cat Lai, Phu An...) |

## Phat hien anh huong proposal

1. Trieu chi co 1 gia tri/ngay, chi 2 tram (Phu An, Nha Be), het nam 2022.
2. Mua 10 phut chi co 2022-2023, chi 8 tram ngoai thanh/Thu Duc.
3. 2 tram mua gan Bach Khoa (Tan Son Hoa 2.8km, Mac Dinh Chi 4.8km) chi co so lieu ngay, het nam 2021.
4. Giai doan trung giua mua 10 phut va trieu: chi nam 2022.

## De xuat khu vuc MVP

- Chinh: TP. Thu Duc (tram Thu Duc, Cat Lai + trieu Phu An). Giu duoc rolling window 1h.
- Du phong: Trung tam (Mac Dinh Chi, Tan Son Hoa + Phu An). Chi co mua theo ngay -> doi nguong mua sang thang 24h.

## Ngay ung vien cho kich ban test

Kich ban 3 (mua to + trieu cao), khu Thu Duc, mua lon nhat trong 1h:

| Ngay | Mua 1h Thu Duc | Mua 1h Cat Lai | Dinh trieu Phu An | Muc |
|---|---|---|---|---|
| 2022-10-24 | 65.4mm | 7.0mm | 1.54m | BDII |
| 2022-08-15 | 54.8mm | 11.8mm | 1.46m | BDI |
| 2022-10-01 | 28.4mm | 53.4mm | 1.43m | BDI |
| 2022-08-14 | - | 51.4mm | 1.43m | BDI |

Kich ban 2 (mua to, trieu thap): 2022-04-29 (Thu Duc 76.8mm/1h, trieu 1.25m).

Khu trung tam (mua ngay >= 50mm + trieu >= BDII): 2018-11-26 (Mac Dinh Chi 147.4mm, 1.55m), 2021-10-23 (59.9 / 64.2mm, 1.55m).
