# PLAN — Kế hoạch hiện thực

| Mục | Giá trị |
|---|---|
| Phiên bản | v0.4 — 26/10/2026 |
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

Trong mỗi phase, làm hết mục **Cloud** trước, rồi **Local → Cloud**, rồi **Local**.

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
- [x] Chốt định nghĩa "trải nghiệm xấu", X, N; 8–12 câu hỏi phân tích ↔ KPI (R01, R25). Review ≤ 2 hoặc giao trễ hẹn; đơn nhiều seller để null, không xóa; X=10; N=40; 10 câu hỏi trong SPEC
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

## Phase 3 — Database và ETL · 21/10 → 31/10

**Mục tiêu:** Gold nạp đầy đủ trên Databricks trước. Cùng mã đó chạy lại trên sample local chỉ sau khi load Cloud đã chạy.

**Cloud** (làm trước)

- [ ] DDL Delta cho schema `bronze`, `silver`, `gold`, `dss`, gồm `gold.etl_audit`; comment bảng/cột Gold trên Unity Catalog (R06, R42, R47)
- [ ] Bronze: đọc CSV (id/zip dạng chuỗi) từ Volume, FULL LOAD OVERWRITE, mọi cột STRING as-is, thêm `_ingest_ts`, `_source_file` (R07, R30, R45)
- [ ] Silver: FULL LOAD OVERWRITE; cast kiểu, dedupe trong file (geolocation, review), chuẩn hóa thành phố, dịch category, map state → region (R07, R27, R45)
- [ ] Gold: bảng Delta; tra surrogate key, member `-1`, `MERGE` 7 dimension và 3 fact theo grain; SCD2 `gold.dim_seller` nếu làm điểm cộng (R07, R02, R41)
- Future work (R28), không làm trong Phase 3: incremental theo watermark, append, CDF, Auto Loader
- [ ] Delta constraints (`NOT NULL`, `CHECK`) trên Gold; `gold.etl_audit` ghi số dòng từng nguồn theo 10 cột ở SPEC §6. Cảnh báo geo, translation, conflict in ở notebook (R27)
- [ ] Databricks Jobs, S4 đã đạt: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly` → dss (R40)

**Local** (sau khi load Cloud chạy được; R46)

- [ ] Chạy lại pipeline với `USE_SAMPLE=1` trên `data/sample/` bằng pyspark + delta-spark (R46)
- [ ] pytest trên sample: đối soát đếm dòng/tổng, orphan FK, unique grain (R27, R46)

**Sản phẩm:** `src/sql/ddl/`, `src/etl/`, `src/tests/`.
**DoD:** load Cloud chạy và `gold.etl_audit` có số dòng; load local + pytest là bước sau, không thay DoD Cloud.
**Phụ thuộc:** Phase 2 và S1. S6 nên đạt trước bước Local. **Rủi ro:** lỗi dữ liệu → set null, đếm `rows_rejected` khi dòng bị bỏ hẳn, in DQ trong notebook. Không chặn pipeline Cloud.

## Phase 4 — OLAP và dashboard · 29/10 → 06/11

**Mục tiêu:** 5 phép OLAP trên **Gold trong Databricks** trước. Frontend gắn vào Gold đó; không dựng OLAP trên sample local trước.

**Cloud**

- [ ] View phục vụ OLAP trên Gold, nếu làm R42. Fact và dimension vẫn là bảng Delta (R08, R42)
- [ ] 5 truy vấn OLAP bằng Spark SQL trên Gold: slice, dice, drill-down, roll-up, pivot — mỗi truy vấn 1 câu hỏi (R25, R08)
- [ ] (ĐC) so sánh thời gian truy vấn có/không aggregate view, đo trên SQL warehouse (R42)

**Local → Cloud**

- [ ] Power BI Desktop: dashboard ROLAP, đọc Gold qua SQL Warehouse. Kết nối kiểm ở S3 (R09, R26)
- [ ] Bộ lọc tương tác + drill theo hierarchy trên Power BI (R09, R24)

**Sản phẩm:** `src/sql/olap_queries/`, `src/sql/views/`, dashboard Power BI.
**DoD:** demo đủ 5 phép trên Gold Cloud; kết quả khớp Spark SQL. Công cụ đã chốt 26/10/2026: Power BI cho dashboard, ROLAP qua SQL Warehouse. Streamlit thuộc Phase 5 (truy vấn và DSS).
**Phụ thuộc:** Phase 3 Cloud (Gold đã có dữ liệu). **Rủi ro:** UI tốn thời gian → ưu tiên 5 câu SQL trên Cloud. Nếu S3 không đạt, dừng ở 2 phương án và chờ nhóm.

## Phase 5 — DSS · 26/10 → 08/11

**Mục tiêu:** mô hình đọc Gold trên Databricks, ghi `dss.*` trên workspace trước. UI local chỉ là lớp gọi warehouse.

**Cloud**

- [ ] Feature view (ví dụ `dss.v_seller_features`) chỉ trên `gold.*` (R31, R32)
- [ ] M2 mô phỏng chính sách + what-if trên dữ liệu Gold (làm trước, dùng p_i đơn giản) (R34, R33, R10)
- [ ] M1 logistic regression, train/test theo thời gian, metric AUC/Brier; huấn luyện trên Gold, không trên Silver (R33, R44)
- [ ] Goal seeking θ theo ràng buộc GMV; sensitivity tornado (R35)
- [ ] Job DSS ghi `dss.seller_risk_score` và `dss.policy_scenario` trên workspace. Streamlit ghi thêm `dss.decision_log` qua SQL Warehouse (R31, R37)

**Local → Cloud** (sau khi bảng `dss.*` đã có trên Cloud và S2 đạt)

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

Mọi yêu cầu mức **BB** và **BB\*** trong SPEC §2 phải xuất hiện ở ≥ 1 task phía trên.

| Mức | Mã | Có task? |
|---|---|---|
| BB [ĐỀ] | R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20 | ☑ tất cả có task |
| BB\* [SUY LUẬN] | R21, R22, R23, R24, R25, R27, R30, R31, R32, R33, R34, R36, R37, R38, R45 | ☑ tất cả có task |
| NC | R26, R28, R29, R39, R42, R44, R46 | ☑ tất cả có task (R28: ⏸ deferred / future work, không hiện thực trước hạn nộp. R46: S6, Phase 3 Local, Phase 6 Local, Phase 7) |
| ĐC | R35, R40, R41, R43, R47 | ☑ tất cả có task (R47: comment bảng/cột Gold ở Phase 3 Cloud) |

**R-xx bắt buộc chưa có task:** không có. Yêu cầu NC/ĐC chưa có task: không có. Kiểm tra lại mỗi khi sửa SPEC hoặc PLAN (13/10/2026: tách Cloud / Local, không thêm hoặc bỏ R-xx).
