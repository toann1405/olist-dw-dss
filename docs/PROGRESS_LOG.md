# PROGRESS LOG

## Hướng dẫn cho AI/người mới
1. Thứ tự đọc: `README.md` → `docs/SPEC.md` → `docs/PLAN.md` → **mục đầu tiên** của nhật ký bên dưới (mới nhất ở trên).
2. Sau **mỗi phiên làm việc**, cập nhật khối "Trạng thái hiện tại" và thêm một mục nhật ký mới **ở trên cùng**.
3. Không đổi quyết định đã chốt trong SPEC mà không ghi lý do ở đây và cập nhật SPEC §10.
4. Ghi rõ ai làm gì (phục vụ peer review — đề mục 1.3).

## Trạng thái hiện tại

| Mục | Nội dung |
|---|---|
| Phase hiện tại | Phase 4 và Phase 5 dùng một app Streamlit. Power BI là future work. T1 chốt 15/10/2026. X=10, N=40 |
| Đang làm | App local đã đọc Gold qua SQL Warehouse. Bảng điểm DSS trên warehouse chỉ có 1 dòng, `n_orders_valid` = 1 |
| Blocker | Job DSS chưa có snapshot đủ seller cho `min_orders` = 5. Checkbox PLAN và RTM chưa tick |
| Việc tiếp theo | Chạy `src/dss/dss_job.py` trên workspace để ghi đủ `dss.seller_risk_score`, rồi mở lại trang Seller risk và Policy |
| Cập nhật | 11/11/2026 (tháng chấm 2018-08) |

---

## Nhật ký

### 11/11/2026 — Tháng chấm không còn là tháng lịch cuối

- **Đã làm:** `AS_OF_MONTH` = `2018-08` trong `src/dss/params.py`. Job DSS chấm đúng tháng đó, không dùng `MAX(month)`. UI Seller risk và Policy chỉ đọc điểm của tháng này. Kỳ không đủ seller thì ẩn thẻ phần trăm, Pareto và insight. Thêm nhãn dự báo/thực tế và khung bài toán 30 giây trên Policy.
- **Đã đo trên Gold, `n_orders_valid` cộng theo seller-tháng:**

  | Tháng | Seller | Đủ ≥ 5 đơn | Đơn hợp lệ |
  |---|---:|---:|---:|
  | 2018-06 | 1175 | 312 | 6259 |
  | 2018-07 | 1261 | 304 | 6334 |
  | 2018-08 | 1278 | 342 | 6540 |
  | 2018-09 | 1 | 0 | 1 |
  | 2018-10 | 0 | 0 | 0 |

- **Chưa chạy:** notebook `src/dss/dss_job.py` trên Databricks. Bảng điểm hiện vẫn là tháng 2018-09 với 1 seller. Trước khi chạy job, hai trang báo kỳ 2018-08 chưa đủ dữ liệu. Sau khi chạy, `sellers` trong log phải là số seller của 2018-08, không phải 1.
- **Không làm:** không đổi công thức M1/M2. Không commit `.env`.

### 11/11/2026 — Seller risk theo hướng intelligence

- **Đã làm:** trang Seller risk đọc `dss.seller_risk_score` và join `dim_seller` (vùng, bang, thành phố, business_segment, lead_type, won_date). Hạng và đơn xấu dự kiến lấy từ `simulate(..., "P2", PolicyParams())`, không viết lại ngưỡng. `min_orders` vẫn là `MIN_ORDERS` = 5. Tab đánh giá hiện câu chờ khi chưa có `dss.model_eval`. DDL ba bảng contrib/eval/calibration được thêm vào job DSS, job chưa chạy lại.
- **Đã chạy:** `python -m pytest src/tests/test_recommend.py src/tests/test_stats.py` — 6 passed. Bảng điểm: 1 seller `25be943a321c8938947bdaabca979a90`, `p_bad` 0.345639, `n_orders_valid` 1, `q_bar` 1.0, `gmv` 145.0. P0/P1/P2 `expected_bad_orders` đều 0.3456389245948667, 0 seller bị gắn cờ. Trang hiện 0 seller đủ điều kiện / 1 seller tổng với ngưỡng 5 đơn. `p_bad` không đổi so với bảng đã ghi.
- **Chưa làm:** không ghi `seller_risk_contrib` hay `model_eval` vì không chạy lại job (chạy lại sẽ ghi đè điểm). Không có 3 seller để đối soát contribution. Không commit `.env`.

### 11/11/2026 — KPI và OLAP analytic

- **Đã làm:** thêm Wilson interval, Pareto, từ điển tách review seller / review sàn và bàn giao trễ / giao trễ tới khách. Trang KPI giữ sáu công thức cũ khi không bật giai đoạn đủ dữ liệu, funnel hay khoảng tháng. Thêm dải ràng buộc, hero trải nghiệm xấu, tab xu hướng / nơi phát sinh / seller / độ tin cậy. OLAP đổi tên tab theo câu hỏi SPEC, kết luận từng tab, CSV, pivot loại Unknown và làm mờ n < 30.
- **Đã chạy:** `python -m pytest src/tests/test_stats.py src/tests/test_insights.py` — 15 passed. Tổng GMV theo tháng, bộ lọc trống: 13494400.74. `market_quality` bộ lọc trống: đơn 98666, đơn nhiều seller 1278, review loại khỏi measure seller 1943, bad_orders 16444, bad_eligible 98079, late_orders 6534, late_eligible 96447. App trang KPI hiện GMV R$ 13,49 tr, đơn 98.199, AOV R$ 137,42, bàn giao trễ 10,1%, review seller 13,7%, cancel 0,5%.
- **Chưa làm:** bản đồ Brazil, histogram nguyên nhân, treemap. Không đổi SQL của năm phép OLAP đã khóa. Không commit `.env`.

### 11/11/2026 — Policy scenario theo logic quyết định

- **Đã làm:** trang Policy xếp ① what-if, ② goal seeking, ③ sensitivity (biểu đồ tornado), ④ chốt. Tên hiển thị ở `lib/labels.py`. `recommend_policy` sinh câu từ kết quả. Giả định nằm trong form "Áp dụng". `decision_id` là UUID. X=10 và N=40 vẫn khóa, không đưa vào slider. Không sửa `compare_policies`, `goal_seek`, `tornado` hay giá trị mặc định trong `src/dss/params.py`.
- **Đã chạy:** `python -m pytest src/tests/test_insights.py` — 12 passed. Tham số mặc định trên bảng điểm hiện có (1 seller): P0, P1 và P2 đều `expected_bad_orders` 0.3456389245948667, GMV bị ảnh hưởng 0.0, 0 seller, đạt cả hai trần. Hàm M2 không đổi nên trước và sau refactor là cùng ba số này. App mở được. Bấm "Dùng ngưỡng gợi ý này" đổi dòng chốt thành "ngưỡng gợi ý".
- **Kho:** `dss.decision_log` có 0 dòng, `decision_id` đang BIGINT. Đã DROP và CREATE lại với `decision_id` STRING. Smoke insert UUID `c35eb05c-026b-4065-b475-c275ccfc7675` rồi DELETE, đếm lại còn 0. Không bấm ghi từ UI hai lần.
- **Không làm:** không đổi công thức M2. Không commit `.env`.

### 11/11/2026 — Streamlit: kể chuyện cho business

- **Đã làm:** điều hướng 0–4 theo câu hỏi. `lib/glossary.py` là một nguồn định nghĩa. Insight trang 1–4 sinh từ dữ liệu (`lib/insights.py`), chỉ so nhóm có n ≥ `min_orders` (5). Query mới `story_by_region` và `active_sellers` dùng tham số, không f-string. Sáu KPI giữ SQL và công thức cũ. Không tick PLAN hay RTM.
- **Đã chạy:** `python -m pytest src/tests/test_insights.py` — 8 passed. Bộ lọc tất cả, sáu KPI: GMV 13494400.74, đơn hợp lệ 98199, AOV 137.418922188617, bàn giao trễ 0.10069651741293532, review xấu 0.13692249984370766, cancel 0.004733140088784384. Khớp số đã ghi 10/11. App hiện GMV R$ 13,49 tr, trải nghiệm xấu 16,8%, 3.053 seller. Insight tất cả: Norte 26,9% (n=26). Năm 2018: 17,4%, Norte 20,0% (n=5); tổng GMV 7341182.41, tử 9315, mẫu 53514. Trang Seller risk: "Chưa đủ dữ liệu để kết luận" vì bảng điểm không có seller với `min_orders` 5. Policy mở được, tháng chấm 2018-09, insight P1 trên snapshot hiện có (một seller).
- **Không làm:** không đổi grain, không sửa ETL, không commit `.env`.

### 11/11/2026 — Xóa file Power BI

- **Đã làm:** xóa `src/frontend/dashboard.pbix`, `dashboard.pbip`, `dashboard.Report/`, `dashboard.SemanticModel/`, và hai thư mục backup `_backup_pbip_20261110_114343`, `_backup_pbip_20261110_120846`. App Streamlit giữ nguyên. Không tick checkbox PLAN hay cột TT của RTM. Quyết định SPEC §10 (Power BI là future work) không đổi.
- **Không làm:** không xóa `src/frontend/olist_seller_performance.lvdash.json` (file Lakeview / AI/BI, không phải Power BI). Không sửa ETL. Không commit.

### 10/11/2026 — UI Streamlit: theme, Home, KPI card, tab OLAP

- **Đã làm:** theme sáng, `lib/ui.py`, sidebar lọc dùng chung, trang Home, KPI thành card và chart, OLAP thành 5 tab. Không đổi công thức tử/mẫu. Không tick PLAN hay RTM.
- **Đối soát cùng filter “Tất cả” và “2018 / Sudeste”:** GMV, số đơn, bàn giao trễ, review, cancel khớp từng số đã đo trước refactor (GMV tất cả 13494400.74, đơn 98199, trễ 11132/110550, review 13141/95974, hủy 467/98666). Tổng GMV theo tháng và theo vùng cũng ra 13494400.74 và 11132/110550.
- **Đã mở app:** Home, KPI, OLAP, Seller risk, Policy đều load. Seller risk với `min_orders` 5 vẫn trống vì bảng điểm chỉ có 1 seller với 1 đơn.
- **Việc tiếp theo:** chạy `src/dss/dss_job.py` để có đủ điểm seller.

### 10/11/2026 — OLAP Explorer hiện năm phép trên một trang

- **Đã làm:** `src/frontend/pages/olap.py` bỏ ô chọn một phép. Cùng một trang có roll-up (cột ngang), drill-down (đường hoặc vùng), slice (cột ngang), dice (cột nhóm) và pivot (ô nhiệt). SQL và cách chia tử/mẫu không đổi. Không tick PLAN hay RTM.
- **Đã chạy:** mở Streamlit, trang `/olap` vẽ đủ năm phần trên SQL Warehouse. Không đo lại số KPI.
- **Việc tiếp theo:** vẫn là chạy `src/dss/dss_job.py` để bảng điểm đủ seller.

### 10/11/2026 — Phase 4–5 — Một app Streamlit, đã chạy KPI trên warehouse

- **Đã làm:** gộp dashboard và DSS vào `src/frontend/app.py`. Power BI chuyển thành future work trong SPEC §7, §10, architecture, PLAN, DESIGN, README và rule `00`, `02`, `08`, `09`. App đọc `gold.*` và `dss.*` qua SQL Warehouse. Không đọc Volume hay Silver. Không sửa `src/etl/`. Không tick checkbox PLAN hay cột TT của RTM.
- **Đã chạy, phiên này:** `SELECT 1` trên SQL Warehouse thành công. Câu KPI không lọc năm/vùng: `gmv` = `gmv_from_items` = 13494400.74; bàn giao trễ 11132 / 110550 = 0.10069651741293532; review seller 13141 / 95974 = 0.13692249984370766; AOV 13494400.74 / 98199 = 137.418922188617; cancel 467 / 98666 = 0.004733140088784384. Cùng bộ lọc năm 2018 và vùng seller Sudeste: `gmv` = `gmv_from_items` = 5771299.43; bàn giao trễ 4481 / 49754; review seller 6164 / 43641; AOV 5771299.43 / 44641; cancel 223 / 44864.
- **UI:** mở Streamlit local, trang Tổng quan KPI hiện đúng các số không lọc ở trên. Trang OLAP Explorer vẽ roll-up theo vùng. Trang Seller risk với `min_orders` = 5 báo chưa có dòng. Trang Policy mở được. Không bấm nút ghi quyết định.
- **DSS trên warehouse, đếm trong phiên này:** `dss.seller_risk_score` 1 dòng, `n_orders_valid` = 1; `dss.policy_scenario` 3 dòng; `dss.decision_log` 0 dòng. Một dòng điểm không phải kết quả chấm toàn bộ seller. Không ghi AUC hay Brier.
- **Không làm:** không chạy lại notebook DSS, không INSERT `decision_log`, không tick R09. Connector trên máy này nhận tham số bằng `?`.
- **Việc tiếp theo:** chạy `src/dss/dss_job.py` trên workspace, rồi đối soát trang Seller risk và Policy với SQL Editor.

### 10/11/2026 — Phase 5 — Mã DSS tối giản, chưa chạy trên warehouse

- **Đã làm:** thêm view `src/sql/views/v_seller_features.sql` chỉ từ `gold.*`. Thêm `src/dss/params.py`, `policy.py`, `train.py`, notebook `dss_job.py` và skeleton `dss_job.yml`. Streamlit `src/frontend/dss_app.py` có bốn trang DSS và một ô SELECT. Ghi cột `dss` vào DESIGN §6.6. Influence diagram SPEC §8 đánh dấu bản cuối. `00_setup.py` cho phép bốn object DSS đã đặt tên, vẫn chặn tên lạ. Không thêm task vào job ETL. Không làm R43. Không tạo `requirements.txt`.
- **Kiểm tra local:** gọi `train_and_score`, `compare_policies`, `goal_seek` và `tornado` trên DataFrame giả. Hàm chạy xong và trả ba phương án. Đây không phải số của Gold, không ghi AUC hay Brier vào SPEC.
- **Không làm:** không chạy notebook trên Databricks, không tạo view trên warehouse, không ghi `dss.seller_risk_score`. Không tick checkbox Phase 5 trong PLAN. Không nối Power BI. Không commit.
- **S2:** chưa gửi `SELECT 1`. File `.env` có mặt nhưng `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH` và `DATABRICKS_TOKEN` đang trống. `import databricks` lỗi `ModuleNotFoundError`. Streamlit đã có. Hai phương án, chưa chọn: (1) điền ba biến và cài `databricks-sql-connector` sau khi nhóm đồng ý, rồi chạy lại `SELECT 1`; (2) giữ app hiện tại và chỉ mở UI sau khi S2 nối được. Không chuyển UI sang đọc CSV.
- **RTM:** R10, R31, R32, R33, R34, R35 sang ◐. R36, R37, R38 sang ☑ vì sơ đồ, bảng biến, phân loại và ánh xạ pha trong SPEC §8 được chốt. R42 giữ ☐.
- **Việc tiếp theo:** người dùng điền `.env` và chạy job DSS trên workspace. Nếu job in được `model_name`, AUC hoặc Brier, và ba dòng P0/P1/P2, lúc đó mới tick PLAN.

### 07/11/2026 — Phase 4 — Năm câu OLAP trên SQL Warehouse

- **Đã làm:** thêm `src/sql/olap_queries/` với năm file, mỗi file một phép SPEC §7. Chạy trên warehouse `Serverless Starter Warehouse`, id `cfb33f9733d84eff`, catalog `olist_catalog`. Cả năm câu `SUCCEEDED`, kết quả không bị cắt. Số dòng: roll-up 665, drill-down 634, slice 612, dice 13, pivot 9. Mức tất cả của roll-up: `late_items` 11132, `eligible_items` 110550, `late_ship_rate` 0.10069651741293532. Slice lọc ví dụ `electronics_it_telephony`. Tick checkbox năm câu trong PLAN. R08 và R25 sang ☑. R42 và Power BI giữ ☐.
- **Không làm:** không tạo `src/sql/views/`. Không mở Power BI. Không xuất CSV. Không tick R09. Không đếm lại `gold.etl_audit` của Job ETL. Không commit.
- **Power BI, chưa nối:** hostname `dbc-6a3fb372-922e.cloud.databricks.com`, HTTP path `/sql/1.0/warehouses/cfb33f9733d84eff`. Token để trong `.env`, không ghi ở đây. License Pro: dựng bằng Power BI Desktop, DirectQuery, rồi Publish lên app.powerbi.com. Không dùng nút Publish trong Catalog.
- **File đã sửa:** `src/sql/olap_queries/`, `docs/PLAN.md`, `docs/SPEC.md`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** người dùng nối Power BI Desktop. Nếu không nối được, ghi hai phương án và dừng.

### 07/11/2026 — Phase 3 — Notebook Databricks-only, DDL về notebook

- **Đã làm:** bỏ lớp `_spark()` / `SparkSession.getActiveSession()`. `00_setup` chỉ tạo 4 schema và `gold.etl_audit`, rồi kiểm tra Volume, không tạo lại Volume. DDL Gold chuyển vào notebook Gold, `CREATE TABLE IF NOT EXISTS` trước MERGE, giữ kiểu, `NOT NULL`, CHECK và comment. Silver giữ `NOT NULL` bằng DDL trong `02_silver.py` và overwrite không `overwriteSchema`. Bronze không có DDL riêng vì không có ràng buộc và ghi tạo bảng STRING. Xóa bản `src/sql/ddl/` đã có trong working tree, không khôi phục và không giữ hai bản. `olist_etl.job.yml` vẫn là skeleton, không phải file deploy. Giữ logic GMV status null, seller `-1` trên snapshot tháng, audit 10 cột và DQ grain.
- **Không làm:** không Run now. Không tick PLAN. Không đổi trạng thái R02, R06, R07, R40, R41, R47. Không đổi grain, KPI, surrogate key. Không commit.
- **File đã sửa:** `src/etl/`, `docs/PLAN.md`, `docs/DESIGN.md` §9, `docs/SPEC.md` (đường dẫn bằng chứng), `docs/architecture.md`, `README.md`, `docs/PROGRESS_LOG.md`.
- **Tự kiểm:** static checks only. Chưa chạy Databricks nên không kết luận pipeline chạy được.
- **Việc tiếp theo:** gắn Job trên workspace và Run now.

### 06/11/2026 — Phase 3 — Chốt GMV, seller -1, rows_loaded

- **Đã làm:** `fact_seller_monthly` vẫn loại seller `-1` và tháng mua thiếu, đếm `rows_rejected`, không tạo dòng tháng cho `-1`. Audit ghi `rows_unknown_fk=0`. `gmv`, `n_orders_valid` và `n_items_valid` giữ đơn có `order_status` null. `rows_loaded` vẫn là số dòng source của lần MERGE. Notebook in thêm grain before/source/after, số khóa Gold không có trong source, và tổng price/GMV của source batch so với tổng bảng.
- **Không làm:** không Run now. Không tick PLAN. Không đóng R07, R40, R47.
- **File đã sửa:** `src/etl/04_gold_facts.py`, `src/etl/05_gold_seller_monthly.py`, `src/etl/_dq.py`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** gắn Job trên workspace và Run now.

### 05/11/2026 — Phase 3 — Scaffold ETL Cloud

- **Đã làm:** viết notebook `src/etl/` (`00_setup` đến `05_gold_seller_monthly`, `_audit`, `_dq`), DDL `src/sql/ddl/`, và skeleton `src/etl/olist_etl.job.yml`. Bronze/Silver FULL LOAD OVERWRITE. Gold MERGE chỉ `WHEN MATCHED THEN UPDATE` và `WHEN NOT MATCHED THEN INSERT`. Trong task facts: `fact_order_item` trước, `fact_order` sau; cờ trễ vẫn là cờ mức đơn tính từ Silver. `gmv` chỉ cộng `price`. Schema `dss` để trống. Không đường local.
- **Không làm:** không Run now trên workspace. Không đo số dòng mới. Không pytest. Không tick checkbox PLAN. Không đóng R07, R40, R47.
- **File đã sửa:** `src/etl/`, `src/sql/ddl/`, `docs/PLAN.md` (một câu thứ tự fact), `docs/DESIGN.md` §9, `docs/PROGRESS_LOG.md`.
- **RTM:** R07 giữ ☐, R40 giữ ◐, R47 giữ ☐. R27 giữ ◐. R46 giữ ☐.
- **Việc tiếp theo:** trên Databricks, kéo Git folder, tạo Job serverless `olist_etl` với 6 task theo `src/etl/olist_etl.job.yml`, `run_id={{job.run_id}}`, rồi Run now.

### 05/11/2026 — Phase 3 — Plan ETL Cloud-only

- **Đã làm:** ghi plan Phase 3 chỉ trên Databricks. Job `olist_etl` có 6 task: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly`. Không task `dss`. Không `USE_SAMPLE`, không `data/sample/`, không pytest local. DQ Phase 3 là Delta constraints và cảnh báo in ở notebook. Trong task gold facts: `fact_order` trước, rồi copy `late_delivery_flag` sang `fact_order_item`.
- **Không làm:** không viết DDL, notebook, job, hay test. Không đo lại Volume. Không đóng R07, R27, R40, R46, R47. R27 giữ ◐. R46 giữ ☐ (S6, Phase 6, Phase 7). R41 giữ ☐.
- **File đã sửa:** `docs/PLAN.md` (v0.6), `docs/SPEC.md` (v0.9), `docs/DESIGN.md` §9, `docs/architecture.md`, `docs/PROGRESS_LOG.md`, `README.md`, `.env.example`, `.cursor/rules/` (`04-data-integrity`, `05-medallion-layers`, `07-spark-databricks`, `10-testing-dq`).
- **Quyết định:** SPEC §10, ngày 05/11/2026. ETL warehouse Phase 3 chỉ Databricks. Không sửa mục nhật ký cũ.
- **RTM:** không đổi trạng thái R07 ☐, R27 ◐, R40 ◐, R46 ☐, R47 ☐. R27 bỏ pytest khỏi sản phẩm Phase 3. R46 bỏ phase 3 khỏi cột phase.
- **Việc tiếp theo:** viết DDL và notebook theo checklist Phase 3. Checkbox vẫn trống vì load chưa chạy.

### 05/11/2026 — Phase 2 — Sửa hợp đồng trước khi sang Phase 3
- **Đã làm:** một luật hiện hành cho từng chủ đề. Gold `MERGE` chỉ `WHEN MATCHED THEN UPDATE` và `WHEN NOT MATCHED THEN INSERT`. Không `WHEN NOT MATCHED BY SOURCE THEN DELETE`. `dss.decision_log` do Streamlit append qua SQL Warehouse. Job ETL Gold không ghi bảng này. Job DSS vẫn ghi điểm và kịch bản. Bronze/Silver FULL LOAD OVERWRITE; Jobs setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly` → dss; Power BI + Streamlit qua SQL Warehouse; `etl_audit` 10 cột; không `_batch_id`, không watermark trong hợp đồng hiện tại. `gmv` = `sum(price)`, freight là measure riêng. Review dùng chung là [GIẢ ĐỊNH]: grain (`review_id`, `order_id`), một review mới nhất mỗi `order_id`, cột `shared_review_type` (`none` / `same_seller` / `cross_seller`). Measure seller loại `cross_seller` và đơn nhiều seller. KPI sàn giữ `cross_seller`. Mẫu `COUNT(DISTINCT order_id)`. `late_flag` vẫn tính khi review bị loại. 789 `review_id` và 814 dòng thừa là số đã đo. Đỉnh tháng 3/2018 khoảng 1,6% vẫn là [GIẢ ĐỊNH]. Luật cuối chờ sensitivity top-40 sau Gold. X=10, N=40 giữ nguyên. Câu bị thay nằm ở SPEC §10, mục lịch sử.
- **Không làm:** không viết DDL, ETL, notebook, test. Không đo lại Volume.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.8), `docs/PLAN.md`, `docs/architecture.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`, `README.md`, `data/README.md`, `.cursor/rules/` (`02-ambiguity-scope`, `05-medallion-layers`, `06-dw-modeling`, `07-spark-databricks`, `09-dss`).
- **Quyết định:** SPEC §10, ngày 05/11/2026. Dòng MERGE có nhánh xóa (26/10) và dòng review null trên fact (22/10, 26/10) đánh dấu superseded.
- **RTM:** không đổi mã. R28 giữ ⏸ deferred / future work.
- **Việc tiếp theo:** Phase 3, DDL và ETL theo hợp đồng đã sửa.

### 26/10/2026 — Tối: sửa nhận xét sau khi đơn giản hóa load
- **Đã làm:** review conflict in ở notebook, không ghi audit. `etl_audit` chỉ 10 cột đếm dòng. Đối soát `rows_read = rows_loaded + rows_dropped_by_dedup + rows_rejected` in trong cùng `run_id`. `rows_rejected` chỉ là dòng bỏ hẳn. Giá trị set null mà vẫn giữ dòng thì in DQ. `MERGE` Gold thêm `WHEN NOT MATCHED BY SOURCE THEN DELETE`, trừ member `-1`. Job DSS ghi điểm và kịch bản. Streamlit ghi thêm `dss.decision_log` qua SQL Warehouse. Sơ đồ: Gold → job DSS → `dss`; Gold và `dss` → SQL Warehouse → Power BI và Streamlit. R28 chuyển ⏸ deferred / future work vì đề cho phép incremental hoặc full refresh và dataset tĩnh. Tie-break thứ tự từ điển ghi vào quyết định 26/10.
- **Không làm:** không đổi grain, measure, SCD, surrogate key. Không viết DDL hay ETL. Không đánh dấu milestone Notion.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/PLAN.md`, `docs/architecture.md`, `docs/PROGRESS_LOG.md`, `README.md`, `.cursor/rules/` (`00-index`, `02-ambiguity-scope`, `03-docs-workflow`, `05-medallion-layers`, `06-dw-modeling`, `07-spark-databricks`, `09-dss`, `10-testing-dq`).
- **Quyết định:** bổ sung SPEC §10, cùng ngày 26/10/2026. Dòng lịch sử bị thay ngày 26/10 đánh dấu superseded. Dòng `snapshot_date` hằng số và ROLAP đánh dấu reinstated 26/10.
- **RTM:** R28 từ ☐ sang ⏸.
- **Việc tiếp theo:** Phase 3, DDL và ETL theo hợp đồng đã sửa.

### 26/10/2026 — Đơn giản hóa cách nạp
- **Đã làm:** ghi quyết định vì dataset tĩnh và ưu tiên tiến độ. Giữ star schema, `MERGE` theo grain, và DQ. Bronze và Silver là batch, FULL LOAD, OVERWRITE. Bronze thêm `_ingest_ts`, `_source_file`. Bỏ `_batch_id` và luật chọn bản giữa các lần nạp. Dedup trong file của review và geolocation giữ nguyên, cùng luật làm sạch §7. Gold là bảng Delta, `MERGE` idempotent, 7 dimension + 3 fact. `snapshot_date` = `DATE '2018-10-17'` trong config. `gold.etl_audit` còn 10 cột; cảnh báo geo, translation, conflict in ở notebook. Jobs: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly` → dss. Power BI là dashboard, Streamlit là truy vấn và DSS, OLAP là ROLAP qua SQL Warehouse. Incremental, append, CDF, Auto Loader ghi là future work (R28).
- **Không làm:** không đổi grain, measure, SCD, surrogate key. Không viết DDL, ETL, notebook, test. Không đánh dấu milestone Notion.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.7), `docs/PLAN.md`, `docs/architecture.md`, `docs/PROGRESS_LOG.md`, `README.md`, `.cursor/rules/` (`00-index`, `02-ambiguity-scope`, `05-medallion-layers`, `07-spark-databricks`, `08-sql-olap`, `09-dss`).
- **Quyết định:** SPEC §10, ngày 26/10/2026. Dòng append-only, watermark, cửa sổ review theo cột ingest, audit nhiều cột, và frontend còn mở chuyển vào lịch sử.
- **RTM:** R26 sang ☑ vì đã chọn ROLAP. R28 giữ ☐ và ghi future work. R45 giữ ☑, sửa chữ hợp đồng layer.
- **Việc tiếp theo:** Phase 3, DDL và ETL theo hợp đồng mới.

### 22/10/2026 — Phase 2 — Chiều: tie-break, seller-tháng, geolocation, category
- **Đã làm:** cửa sổ review thêm `NULLS LAST` và tie-break `_ingest_ts`, `_batch_id`. Tháng seller-tháng theo `order_purchase_timestamp`. `min_orders` mặc định 5 là tham số DSS, không lọc Gold. Geolocation một dòng mỗi prefix, fallback theo thành phố, haversine bỏ null. Category fallback `'Unknown'`. `pc_gamer` là ví dụ minh họa, chưa đo trên Volume.
- **Không làm:** không viết DDL hay ETL.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 22/10/2026 — Phase 2 — Khóa grain review và review dùng chung
- **Đã làm:** `silver.order_reviews` giữ một dòng mỗi (`review_id`, `order_id`) bằng `ROW_NUMBER`, không chỉ bỏ dòng trùng y hệt. Thêm `silver.order_reviews_dedup`, một dòng mỗi `order_id`. `fact_order` chỉ đọc bảng dedupe. Review dùng chung nhiều seller vào cùng điều kiện loại review với đơn nhiều seller. Nhánh `late_flag` của trải nghiệm xấu vẫn tính. Mẫu tỷ lệ review là số `order_id` phân biệt.
- **Quyết định trong ngày, đã ghi SPEC §10:** GMV loại đơn `canceled` và `unavailable`; `n_orders_placed` / `n_orders_valid`, `n_items_placed` / `n_items_valid`, `aov`; `seller_ship_late_flag` null khi hủy và bằng 1 khi quá hạn chưa bàn giao; `snapshot_date` = `TO_DATE(watermark_cutoff_ts)`; luật review ở mục này.
- **Không làm:** không viết DDL, ETL, notebook, test. Không sửa `TOPIC_EVALUATION.md`. Không đo số đơn có seller_set nhiều seller. Câu 1,6% tháng 3/2018 ghi là [GIẢ ĐỊNH].
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/PROGRESS_LOG.md`.
- **Việc tiếp theo:** Phase 3, DDL và ETL. Sau Gold, sensitivity check top-40 cho review dùng chung.

### 22/10/2026 — Phase 2 — Chốt snapshot, volume M1 và cờ giao trễ
- **Đã làm:** đóng ba điểm còn mở sau lần chỉnh GMV. `snapshot_date` lấy từ `watermark_cutoff_ts`; mỗi lần nạp tính lại `seller_ship_late_flag` khi cờ còn null hoặc đơn chưa có carrier. M1 dùng `n_orders_valid`. Đơn hủy ra khỏi `late_flag` và mẫu `late_delivery_*`. Thêm callout ở mục G3, không sửa câu kết quả cũ.
- **Không làm:** không viết DDL, ETL, notebook, test. Không đo lại.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`.
- **Quyết định:** SPEC §10, ngày 22/10/2026. Dòng tách `snapshot_date` khỏi watermark được đánh dấu thay thế cùng ngày.
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 22/10/2026 — Phase 2 — Bổ sung luật đơn nhiều seller, cờ trễ, SCD và địa chỉ
- **Đã làm:** đối chiếu bốn quyết định với SPEC, DESIGN, TOPIC_EVALUATION. Chỗ đã khớp thì giữ. Bổ sung chỗ còn lệch: review của đơn nhiều seller để null trên `fact_order` (không chỉ ở snapshot tháng); `seller_ship_late_flag` khi thiếu carrier sau ngày chốt và khi đơn hủy; `dim_seller` SCD2-ready; địa chỉ khách chuyển từ `dim_customer` sang `fact_order`.
- **Không làm:** không viết DDL, ETL, notebook, test. Không chạy profiling. Không đo thêm số đơn thiếu carrier hay số đơn hủy.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.6), `docs/TOPIC_EVALUATION.md`, `docs/PLAN.md` (một câu ở mục Phase 1: đơn nhiều seller để null, không xóa), `docs/PROGRESS_LOG.md`.
- **Quyết định:** ghi thêm SPEC §10. Dòng địa chỉ 15/10 đánh dấu thay thế. Dòng SCD1 15/10 giữ vì vẫn đúng. R41 vẫn là điểm cộng, chưa làm.
- **RTM:** R04, R23, R24, R29 giữ ☑ (phần thiết kế). R41 giữ ☐.
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 15/10/2026 — Phase 2 — Khóa thiết kế DW
- **Đã làm:** viết lại `docs/DESIGN.md` thành hợp đồng Phase 3. Sửa các lỗi thiết kế đã rà (cờ bàn giao có đủ 0/1/null, mốc đảo thành null kèm `raw_*` và `ts_inversion_flag`, grain review `(order_id, review_id)`, từ điển từng cột, Bronze giữ chuỗi gốc, nhãn `'Unknown'`, audit tách dedupe và reject, CHECK miền giá trị, 99.224 − 814 = 98.410, 547 là số đơn nhiều dòng review trên file thô). Khóa luật nhóm: 8 `category_group` (thêm `eletroportateis`), `size_band`, địa chỉ khách, một deal, thanh toán chính, SCD Type 1, cờ trải nghiệm xấu, so sánh ngày và timestamp, incremental theo `watermark_cutoff_ts` không sửa `order_status`.
- **Không làm:** không viết DDL, ETL, notebook, test. Không chạy profiling. Không đọc lại Volume nên không ghi số dòng IBGE mới.
- **Số giữ pending:** khóa trùng, số dòng review theo grain mới, số zip sau bbox, số seller-tháng, max của các mốc ngoài ngày mua.
- **File đã sửa:** `docs/DESIGN.md`, `docs/SPEC.md` (v0.5), `docs/PLAN.md` (10 mục Phase 2), `docs/PROGRESS_LOG.md`.
- **Quyết định:** ghi thêm ở SPEC §10. Dòng quyết định cũ giữ nguyên. R41 SCD2 vẫn là điểm cộng, chưa làm.
- **RTM:** R04, R05, R22, R23, R24, R29, R45 sang đã xong phần thiết kế. R02 và R36 giữ đang làm (DDL thuộc Phase 3; influence diagram vẫn là bản nháp).
- **Việc tiếp theo:** Phase 3, DDL và ETL.

### 15/10/2026 — Phase 1 — Ghi số đo Volume và chốt T1, X, N
- **Đã làm:** ghi kết quả `01_profiling.py` Run All trên Databricks (`SOURCE=volume`, `NOT_OFFICIAL=no`). Không viết ETL. Không upload Volume.
- **Cổng:** G1 pass 173/3.095; G2 pass 96.469/96.478; G3 pass 1.278/98.666; G4 pass 14.575/99.224; G5 pass 19/25 tháng; G6 record 380/3.095 (12,3%), `funnel_as_attribute_only=no`.
- **Quyết định nhóm:** giữ T1; trải nghiệm xấu = review ≤ 2 hoặc giao trễ hẹn; loại 1.278 đơn nhiều seller khỏi measure đó; giữ cửa sổ 2016-09-04 → 2018-10-17 (tháng thưa ghi hạn chế); X=10% GMV; N=40 seller/tháng.
- **File đã sửa:** `docs/SPEC.md` (v0.4), `docs/TOPIC_EVALUATION.md`, `docs/PLAN.md`, `docs/DESIGN.md` §7, `docs/PROGRESS_LOG.md`.
- **Còn mở:** đọc slide Ch6–7; upload IBGE vào `ref/`; S2, S3, S6; frontend OLAP; loại OLAP; thuyết trình; phân vai.
- **Việc tiếp theo:** Phase 2 thiết kế DW.

### 15/10/2026 — Phase 1 — Bỏ ngày lễ; snapshot bang → vùng IBGE
- **Đã làm:** nhóm bỏ lịch ngày lễ Brazil. Tạo `data/external/ibge_state_region.csv` từ API https://servicodados.ibge.gov.br/api/v1/localidades/estados (tải 15/10/2026). Không gọi API trong ETL. Không upload Volume. Không chạy profiling.
- **Số liệu (đếm file vừa ghi):** 27 dòng dữ liệu, 28 dòng kể header, 863 byte, 27 `state_code` phân biệt, 5 `region_name` (Norte, Nordeste, Sudeste, Sul, Centro-Oeste).
- **Lý do bỏ ngày lễ:** không có file 2016–2018 được phép đưa vào repo. `dim_date` chỉ dùng timestamp của đơn (ngày, thứ, cuối tuần).
- **File đã sửa:** `data/external/ibge_state_region.csv`, `data/README.md`, `docs/SPEC.md`, `docs/PLAN.md`, `docs/DESIGN.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`.
- **Quyết định:** ghi SPEC §10. Upload sau này vào `/Volumes/olist_catalog/bronze/raw/ref/`, không vào `funnel/` (thư mục đó chỉ có 2 CSV Marketing Funnel).
- **Việc tiếp theo:** upload file IBGE vào `ref/`, rồi Run `01_profiling.py` trên Databricks.

### 13/10/2026 — Phase 0 — S1, S4, S5 đạt
- **Đã làm:** ghi kết quả spike Cloud. Không viết ETL, không profiling.
- **S1 đạt:** catalog `olist_catalog`; schema `bronze`, `silver`, `gold`, `dss`; Volume `/Volumes/olist_catalog/bronze/raw/` với `olist/` (9 CSV) và `funnel/` (2 CSV). Dung lượng file trên Volume khớp `data/README.md` §3. `spark.read` `olist_orders_dataset.csv`: 99,441 dòng, mọi cột `string`.
- **S4 đạt:** job `s4_smoke`, compute Serverless, hai lần Run now thành công; lịch `11:04 PM` Asia/Saigon đã lưu và đang Paused. R40 chuyển ◐ vì Job ETL thật chưa gắn.
- **S5 đạt:** Git folder `olist-dw-dss`, nhánh `main`, repo `https://github.com/toann1405/olist-dw-dss.git`. Workspace thấy `README.md`, `docs/`, `src/`, `data/`.
- **File đã sửa:** `docs/PLAN.md`, `docs/SPEC.md` (v0.3), `docs/PROGRESS_LOG.md`, `README.md`, `data/README.md`, `.env.example`. `UC_CATALOG=olist_catalog` đã có trong `.env` (không commit).
- **Quyết định:** catalog và Volume khóa theo S1. Jobs và Git folder dùng được trên Free Edition. Không đổi kiến trúc SPEC §10 ngày 10/10/2026.
- **Còn mở:** S2, S3, S6; frontend OLAP; loại OLAP; AI/BI trên Free Edition.
- **Việc tiếp theo:** S2 (SQL warehouse từ Python local), rồi S3. S6 không chặn ETL Cloud.

### 13/10/2026 — Phase 0 — PLAN tách Cloud và Local
- **Đã làm:** viết lại `docs/PLAN.md` v0.3. Mỗi phase có mục **Cloud**, **Local → Cloud**, **Local**. Thứ tự hiện thực: Databricks trước; pyspark + delta-spark trên `data/sample/` (R46) làm sau khi phần Cloud tương ứng đã chạy.
- **Lý do:** nhóm cần biết việc nào làm trên workspace và việc nào làm trên máy. Không đổi kiến trúc SPEC §10, không thêm hoặc bỏ mã R-xx, không viết ETL.
- **File đã sửa:** `docs/PLAN.md`, `docs/PROGRESS_LOG.md`.
- **Quyết định:** không có quyết định kiến trúc mới. Chỉ thứ tự làm: Cloud trước, local sau.
- **Việc tiếp theo:** S1 trên Databricks (catalog, Volume, `spark.read`).

### 10/10/2026 — Phase 0 (sửa kiến trúc) — Đổi sang Databricks medallion; spike chưa bắt đầu
- **Đã làm:** cập nhật tài liệu từ stack PostgreSQL (đã khóa trong SPEC v0.1) sang medallion Databricks. Không viết ETL/DSS, không tạo file mới, không commit.
- **Lý do:** giảng viên cho phép cloud/Databricks và Power BI. Nhóm muốn lakehouse. Gold vẫn là star-schema DW (data mart Kimball bottom-up) nên vẫn đáp ứng mục tiêu 2–4 và điều kiện 3.1(a). Bỏ PostgreSQL, psycopg và schema `staging` / `dw` để không giữ hai kho. Quyết định PostgreSQL **thay thế ngày 10/10/2026** (giữ dòng cũ trong SPEC §10, không xóa).
- **File đã sửa:** `docs/SPEC.md` (v0.2), `docs/PLAN.md` (v0.2), `docs/DESIGN.md` (chỉ câu kiến trúc và nguồn DSS), `README.md`, `data/README.md`, `.env.example`, `.gitignore`, `docs/PROGRESS_LOG.md`. `docs/TOPIC_EVALUATION.md` không sửa vì không có câu nào nêu PostgreSQL, psycopg, DuckDB hay schema `staging`/`dw` là stack đã chọn.
- **Quyết định đã chốt (nhóm xác nhận 10/10/2026):** Bronze = staging (raw, append-only); Silver = làm sạch/conform; Gold = DW / data mart; `dss` = đầu ra DSS. Chỉ batch. PySpark + Spark SQL, notebook `.py`, Delta `MERGE`. DSS Python đọc chỉ từ Gold, ghi `dss.*`, huấn luyện trên Gold (lệch có chủ đích so với Silver, để đáp ứng mục tiêu 4). Audit: `gold.etl_audit`. Thêm R45 (BB\*), R46 (NC), R47 (ĐC). Đề tài T1, decision maker, alternatives, principle of choice, 3 fact, hierarchy, M1/M2 giữ nguyên.
- **[GIẢ ĐỊNH] chưa kiểm:** tên catalog và Volume (S1); Unity Catalog trên Free Edition (S1); SQL warehouse từ máy local (S2); Jobs (S4); Git folder (S5); AI/BI Dashboard trên Free Edition (quan sát lúc chốt frontend); pyspark + delta-spark local (S6).
- **Câu hỏi còn mở:**
  1. S1–S6 đạt hay không? Nếu không đạt: 2 phương án, chờ nhóm, không tự chọn.
  2. Frontend OLAP: Power BI Desktop, Databricks AI/BI Dashboard, hay Streamlit?
  3. Loại OLAP: ROLAP hay HOLAP? Chốt cùng frontend.
  4. Tên catalog Unity Catalog?
  5. Các mục Phase 1 vẫn mở: G1–G6, X, N, định nghĩa trải nghiệm xấu, thuyết trình, thành viên, ngày lễ / bảng IBGE.
- **Việc tiếp theo:** spike S1–S6 (hạn 13/10). Chưa bắt đầu.

### 10/10/2026 — Phase 0 — Finalize topic, stack, data, sample
- **Đã làm:** kiểm tra `data/raw/` đã có đủ 9 CSV Olist (nhóm tải tay) và `data/external/` đã có Marketing Funnel; chạy `python src/notebooks/00_verify_and_sample.py`; điền số liệu vào `data/README.md`; cập nhật README, SPEC, PLAN, TOPIC_EVALUATION; `git init` + 1 commit local (không push).
- **Script:** Missing/Extra vs expected = none. Integrity asserts: passed. Sample: 5,000 orders, seed 42. Thêm in nhẹ vào script có sẵn: `order_purchase_timestamp` min/max và bảng file `data/external/` (không tạo script mới).
- **Số liệu (từ output script, không profiling):**
  - orders 99,441 × 8 · items 112,650 × 7 · payments 103,886 × 5 · reviews 99,224 × 7 · customers 99,441 × 5 · sellers 3,095 × 4 · products 32,951 × 9 · geolocation 1,000,163 × 5 · translation 71 × 2
  - `order_purchase_timestamp`: min=2016-09-04 21:15:19, max=2018-10-17 17:30:18 (non-null=99,441/99,441)
  - Funnel: closed_deals 842 × 14 (0.16 MB); marketing_qualified_leads 8,000 × 4 (0.67 MB)
- **File đã sửa:** `README.md`, `data/README.md`, `docs/SPEC.md`, `docs/PLAN.md`, `docs/TOPIC_EVALUATION.md`, `docs/PROGRESS_LOG.md`, `src/notebooks/00_verify_and_sample.py`. `.gitignore` đã đúng (`docs/report/*.aux`, `dist/`, `*.egg-info/`, `*.zip`); không đổi. `data/sample/*.csv` sinh bởi script.
- **Quyết định đã chốt (nhóm xác nhận 10/10/2026):** T1 Seller Performance (có điều kiện G1–G6; dự phòng T2 cùng DW); stack PostgreSQL + Python 3.11+ (pandas, SQLAlchemy, psycopg) + Streamlit + scikit-learn/statsmodels + pytest; bottom-up data mart, fact constellation, ROLAP; Marketing Funnel dùng chắc chắn. Decision maker / quyết định / alternatives / principle of choice giữ SPEC §1.
- **Vấn đề phát sinh:** repo chưa có `.git/` khi bắt đầu phiên (PROGRESS_LOG phiên khởi tạo ghi đã `git init`) → `git init` lại rồi commit. Không tạo file tài liệu/code mới.
- **Câu hỏi còn mở (chuyển Phase 1 / nhóm tự làm):**
  1. G1–G6 đạt? Chốt cuối T1 hay chuyển T2?
  2. Giá trị X, N; định nghĩa "trải nghiệm xấu"?
  3. Thuyết trình trực tiếp hay video?
  4. Thành viên, MSSV, phân vai? (nhóm tự điền README)
  5. License ngày lễ Brazil và bảng bang→vùng IBGE?
- **Việc tiếp theo:** Phase 1 profiling + G1–G6. Nhóm tự làm: tạo GitHub và push; mỗi người cài PostgreSQL; điền bảng thành viên.

### 10/10/2026 — Phase 0 — Phiên khởi tạo
- **Đã làm:** đọc đề `CO4031_Assignment_HK261.pdf` và file phân tích; dựng repo `olist-dw-dss/` theo cấu trúc chuẩn; `git init` (nhánh `main`, chưa commit, chưa push); viết TOPIC_EVALUATION, SPEC, PLAN, DESIGN (khung), README, data/README; viết script kiểm tra + tạo mẫu.
- **Tải dữ liệu: CHƯA THÀNH CÔNG.** Kaggle CLI và `kagglehub` không có sẵn và không cài được; mọi kết nối ra ngoài lỗi phân giải tên miền (Kaggle, PyPI); không có `~/.kaggle/kaggle.json`. Không tạo dữ liệu giả. License đã đọc trực tiếp trên trang Kaggle: **CC BY-NC-SA 4.0** (cả dataset chính và Marketing Funnel).
- **Cách khắc phục cho nhóm:** làm theo `data/README.md` §2 (Kaggle CLI / kagglehub / tải bằng trình duyệt) → giải nén 9 CSV vào `data/raw/` → chạy `python src/notebooks/00_verify_and_sample.py` → dán bảng thống kê vào `data/README.md` §3.
- **File tạo:** `README.md`, `.gitignore`, `.env.example`, `docs/{TOPIC_EVALUATION,SPEC,PLAN,DESIGN,PROGRESS_LOG}.md`, `docs/assignment/*`, `data/README.md`, `src/notebooks/00_verify_and_sample.py`, `.gitkeep` ở thư mục rỗng.
- **Quyết định (đề xuất, chờ nhóm xác nhận):** đề tài **T1 – Seller Performance Management**; dự phòng T2 Delivery Promise (dùng lại cùng DW); stack PostgreSQL + Python + Streamlit + scikit-learn/statsmodels; bottom-up data mart, fact constellation, ROLAP.
- **Vấn đề phát sinh:** mục 4 (feasibility) chỉ làm được ở mức schema → "chờ dữ liệu", gom thành cổng G1–G6.
- **Câu hỏi mở:**
  1. Nhóm xác nhận T1 hay chọn T2?
  2. Thuyết trình trực tiếp hay video (đăng ký với giảng viên)?
  3. Thành viên, MSSV, phân vai?
  4. Giá trị mặc định X (% GMV bị ảnh hưởng), N (số seller xử lý/tháng), định nghĩa "trải nghiệm xấu"?
  5. Tuần 8 nhóm làm được bao nhiêu (PLAN giả định ~50%)?
  6. Dùng PostgreSQL hay DuckDB? Có cần Power BI không?
- **Việc tiếp theo:** tải dữ liệu; xác nhận đề tài/stack/vai trò; tạo repo GitHub; bắt đầu Phase 1.
