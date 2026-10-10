# Đánh giá khả thi dữ liệu và chọn đề tài

| Mục | Giá trị |
|---|---|
| Ngày | 10/10/2026 (tuần 7); cập nhật 10/10/2026 sau khi tải dữ liệu |
| Trạng thái | **Đã chốt có điều kiện (10/10/2026).** Dữ liệu Olist và Marketing Funnel đã tải; số liệu nhẹ từ `00_verify_and_sample.py`. Profiling sâu và cổng G1–G6 thuộc Phase 1. |
| Kết luận | **T1 – nhóm đã xác nhận; chốt cuối sau G1–G6** |

Ký hiệu: **[ĐỀ]** có trong file đề · **[SUY LUẬN]** do nhóm suy ra · **[GIẢ ĐỊNH]** chưa kiểm chứng, kiểm tra ở Phase 1.

---

## 1. Data Feasibility Review

### 1.1 Bảng có thể làm fact và granularity tự nhiên

| Bảng nguồn | Có thể làm fact? | Granularity tự nhiên | Ghi chú |
|---|---|---|---|
| `order_items` | ✔ fact giao dịch chính | 1 item của 1 đơn (`order_id` + `order_item_id`) | Mức chi tiết nhất có cả product và seller → hỗ trợ drill-down tối đa |
| `orders` | ✔ fact mức đơn / accumulating snapshot | 1 đơn hàng | Chứa chuỗi mốc thời gian của vòng đời đơn → hợp với *accumulating snapshot* (Kimball) |
| `order_reviews` | Gộp vào fact mức đơn | 1 review (thường 1 review/đơn) | [GIẢ ĐỊNH] có đơn nhiều review và review_id trùng → cần quy tắc chọn review mới nhất |
| `order_payments` | Gộp vào fact mức đơn hoặc fact riêng | 1 dòng thanh toán (đơn × phương thức × thứ tự) | Tổng payment/đơn dùng để đối soát với tổng `price + freight` |
| — (phái sinh) | ✔ periodic snapshot | 1 seller × 1 tháng | Tính từ 2 fact trên trong ETL; là đầu vào chính cho mô hình DSS |
| `customers`, `sellers`, `products`, `geolocation`, `translation` | ✖ — làm dimension | — | — |

### 1.2 Measure khả thi

| Measure | Cách tính | Loại |
|---|---|---|
| Giá trị hàng (GMV) | `price` | Cộng dồn |
| Phí vận chuyển | `freight_value` | Cộng dồn |
| Số item / số đơn | đếm | Cộng dồn |
| Thời gian giao hàng (ngày) | `delivered_customer − purchase` | Không cộng dồn (lấy trung bình/percentile) |
| Độ trễ so với hẹn (ngày) | `delivered_customer − estimated_delivery` | Không cộng dồn |
| Seller giao vận chuyển trễ hạn | `delivered_carrier > shipping_limit_date` (cờ 0/1) | Cộng dồn → tỷ lệ |
| Thời gian xử lý của seller (ngày) | `delivered_carrier − approved` | Trung bình |
| Điểm review / review tiêu cực | `review_score`, cờ `score ≤ 2` | Trung bình / tỷ lệ |
| Khoảng cách seller → khách (km) | Haversine từ lat/lng trung bình theo zip prefix | Trung bình (derived) |
| Tỷ lệ hủy / không giao | `order_status` ∈ {canceled, unavailable} | Tỷ lệ |

### 1.3 Hierarchy khả thi (drill-down / roll-up)

| Dimension | Hierarchy | Nguồn |
|---|---|---|
| Thời gian | Năm → Quý → Tháng → Ngày (+ thứ trong tuần, ngày lễ) | Timestamp của `orders`; ngày lễ từ nguồn bổ sung |
| Địa lý khách hàng | Vùng → Bang → Thành phố (→ zip prefix) | `customers` + bảng bang→vùng (IBGE) |
| Địa lý người bán | Vùng → Bang → Thành phố | `sellers` + bảng bang→vùng |
| Sản phẩm | Nhóm danh mục → Danh mục → Sản phẩm | `products` + `translation` + nhóm danh mục do nhóm tự định nghĩa |
| Người bán | Phân khúc kinh doanh → Seller | `closed_deals.business_segment` (chỉ một phần seller, [GIẢ ĐỊNH] độ phủ thấp) |

### 1.4 KPI tính được

Tỷ lệ giao trễ so với hẹn; tỷ lệ seller bàn giao trễ hạn; thời gian giao trung bình/P90; điểm review trung bình; tỷ lệ review tiêu cực (≤ 2); tỷ lệ hủy; GMV và số đơn theo seller/danh mục/vùng/tháng; tỷ trọng phí vận chuyển trên giá trị đơn; tỷ lệ khách mua lại (theo `customer_unique_id`).

### 1.5 Đủ biến để xây mô hình DSS?

| Loại biến | Có trong dữ liệu? | Ví dụ |
|---|---|---|
| Decision variable | ✔ (là **chính sách** do người quản lý đặt, không cần có sẵn trong dữ liệu) | Ngưỡng phân hạng seller; ngưỡng điểm rủi ro; buffer ngày giao hẹn; mức trợ giá phí ship |
| Uncontrollable variable | ✔ | Nhu cầu theo mùa (Black Friday), khoảng cách địa lý, cơ cấu danh mục, hiệu suất đơn vị vận chuyển, kỳ vọng khách |
| Result variable | ✔ | Tỷ lệ review tiêu cực, tỷ lệ giao trễ, GMV bị ảnh hưởng |
| Dữ liệu để ước lượng quan hệ | ✔ một phần | Quan hệ lịch sử giữa trễ hạn ↔ review tiêu cực ước lượng được; **hiệu quả của biện pháp can thiệp** thì **không có** trong dữ liệu → phải là tham số kịch bản |

### 1.6 Giới hạn dữ liệu có thể ảnh hưởng DSS

1. **Không có chi phí/lợi nhuận thật** (không có giá vốn, hoa hồng, chi phí vận chuyển thật — chỉ có phí ship khách trả) → không tối ưu theo lợi nhuận; dùng GMV và tỷ lệ trải nghiệm xấu.
2. **Không có lịch sử can thiệp** (cảnh báo, đình chỉ seller…) → tác động của chính sách là **giả định kịch bản**, phải làm sensitivity.
3. **Không có mã đơn vị vận chuyển** → không tách được lỗi theo hãng vận chuyển; chỉ tách được phần trễ do seller (trước `shipping_limit_date`) và phần sau bàn giao.
4. **Khoảng thời gian ngắn** — đã đo trên dữ liệu thật (script 10/10/2026): `order_purchase_timestamp` min=2016-09-04 21:15:19, max=2018-10-17 17:30:18 (99,441/99,441 non-null); 99,441 đơn. [GIẢ ĐỊNH còn lại, Phase 1] 2016 rất thưa, cuối 2018 bị cắt → dự báo dài hạn yếu; mô hình nên ở mức tháng, train/test theo thời gian.
5. **Review ở mức đơn**, nhưng đơn có thể nhiều seller → khó quy trách nhiệm; [GIẢ ĐỊNH] tỷ lệ đơn nhiều seller nhỏ.
6. **Nhiều seller ít đơn** → chỉ số theo tháng nhiễu; cần ngưỡng số đơn tối thiểu hoặc làm mượt.
7. **Không có dữ liệu chuyển đổi/lượt xem** → không mô hình hóa được tác động của ngày hẹn giao lên doanh số.
8. **Tỷ lệ mua lại thấp** ([GIẢ ĐỊNH], phần lớn `customer_unique_id` chỉ mua 1 lần) → hướng retention thiếu tín hiệu.

### 1.7 Cổng kiểm tra trên dữ liệu thật (chạy đầu Phase 1, trước khi chốt)

| Mã | Kiểm tra | Ngưỡng đề xuất (nhóm chốt) | Nếu không đạt |
|---|---|---|---|
| G1 | Số seller có ≥ 10 item/tháng trong ≥ 6 tháng | ≥ 150 seller | Hạ ngưỡng sang quý, hoặc chuyển sang T2 |
| G2 | % đơn đã giao có đủ `delivered_carrier_date` và `delivered_customer_date` | ≥ 95% | Loại đơn thiếu mốc, ghi vào hạn chế |
| G3 | % đơn có > 1 seller | ≤ 5% | Quy tắc quy trách nhiệm (chia đều / loại) |
| G4 | Tỷ lệ review ≤ 2 trên tổng review | 5–25% (đủ để mô hình học) | Đổi biến mục tiêu sang "trễ hạn" |
| G5 | Số tháng có ≥ 1.000 đơn | ≥ 15 tháng | Giới hạn phạm vi thời gian |
| G6 | % seller trong `orders` khớp được với `closed_deals` | Chỉ ghi nhận | < 10% → dùng funnel như thuộc tính phụ, không làm hierarchy chính |

---

## 2. So sánh đề tài ứng viên

### T1 — Quản lý hiệu suất người bán (Seller Performance Management)
1. **Decision maker:** Trưởng bộ phận Quản lý chất lượng người bán (Seller Quality / Marketplace Operations Manager) của Olist.
2. **Quyết định:** Mỗi tháng, áp dụng **chính sách phân hạng** nào để xếp seller vào các mức can thiệp (bình thường / theo dõi / cảnh báo + hỗ trợ / tạm ngưng hiển thị) — tức chọn bộ ngưỡng của chính sách.
3. **Alternatives:** P0 giữ nguyên (không can thiệp); P1 chính sách dựa trên ngưỡng KPI cố định (ví dụ tỷ lệ bàn giao trễ, điểm review); P2 chính sách dựa trên **điểm rủi ro dự báo** của mô hình; các biến thể của P1/P2 theo mức ngưỡng.
4. **Principle of choice:** Chọn chính sách **giảm nhiều nhất số đơn trải nghiệm xấu dự kiến** (review ≤ 2 hoặc giao trễ) ở tháng tới, với ràng buộc **GMV bị ảnh hưởng ≤ X%** và **số seller cần xử lý ≤ N/tháng** (X, N do decision maker đặt — tham số trong DSS).

### T2 — Hẹn ngày giao và hiệu suất giao hàng (Delivery Promise & Logistics)
1. **Decision maker:** Trưởng bộ phận Logistics/Vận hành.
2. **Quyết định:** Đặt **số ngày hẹn giao** (buffer) cho từng tuyến bang seller → bang khách.
3. **Alternatives:** Giữ cách tính hiện tại; hẹn theo percentile P80/P90/P95 thời gian giao lịch sử; buffer cố định +k ngày theo vùng.
4. **Principle of choice:** Đạt tỷ lệ giao đúng hẹn ≥ mục tiêu với **số ngày hẹn nhỏ nhất**. *Lưu ý:* lợi ích của hẹn ngắn hơn (tăng chuyển đổi) **không đo được** trong dữ liệu → vế "nhỏ nhất" chỉ là tiêu chí phụ.

### T3 — Giữ chân / hài lòng khách hàng (Customer Retention & Satisfaction)
1. **Decision maker:** Trưởng bộ phận CRM/Marketing.
2. **Quyết định:** Nhắm nhóm khách nào để chạy chương trình giữ chân (voucher, ưu đãi phí ship).
3. **Alternatives:** Không làm; nhắm theo RFM; nhắm theo xác suất mua lại dự báo.
4. **Principle of choice:** Tối đa số khách mua lại trên ngân sách. **Trả lời được về hình thức, nhưng không đủ cơ sở dữ liệu**: [GIẢ ĐỊNH] tỷ lệ mua lại rất thấp, không có chi phí chiến dịch hay phản hồi chiến dịch → không có quan hệ nhân quả nào để mô hình hóa.

### Bảng so sánh

| Đề tài | Decision maker & quyết định | Mức phù hợp DW | Mức phù hợp OLAP | Mức phù hợp DSS (model + what-if) | Dữ liệu có hỗ trợ không | Độ phức tạp / rủi ro tiến độ | Khuyến nghị |
|---|---|---|---|---|---|---|---|
| **T1 Seller Performance** | Seller Quality Manager; chọn chính sách phân hạng/can thiệp seller hằng tháng | **Cao** — dùng gần hết bảng nguồn + funnel; fact constellation (item, đơn, snapshot seller-tháng) | **Cao** — seller × thời gian × địa lý × danh mục, hierarchy rõ | **Cao** — mô hình rủi ro (xác suất) + what-if ngưỡng + goal seeking ngưỡng theo ràng buộc GMV | Có; thiếu dữ liệu hiệu quả can thiệp → tham số kịch bản | Trung bình; rủi ro: seller thưa (G1), quy trách nhiệm đơn nhiều seller (G3) | **Chọn** |
| T2 Delivery Promise | Logistics Manager; đặt số ngày hẹn giao theo tuyến | Cao — dùng orders, items, geolocation, customers, sellers | Cao — tuyến địa lý × thời gian | Trung bình–Cao — mô hình phân phối thời gian giao (risk) + what-if buffer | Có; không đo được lợi ích của hẹn ngắn; không có hãng vận chuyển | Thấp–Trung bình | Phương án dự phòng |
| T3 Retention | CRM Manager; chọn tập khách nhắm mục tiêu | Trung bình — chủ yếu customers + orders | Trung bình | **Thấp** — thiếu biến mục tiêu đủ mạnh, thiếu chi phí/phản hồi chiến dịch | Yếu | Cao (mô hình dễ vô nghĩa) | Không chọn |

---

## 3. Kết luận — đề tài đã chốt có điều kiện (10/10/2026)

**Tên đề tài:** *Kho dữ liệu và Hệ hỗ trợ quyết định quản lý hiệu suất người bán trên sàn thương mại điện tử Olist* (Olist Seller Performance DW & DSS).

**Lý do chọn T1 thay vì T2/T3**
- **Quyết định rõ và lặp lại** (hằng tháng), có người chịu trách nhiệm, có alternatives và principle of choice đo được — tránh lỗi "câu hỏi quyết định mơ hồ".
- **Tích hợp dữ liệu thật nhất:** cần nối orders + items + reviews + payments + sellers + products + geolocation + translation + Marketing Funnel → thể hiện rõ vai trò ETL/integration của DW.
- **DSS có model thực chất:** điểm rủi ro seller (mô hình xác suất, học từ snapshot trong DW) + mô phỏng chính sách what-if + goal seeking ngưỡng; không chỉ là dashboard mô tả.
- **Bao trùm T2:** chỉ số giao hàng vẫn nằm trong T1 (seller bàn giao trễ, giao trễ), nên OLAP về logistics vẫn có. Nếu G1/G3 không đạt, chuyển sang T2 **dùng lại cùng DW** (chi phí đổi hướng thấp).
- T2 bị hạn chế vì lợi ích của hẹn giao ngắn không đo được; T3 thiếu tín hiệu mua lại.

**Thỏa điều kiện mục 3.1 của đề [ĐỀ]**

| Điều kiện | Cách đáp ứng |
|---|---|
| (a) DW là cốt lõi, phục vụ phân tích và ra quyết định | DW dạng fact constellation là nguồn duy nhất cho dashboard OLAP và cho DSS (mô hình đọc snapshot seller-tháng từ DW) |
| (b) Nguồn hợp lệ, quy mô đủ lớn | Kaggle, license CC BY-NC-SA 4.0; **99,441 đơn**, 9 bảng Olist + Marketing Funnel (842 closed deals, 8,000 MQL) — số từ script 10/10/2026. Đề không định lượng "đủ lớn" — nhóm nêu quy mô thực tế |
| (c) Ý nghĩa thực tế, bài toán quyết định cụ thể | Quyết định phân hạng/can thiệp seller hằng tháng của một marketplace thật, gắn KPI trải nghiệm khách và GMV |

**Việc cần làm trước khi chốt cuối:** chạy G1–G6 trên dữ liệu thật (đầu Phase 1); nhóm chốt X (% GMV) và N (số seller/tháng) mặc định cho DSS.
