# DESIGN — Thiết kế DW, ETL mapping, data dictionary

> **Trạng thái: khung (Phase 0).** Điền dần ở Phase 2–3. Bản sơ bộ nằm ở `SPEC.md` §5–6; khi mục nào ở đây được điền, SPEC chỉ giữ tóm tắt và trỏ về file này.

## 1. Kiến trúc và cách tiếp cận (R22) — Phase 2
- Sơ đồ kiến trúc chi tiết (schema `bronze` / `silver` / `gold` / `dss`): _chưa điền_
- Lý do bottom-up data mart (nằm ở Gold): _chưa điền_

## 2. Bus matrix (R04, R41) — Phase 2

| Business process / Fact | dim_date | dim_month | dim_customer | dim_seller | dim_product | dim_order_status | dim_payment_type |
|---|---|---|---|---|---|---|---|
| fact_order_item | ✔ | | ✔ | ✔ | ✔ | ✔ | |
| fact_order | ✔ (role-playing ×5) | | ✔ | | | ✔ | ✔ |
| fact_seller_monthly | | ✔ | | ✔ | | | |

_(bản nháp từ SPEC, xác nhận ở Phase 2)_

## 3. Khai báo granularity (R23) — Phase 2

| Fact | Granularity | Ước lượng số dòng | Ghi chú |
|---|---|---|---|
| fact_order_item | 1 item của 1 đơn | chờ dữ liệu | |
| fact_order | 1 đơn hàng | chờ dữ liệu | |
| fact_seller_monthly | 1 seller × 1 tháng có hoạt động | chờ dữ liệu | |

## 4. ERD / star schema — Phase 2
_chưa điền (mermaid `erDiagram` hoặc hình trong `docs/report/`)_

## 5. Hierarchy (R24) — Phase 2

| Dimension | Các cấp | Cột |
|---|---|---|
| dim_date | Năm → Quý → Tháng → Ngày | _chưa điền_ |
| dim_customer / dim_seller | Vùng → Bang → Thành phố | Vùng = `region_name` trong `ibge_state_region.csv`, nối `state_code` = `customer_state` / `seller_state`. Bang và thành phố từ Olist |
| dim_product | Nhóm danh mục → Danh mục → Sản phẩm | _chưa điền_ |

## 6. Source-to-target mapping (R05, R29, R30) — Phase 2

| Bảng đích | Cột đích | Bảng nguồn | Cột nguồn | Quy tắc biến đổi |
|---|---|---|---|---|
| `dim_customer`, `dim_seller` | region | `data/external/ibge_state_region.csv` | `region_name` | Nối `state_code` với `customer_state` hoặc `seller_state`. Đọc mọi id dạng chuỗi |
| _còn lại_ | | | | _chưa điền — Phase 2_ |

## 7. Quy tắc làm sạch (R27) — Phase 1–2

Số đo từ `01_profiling.py`, `SOURCE=volume`, 15/10/2026.

| Quy tắc | Số dòng / nhóm bị ảnh hưởng | Ghi chú |
|---|---|---|
| Geolocation: lọc bbox Brazil, trung vị lat/lng, mode city/state theo zip | 1.000.163 dòng; 19.015 zip; 17.972 zip nhiều dòng; tối đa 1.146 dòng/zip; 31 điểm ngoài bbox | 0 lat/lng NULL |
| Chuẩn hóa thành phố (lowercase, bỏ dấu, trim) | `geolocation_city`: 8.010 → 5.968 distinct sau khi bỏ dấu; 73.437 dòng có dấu. Customer/seller city không đổi | |
| dim_customer theo `customer_unique_id` | 99.441 `customer_id`; 96.096 `customer_unique_id` | Map `customer_id` ở Silver |
| Category thiếu → `unknown`; join bản dịch | 610 / 32.951 product thiếu category; 2 category không có dòng dịch | |
| Timestamp NULL hoặc đảo thứ tự: giữ NULL + cờ; loại khỏi measure thời gian | NULL approved 160, carrier 1.783, customer 2.965. Đảo: carrier trước approved 1.359; carrier trước purchase 166; customer trước carrier 23 | G2: 9 đơn `delivered` thiếu một trong hai mốc giao |
| Review: giữ dòng mới nhất theo `review_answer_timestamp` | 789 nhóm `review_id` trùng; 814 dòng thừa; 547 đơn nhiều review | 99.224 dòng thô |
| Payment `not_defined` / 0 → unknown; đối soát price+freight vs payment | 3 `not_defined`; 9 value 0; 2 installments 0; 387 / 98.665 đơn lệch > 0,01 | |
| Đọc id và zip dạng chuỗi | 0 zip ngắn hơn 5 ký tự | min_length = 5 trên customer, seller, geolocation |
| Giữ cửa sổ mua hàng 2016-09-04 → 2018-10-17 | Tháng thưa: 2016-09=4, 2016-10=324, 2016-12=1, 2017-01=800, 2018-09=16, 2018-10=4; không có 2016-11. 19 tháng ≥ 1.000 đơn (2017-02 → 2018-08) | Không cắt khỏi kho |
| Loại đơn nhiều seller khỏi measure trải nghiệm xấu | 1.278 / 98.666 đơn | G3 pass |

## 8. Data dictionary (R29) — Phase 2–3

| Bảng | Cột | Kiểu | Khóa | Mô tả | Nguồn |
|---|---|---|---|---|---|
| `ibge_state_region` | `state_id` | string | | Mã IBGE của UF | API localidades/estados, 15/10/2026 |
| `ibge_state_region` | `state_code` | string | duy nhất (27 giá trị) | Sigla UF, khóa nối với Olist | cùng nguồn |
| `ibge_state_region` | `state_name` | string | | Tên bang | cùng nguồn |
| `ibge_state_region` | `region_id` | string | | Mã vùng IBGE 1–5 | cùng nguồn |
| `ibge_state_region` | `region_code` | string | | N, NE, SE, S, CO | cùng nguồn |
| `ibge_state_region` | `region_name` | string | | Norte, Nordeste, Sudeste, Sul, Centro-Oeste | cùng nguồn |
| _còn lại_ | | | | | _chưa điền — Phase 2_ |

## 9. ETL: thứ tự nạp, incremental, audit (R07, R28, R40) — Phase 3
_chưa điền. Bảng audit dùng tên `gold.etl_audit` (chưa thiết kế cột)._

## 10. Thiết kế dữ liệu cho DSS (R31) — Phase 5
_Feature view (ví dụ `dss.v_seller_features`) chỉ dựa trên `gold.*`. Bảng kết quả `dss.seller_risk_score`, `dss.policy_scenario`, `dss.decision_log` — chưa điền._
