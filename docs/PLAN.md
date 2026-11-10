# PLAN — Kế hoạch hiện thực

| Mục | Giá trị |
|---|---|
| Phiên bản | v0.6 — 05/11/2026 |
| Hạn nộp | **23:59 Chủ nhật 15/11/2026** (ZIP qua LMS) — mốc nội bộ: **đóng băng 14/11** |
| Thứ tự hiện thực | **Cloud trước, local sau.** DW, ETL, OLAP SQL và DSS chạy trên Databricks Free Edition trước. Đường local (pyspark + delta-spark trên `data/sample/`, R46) chỉ làm khi phần Cloud tương ứng đã chạy được — để người chấm chạy lại, không phải nơi dựng hệ thống trước. |

Vai trò gợi ý (chờ nhóm gán tên): **A** = DW + ETL · **B** = OLAP + frontend · **C** = DSS + báo cáo. Nhóm 2 người: A gộp ETL, B gộp frontend + DSS UI, cùng làm báo cáo.

Mỗi task ghi mã yêu cầu trong SPEC §2 (R-xx).

**Nhãn nơi làm**

| Nhãn | Nghĩa |
|---|---|
| **Cloud** | Workspace Databricks: notebook, Unity Catalog, Volume, Jobs, SQL Warehouse |
| **Local → Cloud** | Chạy trên laptop nhưng đọc/ghi Databricks (SQL warehouse, token). Không dựng DW trên máy |
| **Local** | Chỉ trên laptop: repo, tài liệu, pytest, Power BI Desktop, Streamlit, pyspark + delta-spark trên `data/sample/` |

Trong mỗi phase, làm hết mục **Cloud** trước, rồi **Local → Cloud**, rồi **Local**. Ngoại lệ: Phase 3 (ETL warehouse) chỉ Cloud. Đường local của R46 nằm ở S6, Phase 6 và Phase 7.

---

## Phase 0 — Chốt phạm vi, dựng repo, tải dữ liệu, chốt công nghệ · 10/10 → 13/10

**Mục tiêu:** nền tảng sẵn sàng, dữ liệu thật trong `data/raw/`, đề tài đã ghi, kiến trúc medallion đã ghi trong SPEC.

**Đã xong**

- [x] Đọc đề + file phân tích, rút ràng buộc (R01, R14, R20) — Local
- [x] Dựng cấu trúc repo, `.gitignore`, `.env.example`, `git init` (R16) — Local
- [x] Đánh giá đề tài sơ bộ, SPEC, PLAN, PROGRESS_LOG, README (R01, R22) — Local
- [x] **Tải dữ liệu Olist** vào `data/raw/` (nhóm tải tay), chạy `00_verify_and_sample.py`, điền `data/README.md` (R03, R17). Marketing Funnel đã có trong `data/external/` — Local
- [x] Tạo repo GitHub (private khi làm, mở quyền khi nộp), push (R16) — Local
- [x] Nhóm xác nhận đề tài T1 (có điều kiện G1–G6) và stack PostgreSQL; ghi vào README/SPEC (R01) — stack này **thay thế ngày 10/10/2026** — Local
- [x] Ghi quyết định thay kiến trúc sang Databricks medallion vào SPEC §10 và PROGRESS_LOG (R22) — 10/10/2026 — Local
- [x] Phân vai thành viên — điền họ tên / MSSV / vai trò vào bảng README (R14) — Local
- [x] Tạo tài khoản Databricks Free Edition (R06) và venv Python local có pyspark, delta-spark (R46). Kiểm tra chạy thật nằm ở S1 (Cloud) và S6 (Local, làm sau S1)

**Spike — Cloud làm trước.** Mỗi spike ghi đạt/không đạt và hệ quả vào PROGRESS_LOG và SPEC §10. **Nếu một spike không đạt, liệt kê 2 phương án và chờ nhóm — không tự chọn.**

**Cloud**

- [x] **S1** Tạo workspace Free Edition, catalog/schema (`bronze`, `silver`, `gold`, `dss`), upload 9 CSV + Funnel vào một Volume, thử đọc bằng `spark.read` (R06, R45). Catalog `olist_catalog`. Volume `/Volumes/olist_catalog/bronze/raw/` (`olist/` 9 CSV, `funnel/` 2 CSV). `olist_orders_dataset.csv`: 99,441 dòng, mọi cột `string` — 13/10/2026
- [x] **S4** Kiểm tra Databricks Jobs / lịch chạy (R40). Đạt 13/10/2026: job `s4_smoke`, compute Serverless, Run now thành công; lịch lưu được và đang Paused
- [x] **S5** Gắn Git folder với repo GitHub (R16). Đạt 13/10/2026: folder `olist-dw-dss`, nhánh `main`, thấy `README.md`, `docs/`, `src/`, `data/`

**Local → Cloud** (sau S1)

- [ ] **S2** Truy vấn SQL warehouse từ Python local (`databricks-sql-connector` + token) (R31, R32). Khả năng kết nối là **[GIẢ ĐỊNH]**
- [ ] **S3** Thử kết nối Power BI Desktop tới SQL warehouse. Chỉ kiểm tra kết nối, chưa làm dashboard (R09)

**Local** (sau khi S1 đạt; không chặn ETL trên Cloud)

- [ ] **S6** Chạy pyspark + delta-spark local trên `data/sample/` (R46). Chỉ xác nhận đường tái lập, không dùng kết quả này để thay workspace

**Sản phẩm:** repo, `data/raw/`, `data/sample/`, `data/README.md`, SPEC/PLAN. Kết quả spike ghi khi chạy.
**DoD (tài liệu):** các file CSV Olist có mặt; sample tạo xong; đề tài và kiến trúc medallion ghi trong SPEC/README.
**DoD (spike):** S1, S4, S5 có trạng thái trước; S2–S3 sau khi có SQL warehouse; S6 sau S1. Frontend và ROLAP đã chốt 26/10/2026 (Power BI dashboard, Streamlit truy vấn/DSS). S2–S3 chỉ kiểm kết nối. Nếu spike không đạt: ghi 2 phương án và chờ nhóm.
**Phụ thuộc:** tài khoản Databricks Free Edition (email cá nhân). **Rủi ro:** Free Edition thiếu tính năng → ghi 2 phương án; đường local (R46) là phương án dự phòng, không phải nơi hiện thực trước.

## Phase 1 — Profiling, chốt câu hỏi quyết định và KPI · 13/10 → 18/10 (tuần nghỉ)

**Mục tiêu:** xác nhận giả định dữ liệu trên Bronze **trong Databricks**, rồi khóa phạm vi trong tài liệu.

**Cloud** (cần S1)

- [x] Profiling 9 bảng trên Bronze trong notebook Databricks (`src/notebooks/01_profiling.py`): số dòng, NULL, trùng, phạm vi thời gian, phân bố (R03, R27). Run `SOURCE=volume` 15/10/2026
- [x] Chạy cổng G1–G6 (TOPIC_EVALUATION §1.7) trên Bronze; nếu không đạt → quyết định chuyển T2 (R01). G1–G5 pass, G6 record; giữ T1 (15/10/2026)

**Local** (sau khi có số từ notebook Cloud)

- [x] Liệt kê vấn đề chất lượng thực tế, cập nhật SPEC §3 (bỏ nhãn [GIẢ ĐỊNH] của dữ liệu) (R27, R30)
- [x] Kiểm tra license ngày lễ Brazil và bảng bang→vùng IBGE; Marketing Funnel đã có file (R30). Ngày lễ: không dùng (15/10/2026). IBGE: `data/external/ibge_state_region.csv`, đã có trên Volume `ref/`
- [x] Chốt định nghĩa "trải nghiệm xấu", X, N; 8–12 câu hỏi phân tích ↔ KPI (R01, R25). Review ≤ 2 hoặc giao trễ hẹn; đơn nhiều seller không xóa; measure review seller loại họ và `cross_seller`; `late_flag` vẫn tính; X=10; N=40; 10 câu hỏi trong SPEC
- [ ] Đọc trước slide Ch6–7 (DSS, modeling) (R33, R36)

**Sản phẩm:** `src/notebooks/01_profiling.py` (chạy trên Cloud), SPEC cập nhật sau profiling.
**DoD:** G1–G6 có kết quả đo trên Databricks; đề tài **chốt**; không còn [GIẢ ĐỊNH] dữ liệu quan trọng chưa kiểm. Các [GIẢ ĐỊNH] về Free Edition thuộc spike, không đóng bằng profiling.
**Phụ thuộc:** S1. **Rủi ro:** tuần nghỉ, ít người → chỉ profiling trên Cloud, không mở rộng phạm vi.

## Phase 2 — Thiết kế DW · 17/10 → 22/10

**Mục tiêu:** thiết kế đủ để code DDL/ETL trên Cloud không phải đoán. Viết tài liệu trên máy; tên catalog lấy từ S1.

**Local** (nội dung mô tả bảng sẽ tạo trên Cloud)

- [x] Sơ đồ kiến trúc tổng thể + lý do bottom-up data mart đặt ở Gold (R22, R02)
- [x] Liệt kê bảng Bronze và Silver; ánh xạ layer ↔ staging / integration / DW / data mart / metadata (R22, R45, R29)
- [x] Ghi tên catalog và schema (`bronze`, `silver`, `gold`, `dss`) theo kết quả S1 (R06, R45)
- [x] Thiết kế vật lý Delta: không partition vì ~100 nghìn đơn; nếu partition sau này thì theo cột lọc, không theo cột cardinality cao (R06, R45)
- [x] ERD fact constellation; khai báo granularity từng fact (R04, R23)
- [x] Hierarchy cho date, địa lý khách/seller, sản phẩm (R24)
- [x] Bus matrix, chọn surrogate key, member Unknown, SCD (R41, R04)
- [x] Source-to-target mapping + quy tắc làm sạch/biến đổi (R05, R29, R30)
- [x] Data dictionary; ước lượng số dòng từ profiling Cloud; ghi loại OLAP (R29, R26). ROLAP chốt 26/10/2026, xem SPEC §10
- [x] Influence diagram bản nháp để kiểm tra DW đủ biến cho DSS (R36, R10)

**Sản phẩm:** `docs/DESIGN.md` đầy đủ.
**DoD:** mọi cột fact/dim có nguồn và quy tắc; hợp đồng layer (R45) ghi trong DESIGN; cả nhóm review.
**Phụ thuộc:** Phase 1 Cloud. **Rủi ro:** thiết kế quá rộng → giới hạn 3 fact.

## Phase 3 — Database và ETL (Cloud only) · 21/10 → 31/10

Nguồn khóa: `docs/DESIGN.md` §2–3, §6, §9; `docs/SPEC.md` §6; `docs/architecture.md`. Grain, KPI và SCD Type 1 không đổi. R41 (SCD2 thật) không làm trong phase này; mã giữ ☐.

### Mục tiêu và DoD Cloud

Gold trên `olist_catalog` nạp đủ từ Volume, idempotent, có audit. Chưa đo ở phiên ghi plan; số dòng file giữ baseline DESIGN §2.2, không bịa số mới. Đo được khi một Job serverless chạy xong:

- Job `olist_etl` thành công, đúng 6 task: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly`. Không có task `dss`.
- `gold.etl_audit` của `run_id` đó: đúng 1 dòng mỗi bảng đích (12 Bronze + 14 Silver + 7 dim + `fact_order` + `fact_order_item` + `fact_seller_monthly`). Đủ 10 cột SPEC §6. `rows_unknown_fk` null nếu đích không phải fact.
- Chạy lại cùng Job: count grain 3 fact không tăng; audit chỉ thêm dòng log (không MERGE đè lịch sử).
- SQL sau load: 0 dòng trùng khóa MERGE; mọi FK fact tồn tại trong dim (kể cả `-1`); 7 dim đều có đúng một dòng `-1` nhãn `'Unknown'`.
- Notebook in (không fail job): `rows_read = rows_loaded + rows_dropped_by_dedup + rows_rejected`; `SUM(price)` Silver item = `SUM(price)` `fact_order_item` sau reject; `gmv` seller-tháng = `SUM(price)` item không thuộc `canceled`/`unavailable`, không cộng freight.
- `dss` chỉ là schema rỗng. Không bảng `decision_log`, `seller_risk_score`, `policy_scenario`.

### Giả định và ngoài phạm vi

- Catalog/Volume đã có (S1): `olist_catalog`, `/Volumes/olist_catalog/bronze/raw/` (`olist/`, `funnel/`, `ref/`). Git folder S5, Jobs serverless S4. Đường workspace của notebook xác nhận lúc tạo Job; không đoán path thứ hai.
- **No local warehouse.** Không có `USE_SAMPLE`, `data/sample/`, pyspark local, delta-spark local, pytest local. S6 không chặn Phase 3. R46 giữ ☐ ở S6, Phase 6 và Phase 7.
- Ngoài scope: incremental, append, CDF, Auto Loader (R28, giữ ⏸); SCD2 lịch sử (R41 giữ ☐); view OLAP (R42, Phase 4); M1/M2 và ghi `dss.*` (Phase 5); partition; `_batch_id`; watermark; `WHEN NOT MATCHED BY SOURCE THEN DELETE`.
- Job ETL không ghi `dss.decision_log`. Mũi tên `dss` trên architecture là chỗ Phase 5.

Notebook nguồn là `.py` có `# Databricks notebook source`, cùng kiểu `src/notebooks/01_profiling.py`. DDL chỉ nằm trong notebook sở hữu bảng: setup tạo schema và `gold.etl_audit`; Silver tạo 14 bảng trước overwrite; mỗi notebook Gold tạo bảng của mình trước MERGE. Không còn bản song song ở `src/sql/ddl/`. Widget (không đọc `.env` trên serverless, không hardcode catalog trong SQL): `uc_catalog` (default `olist_catalog`), ba schema, `dss_schema`, `volume_root`, `snapshot_date=2018-10-17`, `run_id` từ `{{job.run_id}}`.

Thứ tự Job: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly`.

### Setup

- [ ] DDL schema và `gold.etl_audit`; comment bảng/cột Gold trên Unity Catalog (R06, R47). File: `src/etl/00_setup.py` cho schema và `etl_audit`. Comment Gold nằm trong `03_gold_dims.py`, `04_gold_facts.py`, `05_gold_seller_monthly.py`.
  - Tạo schema `bronze`, `silver`, `gold`, `dss` nếu chưa có. Setup chỉ tạo `etl_audit`. DDL Gold chạy ở notebook Gold, trước MERGE đầu tiên. Không tạo bảng nghiệp vụ `dss`. Volume đã có: kiểm tra, không tạo lại.
  - `snapshot_date` hằng số trong widget. Không partition.
  - Accept: 4 schema tồn tại; `gold.etl_audit` đủ 10 cột; chưa có bảng `decision_log`.

### Bronze — FULL LOAD OVERWRITE

- [ ] 12 bảng DESIGN §2.2 từ Volume (R07, R30, R45). File: `src/etl/01_bronze.py`. Bảng tạo lúc overwrite, mọi cột nghiệp vụ STRING. Không DDL Bronze riêng.
  - `spark.read` header, mọi cột nghiệp vụ STRING (kể cả zip/id), không trim. Thêm `_ingest_ts`, `_source_file`. Bỏ BOM và ngoặc kép tên cột như `normalize_columns` của profiling. Overwrite ảnh hiện tại.
  - Không join, không cast nghiệp vụ, không `_batch_id`.
  - Accept: 12 dòng audit `layer=bronze`; `rows_rejected=0`; count bảng = count file lần đọc (so baseline §2.2, lệch thì in, không bịa số).

### Silver — FULL LOAD OVERWRITE

- [ ] 14 bảng DESIGN §2.3 (R07, R27, R45). File: `src/etl/02_silver.py`. `CREATE TABLE IF NOT EXISTS` trong notebook này, rồi overwrite dữ liệu, không `overwriteSchema`, để giữ `NOT NULL`.
  - Thứ tự trong notebook: `state_region`, `category_translation`, `geolocation_zip`, `geolocation_city`, rồi `orders`, `order_items`, `order_payments`, `products`, `customers`, `sellers`, rồi `order_reviews`, `order_reviews_dedup`, rồi `closed_deals`, `marketing_qualified_leads`.
  - Cast DESIGN §6. Id/zip STRING. Timestamp `yyyy-MM-dd HH:mm:ss`, lỗi parse → null, không bật `ts_inversion_flag`. Âm hoặc ngoài miền → null, giữ dòng, in DQ, không tính `rows_rejected`.
  - `city_norm`: trim, lower, `translate` đúng bảng accent trong `01_profiling.py`. State upper, left join IBGE. Không khớp vùng → null.
  - Geo: bbox lat [-34, 6], lng [-74, -28]; điểm ngoài bbox = reject. `percentile_approx` 0.5. Mode city/state, hòa thì chuỗi nhỏ nhất. Zip không còn điểm trong bbox thì không có dòng. Khách/seller: zip → (`city_norm`, state) → null, `geo_match_level` `zip|city|none`. Không điền 0.
  - Orders: mốc đảo → null cột chính thức, giữ `raw_*`, so sánh trên `raw_*` (DESIGN §3.3). `order_status` trim+lower, không điền `shipped`/`approved`/`created`.
  - Dedupe trong file: review grain (`review_id`, `order_id`) rồi `order_reviews_dedup` một `order_id` (cửa sổ §2.3). `shared_review_type` gắn sau khi `order_items` của cùng lần overwrite đã có. Khóa grain khác, ngoài hai luật đó: một dòng, chuỗi nghiệp vụ lớn nhất theo thứ tự từ điển. Không chọn bản theo `_ingest_ts`.
  - `fact_order` chỉ đọc `order_reviews_dedup`. MQL lên Silver; `dim_seller` không đọc MQL.
  - Accept: unique grain §2.3; prefix zip trùng = 0 (in); join geo không nhân dòng (in); nhóm review lệch giá trị chỉ cảnh báo.

### Gold dims — MERGE, SCD1, Unknown -1

- [ ] 7 dimension, member `-1`, MERGE hai nhánh (R07, R02). File: `src/etl/03_gold_dims.py`, gồm DDL dim trước MERGE. R41 không làm: không sinh lịch sử SCD2.
  - Chèn member `-1` trước fact: PK `-1`; natural key null; chữ OLAP `'Unknown'`; số/ngày/cờ null (kể cả `is_weekend`, `has_closed_deal`). Không member `'unknown'` thứ hai.
  - Surrogate còn lại: natural key `ORDER BY` tăng dần, `max(key)+1` từ 1. Cùng tập key thì rerun cùng số. Không hash. `date_key = year*10000+month*100+day`. `month_key = year*100+month`.
  - `dim_date`: mọi ngày từ min đến max timestamp chính thức Silver (purchase, approved, carrier, customer, estimated, shipping limit, review). Không lịch lễ. `dim_month` rút từ `dim_date`.
  - `dim_customer`: một `customer_unique_id`, không địa chỉ. `dim_seller`: một `seller_id`; deal = `won_date` sớm nhất, hòa `mql_id` tăng dần; không deal thì segment null (không `'Unknown'`). SCD2-ready: `effective_from=1900-01-01`, `effective_to` null, `is_current=1`. Dòng `-1` ba cột hiệu lực null.
  - `dim_product`: category null → `'Unknown'` + `category_group` §3.4 + `size_band` §3.4. Giữ lỗi chính tả nguồn đến Silver; Gold đổi `name_length` / `description_length`.
  - `dim_order_status` / `dim_payment_type`: distinct chuỗi đã chuẩn hóa; payment null không thành member.
  - MERGE mỗi dim: `WHEN MATCHED THEN UPDATE` và `WHEN NOT MATCHED THEN INSERT` trên surrogate (đã tra natural key). Không `NOT MATCHED BY SOURCE DELETE`. `rows_loaded` không cộng dòng `-1`.
  - Accept: 7 dòng `-1`; mỗi `seller_id` một dòng `is_current=1`; `dim_product` trừ `-1` khớp `silver.products` (in, cảnh báo nếu lệch).

### Gold facts — MERGE

- [ ] `fact_order_item` rồi `fact_order` trong cùng task (R07, R02). File: `src/etl/04_gold_facts.py`, gồm DDL hai fact và CHECK trước MERGE. Comment grain ở đầu notebook. Cờ mức đơn tính từ Silver, lặp lên item, rồi MERGE item trước và order sau. Không đọc Volume.
  - `fact_order`: grain `order_id`. Accumulating snapshot. Năm mốc date role-playing. Địa chỉ khách của đúng `customer_id` nằm trên fact. Review chỉ từ `order_reviews_dedup` (không trung bình, không xóa review tạo trước ngày nhận). `payment_type_key`: một loại chính theo §3.7; `payment_total` vẫn sum mọi dòng. `items_value`/`freight_total` sum mọi status (đơn không item → 0). Không xóa đơn lệch giá.
  - `fact_order_item`: grain (`order_id`, `order_item_id`). Transaction. FK date (purchase, shipping limit), customer, seller, product, order status. Thiếu natural key → `-1`, không bỏ dòng, đếm `rows_unknown_fk`. `late_delivery_flag` là bản copy, không SUM theo item. `price` và `freight_value` là measure riêng. `distance_km` haversine 6371 km, null nếu thiếu tọa độ.
  - `seller_ship_late_flag` tính lại mỗi MERGE từ `snapshot_date` (§3.6): null nếu `canceled`/`unavailable`; null nếu limit null, limit trước purchase, hoặc carrier null vì đảo; 1 nếu carrier sau limit; nếu carrier thật sự thiếu thì 1 khi `TO_DATE(limit) < snapshot_date`, else null.
  - `source_name`: order = `silver.orders` (`rows_read` = số đơn, không cộng review); item = `silver.order_items`.
  - Cùng hai nhánh MERGE. Khóa đã có trên Gold nhưng mất khỏi ảnh Silver thì giữ.
  - Accept: grain unique; không orphan FK; Σ price in khớp; `shared_review_type` chỉ `none|same_seller|cross_seller` hoặc null cùng `review_score`.

### fact_seller_monthly

- [ ] MERGE sau hai fact (R07). File: `src/etl/05_gold_seller_monthly.py`, gồm DDL `fact_seller_monthly` và CHECK trước MERGE.
  - Grain: một seller × một tháng `order_purchase_timestamp` có ít nhất một item. MERGE trên (`seller_key`, `month_key`). `source_name=gold.fact_order_item`. `rows_read` = số item; `rows_loaded` = số cặp. Đọc Gold fact, không đọc Bronze.
  - `gmv = SUM(price)` loại `canceled` và `unavailable`, kể cả đơn nhiều seller. Không cộng `freight_value`. Tháng mọi đơn hủy vẫn có dòng, `gmv=0`. Không bịa seller-tháng 0. Không lọc `min_orders`.
  - Review seller: chỉ đơn `n_sellers=1` và `shared_review_type` thuộc `none|same_seller`. Mẫu `COUNT(DISTINCT order_id)`. `late_flag` vẫn vào bad-experience khi review bị loại. Rate và `aov` không dùng để SUM; lưu cả tử và mẫu.
  - `n_orders_placed` và `n_orders_valid` không cộng ngang seller.
  - Accept: `gmv` đối soát bằng SQL trên item (không so với Σ price full fact); `chk_fsm_totals` không vỡ; không có dòng `n_orders_placed < 1`.

### Jobs

- [ ] Job serverless `olist_etl`, 6 task tuần tự, không task `dss` (R40). File mô tả: `src/etl/olist_etl.job.yml` (task + `depends_on`, không phải DAB đầy đủ). Tạo Job trên workspace trỏ Git folder, compute Serverless (cùng kiểu `s4_smoke`).
  - Một `run_id` cho cả chuỗi. Task sau chỉ chạy khi task trước success.
  - Accept: Run now xanh; lịch có thể lưu Paused (không bắt buộc bật). R40 vẫn ◐ cho đến khi Job ETL thật chạy, rồi mới ☑.

### DQ và audit

- [ ] `gold.etl_audit` 10 cột và CHECK Gold (R27). Helper: `src/etl/_audit.py`, `src/etl/_dq.py`.
  - `audit_id = max+1`. Append, không MERGE. Một dòng mỗi bảng đích mỗi `run_id`.
  - Delta `NOT NULL` trên grain/FK và `CHECK` đúng tên DESIGN §9: `chk_foi_money`, `chk_foi_flags`, `chk_fo_amounts_counts`, `chk_fo_review`, `chk_fo_flags`, `chk_fsm_totals`, `chk_fsm_num_den`, `chk_fsm_rates`. Constraint làm fail ghi dòng xấu.
  - Cảnh báo geo, translation, conflict review, đảo timestamp, G2 delivered thiếu mốc ≤ 5% chỉ in, không fail. Không thêm cột audit.
  - Future work (R28), không làm trong Phase 3: incremental theo watermark, append, CDF, Auto Loader.

### Thứ tự phụ thuộc trong Job

1. `setup` — không phụ thuộc.
2. `bronze` — sau setup.
3. `silver` — sau bronze.
4. `gold_dims` — sau silver (gồm chèn `-1`).
5. `gold_facts` — sau dims. Trong task: `fact_order_item` trước, `fact_order` sau. Cờ `late_delivery_flag` vẫn là cờ mức đơn tính từ Silver.
6. `fact_seller_monthly` — sau gold facts.

### Checklist trước merge code ETL

- Grain comment đúng 3 fact; MERGE key đúng DESIGN §2.4.
- SQL MERGE chỉ hai nhánh UPDATE/INSERT. Không có `NOT MATCHED BY SOURCE`.
- `gmv` không cộng `freight_value` hay `freight_total`. `items_value` không áp lọc hủy.
- Fan-out: geo 1 dòng/khóa; một payment type mỗi đơn; một review mỗi đơn trên fact; đơn nhiều seller không bị xóa; `late_delivery_flag` không SUM theo item.
- `-1` có trước fact; FK hỏng trỏ `-1`; không drop dòng fact; không nhãn `'unknown'` thứ hai.
- `dim_seller` một dòng mỗi `seller_id`, không SCD2 history.
- Zip và id vẫn STRING đến Gold.
- Job không ghi `dss` và không đọc `data/sample` hay `data/raw`.
- `rows_loaded` của dim không cộng dòng `-1`.

### Rủi ro Free Edition / serverless

- S4 đã chứng minh Job serverless chạy được. Quota phút, timeout, số task tối đa chưa đo — ghi [GIẢ ĐỊNH] nếu Run now fail, đưa 2 phương án (tách job hoặc giảm collect), không tự đổi kiến trúc.
- Geolocation khoảng 1 triệu dòng: không `collect` / `toPandas`. Overwrite một bảng, không cache cả Volume.
- Serverless không thấy `.env` laptop: mọi tham số qua widget Job. Sai catalog → dừng, không tạo catalog mới.
- Git folder lệch `main`: pull trước Run now.
- Constraint CHECK fail cả batch: sửa dòng (set null đúng DESIGN §6) rồi chạy lại; không tắt constraint.
- `audit_id = max+1` an toàn vì 6 task tuần tự, không ghi audit song song.
- SQL Warehouse (S2/S3) không cần cho Job ETL.

**Sản phẩm:** `src/etl/`. DDL nằm trong các notebook đó. `src/etl/olist_etl.job.yml` chỉ là skeleton, chưa phải file deploy. Không có `src/tests/` trong Phase 3. Không có `src/sql/ddl/`.
**Phụ thuộc:** Phase 2 và S1. **Rủi ro:** lỗi dữ liệu → set null, đếm `rows_rejected` khi dòng bị bỏ hẳn, in DQ trong notebook. Không chặn pipeline Cloud.

## Phase 4 — OLAP và dashboard · 29/10 → 06/11

**Mục tiêu:** 5 phép OLAP trên **Gold trong Databricks** trước. Frontend gắn vào Gold đó; không dựng OLAP trên sample local trước.

**Cloud**

- [ ] View phục vụ OLAP trên Gold, nếu làm R42. Fact và dimension vẫn là bảng Delta (R08, R42)
- [x] 5 truy vấn OLAP bằng Spark SQL trên Gold: slice, dice, drill-down, roll-up, pivot — mỗi truy vấn 1 câu hỏi (R25, R08). Chạy trên SQL Warehouse `cfb33f9733d84eff` ngày 07/11/2026.
- [ ] (ĐC) so sánh thời gian truy vấn có/không aggregate view, đo trên SQL warehouse (R42)

**Local → Cloud**

- [ ] Power BI Desktop: dashboard ROLAP, đọc Gold qua SQL Warehouse. Kết nối kiểm ở S3 (R09, R26)
- [ ] Bộ lọc tương tác + drill theo hierarchy trên Power BI (R09, R24)

**Sản phẩm:** `src/sql/olap_queries/`, `src/sql/views/`, dashboard Power BI.
**DoD:** demo đủ 5 phép trên Gold Cloud; kết quả khớp Spark SQL. Công cụ đã chốt 26/10/2026: Power BI cho dashboard, ROLAP qua SQL Warehouse. Streamlit thuộc Phase 5 (truy vấn và DSS).
**Phụ thuộc:** Phase 3 Cloud (Gold đã có dữ liệu). **Rủi ro:** UI tốn thời gian → ưu tiên 5 câu SQL trên Cloud. Nếu S3 không đạt, dừng ở 2 phương án và chờ nhóm.

## Phase 5 — DSS · 26/10 → 08/11

**Mục tiêu:** mô hình đọc Gold trên Databricks, ghi `dss.`* trên workspace trước. UI local chỉ là lớp gọi warehouse.

**Cloud**

- [ ] Feature view (ví dụ `dss.v_seller_features`) chỉ trên `gold.*` (R31, R32)
- [ ] M2 mô phỏng chính sách + what-if trên dữ liệu Gold (làm trước, dùng p_i đơn giản) (R34, R33, R10)
- [ ] M1 logistic regression, train/test theo thời gian, metric AUC/Brier; huấn luyện trên Gold, không trên Silver (R33, R44)
- [ ] Goal seeking θ theo ràng buộc GMV; sensitivity tornado (R35)
- [ ] Job DSS ghi `dss.seller_risk_score` và `dss.policy_scenario` trên workspace. Streamlit ghi thêm `dss.decision_log` qua SQL Warehouse (R31, R37)

**Local → Cloud** (sau khi bảng `dss.`* đã có trên Cloud và S2 đạt)

- [ ] UI DSS và truy vấn: trang Điểm rủi ro, What-if, Goal seek, Quyết định & export. Streamlit local đọc Gold và `dss.*` qua SQL Warehouse (R32, R34). Nếu S2 không đạt: ghi 2 phương án, chờ nhóm, không tự chuyển UI sang đọc CSV

**Local** (tài liệu, không cần cluster)

- [ ] Influence diagram bản cuối, bảng biến, phân loại DSS, ánh xạ pha (R36, R37, R38)
- [ ] (ĐC) luật khuyến nghị hành động theo hạng (R43)

**Sản phẩm:** `src/dss/`, trang DSS trong `src/frontend/`.
**DoD:** so sánh ≥ 3 phương án (P0/P1/P2), số liệu lấy từ Gold trên Cloud; không có `read_csv` / đường dẫn `data/raw` trong `src/dss/`.
**Phụ thuộc:** Phase 3 Cloud (`gold.fact_seller_monthly`). UI cần S2. **Rủi ro:** M1 kém → giữ baseline, nêu ở hạn chế; M2 + what-if trên Cloud là tối thiểu bắt buộc.

## Phase 6 — Tích hợp, kiểm thử, đánh giá · 07/11 → 10/11

**Mục tiêu:** một vòng end-to-end trên Databricks trước, rồi lặp lại trên sample local.

**Cloud**

- [ ] Chạy end-to-end trên Databricks: Bronze → Silver → Gold → OLAP → DSS (R07, R10)
- [ ] Backtest chính sách trên Gold: áp dụng tại tháng t, so dự báo vs thực tế t+1 (R44, R11)
- [ ] Lưu screenshot và output của đường Cloud (R46)

**Local** (sau khi vòng Cloud chạy xong)

- [ ] Chạy cùng pipeline trên `data/sample/` bằng pyspark + delta-spark (R46)
- [ ] Lưu screenshot và output đường local (phòng mất tài khoản hoặc người chấm không vào được workspace) (R46)
- [ ] Viết `README.md` mục "Cách chạy": mục Cloud trước, mục local trên sample sau (R16, R46)

**Local** (báo cáo số liệu, không chạy cluster)

- [ ] Bảng đánh giá: câu hỏi/KPI ban đầu ↔ đạt/chưa đạt (R11)
- [ ] Liệt kê hạn chế (dữ liệu, mô hình, giả định e_k/r, giới hạn Free Edition) và hướng phát triển (incremental theo watermark, CDF, Auto Loader, streaming, CDC, Kafka, Lakehouse Federation, Reverse ETL) (R12)

**Sản phẩm:** kết quả test, số liệu đánh giá, hình trong `docs/report/`.
**DoD:** đường Cloud có hướng dẫn và bằng chứng đã chạy. Đường local trên sample chạy được theo README.  
**Phụ thuộc:** Phase 4–5 Cloud. **Rủi ro:** lỗi tích hợp → tích hợp sớm trên Databricks, không dồn đường local lên trước.

## Phase 7 — Báo cáo, slide, video, đóng gói, tập thuyết trình · 09/11 → 15/11

**Mục tiêu:** nộp đúng hạn. Soạn trên máy; nội dung lấy từ bằng chứng Cloud ở Phase 6.

**Local**

- [ ] Báo cáo PDF theo mục lục đề xuất trong file phân tích, phủ L.O.1.1–4.2 (R15, R21)
- [ ] Mục phương pháp phát triển (prototyping) + rủi ro dự án (R39)
- [ ] Mục đánh giá, hạn chế, hướng phát triển (R11, R12)
- [ ] Bìa: thành viên, MSSV, vai trò, link GitHub, link workspace hoặc bằng chứng Cloud, link video nếu có (R14, R19)
- [ ] Slide PDF; chia phần cho **mọi thành viên** (R18, R13)
- [ ] Video 10–15' nếu không thuyết trình trực tiếp; YouTube unlisted/Drive (R13, R19)
- [ ] Đóng gói ZIP: báo cáo PDF, `src/` (notebook dạng `.py`), `data/` (sample + link full), slide PDF. README: cách xem kết quả Cloud, rồi cách người chấm chạy local trên sample (R20, R16, R17, R46)
- [ ] Nộp LMS **trước 14/11** (dự phòng 1 ngày); tập thuyết trình + Q&A (R20, R13)

**Sản phẩm:** `CO4031_<Nhóm>.zip`.
**DoD:** đã nộp, đã kiểm tra file trên LMS; người chấm có hướng dẫn chạy lại trên sample và thấy bằng chứng đã chạy trên Databricks.
**Phụ thuộc:** Phase 6. **Rủi ro:** dồn việc cuối → viết báo cáo dần từ Phase 2 (`docs/report/`).

---

## Kiểm tra chéo RTM

Mọi yêu cầu mức **BB** và **BB** trong SPEC §2 phải xuất hiện ở ≥ 1 task phía trên.

| Mức           | Mã                                                                                                 | Có task?                                                                                                                                                  |
| ------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BB [ĐỀ]       | R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20 | ☑ tất cả có task                                                                                                                                          |
| BB [SUY LUẬN] | R21, R22, R23, R24, R25, R27, R30, R31, R32, R33, R34, R36, R37, R38, R45                          | ☑ tất cả có task                                                                                                                                          |
| NC            | R26, R28, R29, R39, R42, R44, R46                                                                  | ☑ tất cả có task (R28: ⏸ deferred / future work, không hiện thực trước hạn nộp. R46: S6, Phase 6 Local, Phase 7. Phase 3 không có đường local warehouse.) |
| ĐC            | R35, R40, R41, R43, R47                                                                            | ☑ tất cả có task (R47: comment bảng/cột Gold ở Phase 3 Cloud)                                                                                             |

**R-xx bắt buộc chưa có task:** không có. Yêu cầu NC/ĐC chưa có task: không có. Kiểm tra lại mỗi khi sửa SPEC hoặc PLAN (13/10/2026: tách Cloud / Local, không thêm hoặc bỏ R-xx).
