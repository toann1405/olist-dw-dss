# PROGRESS LOG

## Hướng dẫn cho AI/người mới
1. Thứ tự đọc: `README.md` → `docs/SPEC.md` → `docs/PLAN.md` → **mục đầu tiên** của nhật ký bên dưới (mới nhất ở trên).
2. Sau **mỗi phiên làm việc**, cập nhật khối "Trạng thái hiện tại" và thêm một mục nhật ký mới **ở trên cùng**.
3. Không đổi quyết định đã chốt trong SPEC mà không ghi lý do ở đây và cập nhật SPEC §10.
4. Ghi rõ ai làm gì (phục vụ peer review — đề mục 1.3).

## Trạng thái hiện tại

| Mục | Nội dung |
|---|---|
| Phase hiện tại | Phase 2 thiết kế đã khóa (15/10/2026). T1, X=10, N=40 giữ nguyên. Việc tiếp theo là Phase 3 |
| Đang làm | — |
| Blocker | Không có blocker thiết kế. SQL warehouse từ máy local (S2) và Power BI (S3) chưa kiểm. File IBGE đã được nhóm xác nhận trên Volume `ref/`; phiên này không đọc lại Volume |
| Việc tiếp theo | Phase 3: DDL Delta và ETL Bronze → Silver → Gold theo `docs/DESIGN.md` |
| Cập nhật | 15/10/2026 |

---

## Nhật ký

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
