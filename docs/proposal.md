# ĐỀ XUẤT ĐỒ ÁN: SAFE-ROUTE HCMC
### Hệ thống định tuyến giao thông tránh ngập (Flood-Aware Routing System)

---

## 1. Đặt vấn đề & Sự khác biệt (Novelty)

**Vấn đề thực tiễn:** Tại TP.HCM, ngập lụt do mưa và triều cường ảnh hưởng nghiêm trọng đến giao thông. Dù UDI Maps đã cung cấp thông tin cảnh báo "điểm đang ngập", người dùng vẫn thiếu một công cụ chủ động tính toán lộ trình né ngập trước khi khởi hành.

**Sự khác biệt (Novelty):** Dù ý tưởng định tuyến tránh ngập (flood-aware routing) đã xuất hiện trong một số nghiên cứu quốc tế, đồ án này tạo ra giá trị thực tiễn bằng cách địa phương hóa cho TP.HCM — tự động đồng bộ dữ liệu đặc thù của thành phố (mưa, triều cường, cao độ địa hình) để tính toán rủi ro ngập và định tuyến lại.

---

## 2. Luồng nghiệp vụ & Sản phẩm MVP

Sản phẩm là ứng dụng bản đồ (Web/Mobile) loại bỏ hoàn toàn sự phụ thuộc vào người dùng đóng góp dữ liệu (khác với hướng Map4Drop ban đầu).

- **Đầu vào:** Người dùng nhập điểm A và điểm B.
- **Đầu ra:** Bản đồ vùng rủi ro (Heatmap) và 2 lộ trình so sánh:
  - *Tuyến nhanh nhất (Fastest)*: tối ưu thời gian, chấp nhận rủi ro ngập.
  - *Tuyến an toàn (Safest)*: né vùng ngập, chấp nhận đi xa hơn.
- **Explainable UI:** Dưới mỗi lộ trình, hệ thống sinh câu giải thích trực quan, ví dụ: "Tuyến đường này đi xa hơn 2km nhưng tránh được đoạn ngã tư X có xác suất ngập cao do triều cường."

---

## 3. Thiết kế Kiến trúc Hệ thống (System Architecture)

| Service | Chức năng |
|---|---|
| **Data Ingestion Service** | Lambda + EventBridge pull định kỳ từ Cổng dữ liệu mở TP.HCM (mưa, mực nước). Nhóm khảo sát tính khả dụng API thật trong giai đoạn đầu; nếu không sẵn sàng, dùng dữ liệu lịch sử 2022–2023 làm event stream giả lập (xem mục 6). |
| **Geospatial Database** | PostgreSQL + PostGIS. Road Graph (từ OpenStreetMap) và các trạm đo được nạp dưới dạng `geography` (không phải `geometry` thô) để phép ghép dữ liệu bằng toán tử KNN (`<->`) và phép tính khoảng cách kiểm tra ngưỡng tin cậy (`ST_Distance`) đều trả về đơn vị mét chính xác, tránh nhầm lẫn với đơn vị độ (degree) của WGS84. |
| **Prediction Service** | Threshold-based Risk Scoring (không dùng Machine Learning — xem lý do ở mục 4). Input: mức mưa, mức triều (theo `baoDongI/II/III`), độ cao mặt đường. Output: `flood_probability` theo từng đoạn đường. |
| **Routing Service** | Dùng custom profile trên engine mã nguồn mở (OSRM hoặc GraphHopper) thay vì tự viết pathfinding từ đầu. Chạy A* trên Road Graph, nhận `flood_probability` để cập nhật edge weight theo batch (không claim real-time tuyệt đối — xem mục 6). |
| **Explainability Engine** | Rule-based, đối chiếu `time_delta` và `risk_delta` giữa các tuyến để tự động sinh câu giải thích. |

**Ghép dữ liệu trạm đo vào đoạn đường (Spatial Join):**
Hệ thống dùng **K-Nearest Neighbor** qua toán tử `<->` để tìm trạm đo gần nhất cho mỗi đoạn đường (không dùng cách khoanh vùng bán kính cố định, vì cách đó dễ gây xung đột khi 1 đoạn đường rơi vào bán kính của nhiều trạm, và bỏ sót các đoạn đường "mồ côi" không có trạm nào trong bán kính cứng).

**Cơ chế Ngưỡng tin cậy (Confidence Threshold):** Vì KNN vẫn trả về "trạm gần nhất" ngay cả khi trạm đó cách xa hàng chục km, hệ thống tính khoảng cách thực `d` (bằng mét, nhờ kiểu `geography`) tới trạm được chọn. Nếu `d > 5km`, `flood_probability` của đoạn đường đó được nhân với hệ số suy giảm (decay factor) theo khoảng cách vượt ngưỡng, để thuật toán A* không đưa ra quyết định bẻ lái cực đoan dựa trên dữ liệu nội suy kém tin cậy.

---

## 4. Thuật toán Cốt lõi

### 4.1 Định tuyến (A*)

`weight = α × travel_time + β × flood_probability`

- `α, β`: hệ số ưu tiên do người dùng chọn (Fastest: β=0; Safest: β lớn).
- Ví dụ: Tuyến A (5 phút, xác suất ngập 0.8) vs Tuyến B (8 phút, xác suất ngập 0.1). Với α=1, β=20: trọng số A = 21 > trọng số B = 10 → hệ thống chọn Tuyến B.

### 4.2 Tính `flood_probability` — Decision Table (Threshold-based Risk Scoring)

Nhóm chủ động **không dùng Machine Learning**, vì dữ liệu hiện có (`luongMua`, `mucNuoc`...) không có nhãn "đã ngập/chưa ngập" theo từng đoạn đường để làm ground truth huấn luyện. Thay vào đó, dùng hệ thống luật (rule-based expert system) dựa trên ngưỡng có thẩm quyền:

- **Ngưỡng triều:** dựa trực tiếp vào cột `baoDongI/II/III` do cơ quan thủy văn nhà nước cấp sẵn trong dữ liệu — không tự đặt.
- **Ngưỡng mưa:** tham chiếu tiêu chuẩn thiết kế thoát nước hiện hành của TP.HCM (mưa vượt ngưỡng ~50mm/1h hoặc ~70mm/2h được xem là vượt công suất thiết kế, gây ngập cục bộ), đối chiếu với số liệu thực tế do Sở Xây dựng TP.HCM công bố (ngập thường xảy ra khi mưa 20–126,3mm trùng lúc triều đạt 1,74–1,82m).
  - **Lưu ý kỹ thuật quan trọng:** ngưỡng mưa phải tính theo **cường độ tức thời** (rolling sum 1–2 giờ), không dùng thang phân loại mưa 24h (mưa vừa/to/rất to), vì ngập đô thị phản ứng với cường độ mưa trong thời gian ngắn chứ không phải tổng lượng mưa cả ngày. Dữ liệu gốc ghi theo `gio, ngay` nên được tổng hợp lại theo cửa sổ trượt (rolling window) trước khi áp ngưỡng.
- **Độ cao mặt đường (elevation):** xem mục 6 — dữ liệu placeholder.

**Ma trận quyết định (Decision Matrix):** dùng dạng bảng tra 2 chiều thay vì công thức weighted-sum tuyến tính, vì hiệu ứng ngập ở HCMC mang tính **cộng hưởng** (mưa to + triều cao cùng lúc → rủi ro tăng phi tuyến), không phải cộng dồn đều từng yếu tố độc lập:

| ΔH = Mực nước − Cao độ đường | Mưa nhỏ (R < 20mm/1-2h) | Mưa vừa (20 ≤ R < 50mm) | Mưa to (R ≥ 50mm) |
|---|---|---|---|
| ΔH ≤ 0 (đường cao hơn nước) | 0.0 | 0.3 | 0.6 |
| 0 < ΔH ≤ 0.2m (xâm xấp) | 0.4 | 0.6 | 0.8 |
| ΔH > 0.2m (ngập sâu) | 0.8 | 0.9 | 1.0 |

*(Ghi chú: hàng ΔH ≤ 0 vẫn có rủi ro khi mưa to, vì đây mô hình hóa cơ chế ngập do quá tải hệ thống thoát nước cục bộ — độc lập với mực nước triều — cộng hưởng với cơ chế ngập do triều ở hai hàng dưới.)*

Backend chỉ cần `if/else` hoặc bảng tra (lookup table) để map đúng ô — tường minh, vét cạn mọi tổ hợp, trả lời được bất kỳ câu hỏi kiểm tra nào của hội đồng (ví dụ "Báo động II + elevation trung bình + mưa 40mm thì ra bao nhiêu?").

---

## 5. Đánh giá và Khảo sát (Evaluation)

- **Requirement Elicitation:** khảo sát 50–100 người dùng (sinh viên, shipper) để định lượng mức độ ưu tiên "Thời gian" vs "An toàn" khi trời mưa.
- **Scenario-based Testing:** so sánh lộ trình Safe-Route với Google Maps mặc định trong 3 kịch bản:
  1. Thời tiết bình thường (đường đi phải tương đương Google Maps).
  2. Mưa lớn cục bộ.
  3. Mưa lớn kết hợp đỉnh triều cường (hệ thống phải chủ động vẽ đường vòng tránh "rốn ngập").
- **Tiêu chí thành công định lượng:** ở kịch bản 3, hệ thống giảm được ít nhất 80% chiều dài quãng đường đi qua các điểm có `flood_probability > 0.7`, với chi phí thời gian tăng thêm không vượt quá 15% so với tuyến nhanh nhất.
- **Giới hạn phạm vi (Scope):** MVP chỉ xử lý Road Graph và dữ liệu ngập tại một khu vực trọng điểm (ví dụ Quận 10 hoặc quanh Bách Khoa), không phủ toàn thành phố.

---

## 6. Hạn chế & Chiến lược Dữ liệu (chủ động công bố với hội đồng)

Nhóm xác định rõ các điểm nghẽn sau, thay vì để hội đồng phát hiện:

1. **Nội suy theo khoảng cách đường chim bay (Euclidean):** KNN tìm trạm gần nhất dựa trên khoảng cách thẳng, chưa phản ánh địa hình thủy văn thực tế (kênh rạch, hướng dòng chảy). Định hướng mở rộng: tích hợp bản đồ địa hình kênh rạch (topological) để nội suy chính xác hơn.

2. **Dữ liệu cao độ mặt đường (Elevation) là placeholder:** trong khuôn khổ MVP, nhóm dùng dữ liệu từ SRTM/Google Elevation API (độ phân giải ~30m) — quá thô để phản ánh chính xác tiểu địa hình của từng đoạn đường cách nhau vài chục mét. Mục tiêu đồ án CNPM là chứng minh **kiến trúc luồng dữ liệu** hoạt động đúng; trong môi trường production, chỉ cần thay nguồn cấp bằng LiDAR DEM độ phân giải cao (ví dụ từ Sở Tài nguyên và Môi trường) mà không cần viết lại kiến trúc phần mềm.

3. **Real-time vs Mock data:** Kiến trúc (API, Lambda, event-driven) được thiết kế sẵn sàng nhận luồng dữ liệu thời gian thực. Tuy nhiên, do giới hạn quyền truy cập API chính thức của thành phố ở thời điểm làm đồ án, nhóm dùng tập dữ liệu lịch sử (2022–2023) làm event stream giả lập để chứng minh pipeline xử lý và thuật toán A* phản ứng đúng khi có biến động dữ liệu đầu vào — không phải một bản đồ tĩnh.

4. **Granularity của đoạn đường (OSM way):** một đoạn đường OSM có thể dài vài km trong khi độ cao thực tế biến thiên dọc theo đó; MVP chấp nhận gán 1 giá trị ΔH cho cả đoạn, hướng mở rộng là resample đoạn đường thành các segment ngắn hơn (~100–200m) trước khi tính ΔH.

---

## Kết luận

Đồ án chuyển trọng tâm từ "cảnh báo" (như UDI Maps) sang "dự báo và định tuyến chủ động", giữ được tinh thần ban đầu (dùng bản đồ giúp người dùng ra quyết định trong điều kiện đô thị biến động) nhưng loại bỏ hoàn toàn phụ thuộc vào con người (khác Map4Drop) và minh bạch hóa mọi giả định/giới hạn kỹ thuật thay vì che giấu — đây là điểm nhóm chủ động trình bày để không bị động trước hội đồng phản biện.
