# Phan cong (3 nguoi, ~4 tuan)

Bo khung da chay duoc tu dau den cuoi (du lieu that + rui ro + API + web).


## Nguoi A - Du lieu & Database
Thu muc: data/, data-ingestion-service/, geospatial-db/
- [ ] Chay thu toan bo buoc 1-2 trong README, sua loi neu co (image, osm2pgrouting, Overpass)
- [ ] Chot bbox khu vuc MVP (hien 10.80-10.88, 106.72-106.80), kiem tra so doan duong
- [ ] Thay elevation_m = 1.5 (placeholder) bang do cao SRTM cho tung doan duong
- [ ] Xem lai config osm2pgrouting: mapconfig_for_cars co bo hem nho khong (xe may di duoc)
- [ ] Viet muc "Tien xu ly du lieu" trong bao cao (dung bang trong data-profile.md)

## Nguoi B - Tinh rui ro & Giai thich
Thu muc: prediction-service/
- [ ] Doc va hieu risk_logic.py, chay test_risk_logic.py
- [ ] Chay compute_risk.py cho cac ngay test (2022-10-24, 2022-04-29, 1 ngay khong mua)
- [ ] Explainability Engine day du (hien chi la 1 ham tam trong routing-service/app.py)
- [ ] Script danh gia: tinh tieu chi thanh cong (giam >= 80% km rui ro cao, them <= 15% thoi gian)
- [ ] Phu trach form khao sat 50-100 nguoi (gui trong tuan 1)

## Nguoi C - Tim duong & Giao dien
Thu muc: routing-service/, frontend/
- [ ] Dung seed_fake_risk.sql de code ngay, khong cho B
- [ ] Kiem tra tuyen nhanh/an toan hop ly tren ban do, chinh beta mac dinh
- [ ] Thanh truot thoi gian: tua qua cac moc 30 phut de demo tuyen thay doi
- [ ] Hoan thien giao dien (chon diem bang o tim kiem, hien thi dep hon)

## Viec chung / chot trong buoi hop
- [ ] Chot khu vuc MVP: Thu Duc (de xuat) hay trung tam
- [ ] Chot dung pgRouting thay OSRM/GraphHopper -> sua 1 dong trong proposal
- [ ] Sua proposal: mucNuoc -> dinh trieu; baoDong = nguong 1.4/1.5/1.6m; cong thuc
      chi phi doi sang cost = time * (1 + beta * risk); decay chi theo tram mua
- [ ] AWS (Lambda/EventBridge): de tuan 3, chi lam neu phan loi da chay

## Lo trinh
| Tuan | Muc tieu |
|---|---|
| 1 | Moi nguoi chay duoc bo khung tren may minh. A: elevation. B: rui ro that 3 ngay test. C: giao dien dung voi rui ro gia. |
| 2 | Ghep rui ro that vao giao dien, Explainability day du, khao sat thu ve. |
| 3 | Chay 3 kich ban, do tieu chi thanh cong, sua loi. Deploy AWS neu con thoi gian. |
| 4 | Bao cao, slide, tap bao ve. |
