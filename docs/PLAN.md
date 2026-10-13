# PLAN — Kế hoạch hiện thực

| Mục | Giá trị |
|---|---|
| Phiên bản | v0.2 — 10/10/2026 |
| Hạn nộp | **23:59 Chủ nhật 15/11/2026** (ZIP qua LMS) — mốc nội bộ: **đóng băng 14/11** |

Vai trò gợi ý (chờ nhóm gán tên): **A** = DW + ETL · **B** = OLAP + frontend · **C** = DSS + báo cáo. Nhóm 2 người: A gộp ETL, B gộp frontend + DSS UI, cùng làm báo cáo.

Mỗi task ghi mã yêu cầu trong SPEC §2 (R-xx).

---

## Phase 0 — Chốt phạm vi, dựng repo, tải dữ liệu, chốt công nghệ · 10/10 → 13/10
**Mục tiêu:** nền tảng sẵn sàng, dữ liệu thật trong `data/raw/`, đề tài đã ghi, kiến trúc medallion đã ghi trong SPEC. Spike Databricks làm trong cửa sổ này, chưa bắt đầu.
- [x] Đọc đề + file phân tích, rút ràng buộc (R01, R14, R20)
- [x] Dựng cấu trúc repo, `.gitignore`, `.env.example`, `git init` (R16)
- [x] Đánh giá đề tài sơ bộ, SPEC, PLAN, PROGRESS_LOG, README (R01, R22)
- [x] **Tải dữ liệu Olist** vào `data/raw/` (nhóm tải tay), chạy `00_verify_and_sample.py`, điền `data/README.md` (R03, R17). Marketing Funnel đã có trong `data/external/`
- [ ] Tạo repo GitHub (private khi làm, mở quyền khi nộp), push (R16) — nhóm tự làm: tạo remote rồi `git push -u origin main`
- [x] Nhóm xác nhận đề tài T1 (có điều kiện G1–G6) và stack PostgreSQL; ghi vào README/SPEC (R01) — stack này **thay thế ngày 10/10/2026**
- [x] Ghi quyết định thay kiến trúc sang Databricks medallion vào SPEC §10 và PROGRESS_LOG (R22) — 10/10/2026
- [ ] Phân vai thành viên — nhóm tự làm: điền họ tên / MSSV / vai trò vào bảng README (R14)
- [ ] Tạo tài khoản Databricks Free Edition + môi trường Python local (pyspark, delta-spark) (R06, R46) — nhóm tự làm; việc kiểm tra nằm ở spike S1–S6 bên dưới

**Spike Databricks (hạn 13/10) — chưa bắt đầu.** Mỗi spike ghi đạt/không đạt và hệ quả vào PROGRESS_LOG và SPEC §10, rồi khóa frontend OLAP và loại OLAP. **Nếu một spike không đạt, liệt kê 2 phương án và chờ nhóm — không tự chọn.**

- [ ] **S1** Tạo workspace Free Edition, catalog/schema (`bronze`, `silver`, `gold`, `dss`), upload 9 CSV + Funnel vào một Volume, thử đọc bằng `spark.read` (R06, R45). Tên catalog và đường dẫn Volume là **[GIẢ ĐỊNH]** đến khi spike này ghi lại
- [ ] **S2** Truy vấn SQL warehouse từ Python local (`databricks-sql-connector` + token) (R31, R32). Khả năng kết nối là **[GIẢ ĐỊNH]**
- [ ] **S3** Thử kết nối Power BI Desktop tới SQL warehouse. Chỉ kiểm tra kết nối, chưa làm dashboard (R09)
- [ ] **S4** Kiểm tra Databricks Jobs / lịch chạy (R40). Jobs trên Free Edition là **[GIẢ ĐỊNH]**
- [ ] **S5** Gắn Git folder với repo GitHub (R16). Git folder trên Free Edition là **[GIẢ ĐỊNH]**
- [ ] **S6** Chạy pyspark + delta-spark local trên `data/sample/` (R46)

**Sản phẩm:** repo, `data/raw/`, `data/sample/`, `data/README.md`, SPEC/PLAN v0.2. Kết quả spike ghi sau, khi chạy.
**DoD (phần tài liệu, đã xong trong phiên 10/10):** các file CSV Olist có mặt; sample tạo xong; đề tài và kiến trúc medallion ghi trong SPEC/README. Vai trò: nhóm tự điền.
**DoD (spike):** mỗi S1–S6 có trạng thái đạt/không đạt trong PROGRESS_LOG và SPEC §10; frontend OLAP và loại OLAP được khóa, hoặc được để mở kèm 2 phương án nếu spike không đạt.
**Phụ thuộc:** tài khoản Databricks Free Edition (email cá nhân). **Rủi ro:** Free Edition thiếu tính năng → dùng đường local (R46) và chờ nhóm chọn phương án.

## Phase 1 — Profiling, chốt câu hỏi quyết định và KPI · 13/10 → 18/10 (tuần nghỉ)
**Mục tiêu:** xác nhận giả định dữ liệu và khóa phạm vi.
- [ ] Profiling 9 bảng trên Bronze trong notebook Databricks (`src/notebooks/`, lưu `.py`): số dòng, NULL, trùng, phạm vi thời gian, phân bố (R03, R27)
- [ ] Chạy cổng G1–G6 (TOPIC_EVALUATION §1.7); nếu không đạt → quyết định chuyển T2 (R01)
- [ ] Liệt kê vấn đề chất lượng thực tế, cập nhật SPEC §3 (bỏ nhãn [GIẢ ĐỊNH] của dữ liệu) (R27, R30)
- [ ] Tải + kiểm tra license nguồn bổ sung: Marketing Funnel, ngày lễ, bang→vùng (R30)
- [ ] Chốt định nghĩa "trải nghiệm xấu", X, N; 8–12 câu hỏi phân tích ↔ KPI (R01, R25)
- [ ] Đọc trước slide Ch6–7 (DSS, modeling) (R33, R36)
**Sản phẩm:** `src/notebooks/01_profiling.py`, SPEC cập nhật sau profiling.
**DoD:** G1–G6 có kết quả; đề tài **chốt**; không còn [GIẢ ĐỊNH] dữ liệu quan trọng chưa kiểm. Các [GIẢ ĐỊNH] về Free Edition thuộc spike Phase 0, không đóng bằng profiling.
**Phụ thuộc:** Phase 0 (S1 để có Bronze). **Rủi ro:** tuần nghỉ, ít người → chỉ làm profiling, không mở rộng phạm vi.

## Phase 2 — Thiết kế DW · 17/10 → 22/10
**Mục tiêu:** thiết kế đủ để code DDL/ETL không phải đoán.
- [ ] Sơ đồ kiến trúc tổng thể + lý do bottom-up data mart đặt ở Gold (R22, R02)
- [ ] Liệt kê bảng Bronze và Silver; ánh xạ layer ↔ staging / integration / DW / data mart / metadata (R22, R45, R29)
- [ ] Ghi tên catalog và schema (`bronze`, `silver`, `gold`, `dss`) theo kết quả S1 (R06, R45)
- [ ] Thiết kế vật lý Delta: không partition vì ~100 nghìn đơn; nếu partition sau này thì theo cột lọc, không theo cột cardinality cao (R06, R45)
- [ ] ERD fact constellation; khai báo granularity từng fact (R04, R23)
- [ ] Hierarchy cho date, địa lý khách/seller, sản phẩm (R24)
- [ ] Bus matrix, chọn surrogate key, member Unknown, SCD (R41, R04)
- [ ] Source-to-target mapping + quy tắc làm sạch/biến đổi (R05, R29, R30)
- [ ] Data dictionary; ước lượng số dòng; ghi loại OLAP còn mở (ROLAP hoặc HOLAP) cho đến khi spike khóa (R29, R26)
- [ ] Influence diagram bản nháp để kiểm tra DW đủ biến cho DSS (R36, R10)
**Sản phẩm:** `docs/DESIGN.md` đầy đủ.
**DoD:** mọi cột fact/dim có nguồn và quy tắc; hợp đồng layer (R45) ghi trong DESIGN; cả nhóm review.
**Phụ thuộc:** Phase 1. **Rủi ro:** thiết kế quá rộng → giới hạn 3 fact.

## Phase 3 — Database và ETL · 21/10 → 31/10
**Mục tiêu:** Gold nạp đầy đủ, tái chạy được trên Databricks và trên sample local.
- [ ] DDL Delta cho schema `bronze`, `silver`, `gold`, `dss`, gồm `gold.etl_audit`; comment bảng/cột Gold trên Unity Catalog (R06, R42, R47)
- [ ] Bronze: đọc CSV (id/zip dạng chuỗi) từ Volume, append, thêm `_ingest_ts`, `_source_file`, `_batch_id` (R07, R30, R45)
- [ ] Silver: cast kiểu, dedupe (geolocation, review), chuẩn hóa thành phố, dịch category, map state → region (R07, R27, R45)
- [ ] Gold: tra surrogate key, member `-1`, nạp 3 fact bằng Delta `MERGE`; SCD2 `gold.dim_seller` nếu làm điểm cộng (R07, R02, R41)
- [ ] Incremental theo watermark `order_purchase_timestamp`; demo nạp thêm 1 tháng (R28)
- [ ] DQ: Delta constraints (`NOT NULL`, `CHECK`) + đối soát đếm dòng/tổng + pytest local trên `data/sample/` (R27, R46)
- [ ] Databricks Jobs — chỉ nếu S4 đạt (R40). Nếu S4 không đạt: ghi 2 phương án, chờ nhóm, không tự chọn
**Sản phẩm:** `src/sql/ddl/`, `src/etl/`, `src/tests/`.
**DoD:** load trên Databricks và load local trên sample đều chạy; test xanh; `gold.etl_audit` ghi số dòng từng nguồn.
**Phụ thuộc:** Phase 2 và S1, S6. **Rủi ro:** lỗi dữ liệu bất ngờ → dồn vào bảng reject, không chặn pipeline.

## Phase 4 — OLAP và dashboard · 29/10 → 06/11
**Mục tiêu:** khám phá dữ liệu đa chiều trên Gold.
- [ ] View phục vụ OLAP trên Gold (R08, R42)
- [ ] 5 truy vấn OLAP bằng Spark SQL trên Gold: slice, dice, drill-down, roll-up, pivot — mỗi truy vấn 1 câu hỏi (R25, R08)
- [ ] Frontend OLAP theo kết quả spike (Power BI Desktop / Databricks AI/BI Dashboard / Streamlit). Không chọn công cụ trước khi spike khóa quyết định (R09, R26)
- [ ] Bộ lọc tương tác + drill theo hierarchy (R09, R24)
- [ ] (ĐC) so sánh thời gian truy vấn có/không aggregate view (R42)
**Sản phẩm:** `src/sql/olap_queries/`, `src/sql/views/`, `src/frontend/`.
**DoD:** demo được đủ 5 phép; kết quả khớp Spark SQL trên Gold; công cụ đúng quyết định đã khóa sau spike.
**Phụ thuộc:** Phase 3 (có thể bắt đầu trên `sample`). **Rủi ro:** UI tốn thời gian → ưu tiên chức năng, không trau chuốt. Nếu S3 không đạt, dừng ở 2 phương án và chờ nhóm.

## Phase 5 — DSS · 26/10 → 08/11
**Mục tiêu:** DSS model-driven đọc từ Gold, ghi `dss.*`, có what-if.
- [ ] Feature view (ví dụ `dss.v_seller_features`) chỉ trên `gold.*` (R31, R32)
- [ ] M2 mô phỏng chính sách + what-if (làm trước, dùng p_i đơn giản) (R34, R33, R10)
- [ ] M1 logistic regression, train/test theo thời gian, metric AUC/Brier; huấn luyện trên Gold, không trên Silver (R33, R44)
- [ ] Goal seeking θ theo ràng buộc GMV; sensitivity tornado (R35)
- [ ] UI DSS: trang Điểm rủi ro, What-if, Goal seek, Quyết định & export. Streamlit local đọc Gold qua SQL warehouse nếu S2 đạt (R32, R34)
- [ ] Ghi `dss.seller_risk_score`, `dss.decision_log` (R31, R37)
- [ ] Influence diagram bản cuối, bảng biến, phân loại DSS, ánh xạ pha (R36, R37, R38)
- [ ] (ĐC) luật khuyến nghị hành động theo hạng (R43)
**Sản phẩm:** `src/dss/`, trang DSS trong `src/frontend/`.
**DoD:** so sánh ≥ 3 phương án (P0/P1/P2) trên UI, kết quả lấy từ Gold; không có `read_csv` / đường dẫn `data/raw` trong `src/dss/`.
**Phụ thuộc:** Phase 3 (`gold.fact_seller_monthly`) và S2. **Rủi ro:** M1 kém → giữ baseline, nêu ở hạn chế; M2 + what-if là tối thiểu bắt buộc. Nếu S2 không đạt: ghi 2 phương án, chờ nhóm.

## Phase 6 — Tích hợp, kiểm thử, đánh giá · 07/11 → 10/11
**Mục tiêu:** hệ thống chạy end-to-end trên Databricks và trên sample local, có đánh giá.
- [ ] Chạy end-to-end trên Databricks: Bronze → Silver → Gold → OLAP → DSS (R07, R10)
- [ ] Chạy đường local trên `data/sample/` bằng pyspark + delta-spark (R46)
- [ ] Lưu screenshot và output làm bằng chứng (phòng mất tài khoản hoặc người chấm không vào được workspace) (R46)
- [ ] Backtest chính sách: áp dụng tại tháng t, so dự báo vs thực tế t+1 (R44, R11)
- [ ] Bảng đánh giá: câu hỏi/KPI ban đầu ↔ đạt/chưa đạt (R11)
- [ ] Liệt kê hạn chế (dữ liệu, mô hình, giả định e_k/r, giới hạn Free Edition) và hướng phát triển (streaming, CDC, Kafka, Lakehouse Federation, Reverse ETL) (R12)
- [ ] Viết `README.md` mục "Cách chạy" cho cả hai đường (R16, R46)
**Sản phẩm:** kết quả test, số liệu đánh giá, hình cho báo cáo trong `docs/report/`.
**DoD:** người ngoài nhóm chạy được đường local trên sample theo README; đường Databricks có hướng dẫn và bằng chứng đã chạy.
**Phụ thuộc:** Phase 4–5. **Rủi ro:** lỗi tích hợp muộn → tích hợp sớm trên `sample` từ Phase 4.

## Phase 7 — Báo cáo, slide, video, đóng gói, tập thuyết trình · 09/11 → 15/11
**Mục tiêu:** nộp đúng hạn, đủ thành phần.
- [ ] Báo cáo PDF theo mục lục đề xuất trong file phân tích, phủ L.O.1.1–4.2 (R15, R21)
- [ ] Mục phương pháp phát triển (prototyping) + rủi ro dự án (R39)
- [ ] Mục đánh giá, hạn chế, hướng phát triển (R11, R12)
- [ ] Bìa: thành viên, MSSV, vai trò, link GitHub, link video nếu có (R14, R19)
- [ ] Slide PDF; chia phần cho **mọi thành viên** (R18, R13)
- [ ] Video 10–15' nếu không thuyết trình trực tiếp; YouTube unlisted/Drive (R13, R19)
- [ ] Đóng gói ZIP: báo cáo PDF, `src/` (notebook dạng `.py`), `data/` (sample + link full), slide PDF; README hướng dẫn người chấm chạy local trên sample (R20, R16, R17, R46)
- [ ] Nộp LMS **trước 14/11** (dự phòng 1 ngày); tập thuyết trình + Q&A (R20, R13)
**Sản phẩm:** `CO4031_<Nhóm>.zip`.
**DoD:** đã nộp, đã kiểm tra file trên LMS; người chấm có hướng dẫn chạy lại.
**Phụ thuộc:** Phase 6. **Rủi ro:** dồn việc cuối → viết báo cáo dần từ Phase 2 (`docs/report/`).

---

## Kiểm tra chéo RTM

Mọi yêu cầu mức **BB** và **BB\*** trong SPEC §2 phải xuất hiện ở ≥ 1 task phía trên.

| Mức | Mã | Có task? |
|---|---|---|
| BB [ĐỀ] | R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20 | ☑ tất cả có task |
| BB\* [SUY LUẬN] | R21, R22, R23, R24, R25, R27, R30, R31, R32, R33, R34, R36, R37, R38, R45 | ☑ tất cả có task |
| NC | R26, R28, R29, R39, R42, R44, R46 | ☑ tất cả có task (R46: S6, Phase 3, Phase 6, Phase 7) |
| ĐC | R35, R40, R41, R43, R47 | ☑ tất cả có task (R47: comment bảng/cột Gold ở Phase 3) |

**R-xx bắt buộc chưa có task:** không có. Yêu cầu NC/ĐC chưa có task: không có. Kiểm tra lại mỗi khi sửa SPEC hoặc PLAN (đã kiểm khi chuyển kiến trúc, 10/10/2026).
