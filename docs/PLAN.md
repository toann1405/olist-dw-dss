# PLAN — Kế hoạch hiện thực

| Mục | Giá trị |
|---|---|
| Phiên bản | v0.1 — 10/10/2026 |
| Hạn nộp | **23:59 Chủ nhật 15/11/2026** (ZIP qua LMS) — mốc nội bộ: **đóng băng 14/11** |
| Thuyết trình | 19/11, 26/11, 03/12 (trực tiếp) hoặc video nộp kèm báo cáo |
| Lưu ý lịch | Tuần 8 (12–18/10) nghỉ giữa kỳ — **[GIẢ ĐỊNH] năng lực ~50%**, chỉ xếp việc nhẹ. Chương 6–8 (DSS) học tuần 9–11 → đọc trước |

Vai trò gợi ý (chờ nhóm gán tên): **A** = DW + ETL · **B** = OLAP + frontend · **C** = DSS + báo cáo. Nhóm 2 người: A gộp ETL, B gộp frontend + DSS UI, cùng làm báo cáo.

Mỗi task ghi mã yêu cầu trong SPEC §2 (R-xx).

---

## Phase 0 — Chốt phạm vi, dựng repo, tải dữ liệu, chốt công nghệ · 10/10 → 13/10
**Mục tiêu:** nền tảng sẵn sàng, dữ liệu thật trong `data/raw/`, đề tài + stack được nhóm xác nhận.
- [x] Đọc đề + file phân tích, rút ràng buộc (R01, R14, R20)
- [x] Dựng cấu trúc repo, `.gitignore`, `.env.example`, `git init` (R16)
- [x] Đánh giá đề tài sơ bộ, SPEC, PLAN, PROGRESS_LOG, README (R01, R22)
- [x] **Tải dữ liệu Olist** vào `data/raw/` (nhóm tải tay), chạy `00_verify_and_sample.py`, điền `data/README.md` (R03, R17). Marketing Funnel đã có trong `data/external/`
- [ ] Tạo repo GitHub (private khi làm, mở quyền khi nộp), push (R16) — nhóm tự làm: tạo remote rồi `git push -u origin main`
- [x] Nhóm xác nhận đề tài T1 (có điều kiện G1–G6) và stack; ghi vào README/SPEC (R01)
- [ ] Phân vai thành viên — nhóm tự làm: điền họ tên / MSSV / vai trò vào bảng README (R14)
- [ ] Mỗi người cài PostgreSQL + Python env, chạy thử kết nối (R06) — nhóm tự làm: cài PostgreSQL local hoặc Docker, copy `.env.example` → `.env`, kiểm tra kết nối
**Sản phẩm:** repo, `data/raw/`, `data/sample/`, `data/README.md` hoàn chỉnh.
**DoD:** các file CSV Olist có mặt (hoặc khác biệt đã ghi); sample tạo xong; đề tài + stack ghi trong SPEC/README. Vai trò: nhóm tự điền.
**Phụ thuộc:** tài khoản Kaggle. **Rủi ro:** không tải được → dùng trình duyệt/máy khác ngay trong ngày.

## Phase 1 — Profiling, chốt câu hỏi quyết định và KPI · 13/10 → 18/10 (tuần nghỉ)
**Mục tiêu:** xác nhận giả định dữ liệu và khóa phạm vi.
- [ ] Profiling 9 bảng: số dòng, NULL, trùng, phạm vi thời gian, phân bố (R03, R27)
- [ ] Chạy cổng G1–G6 (TOPIC_EVALUATION §1.7); nếu không đạt → quyết định chuyển T2 (R01)
- [ ] Liệt kê vấn đề chất lượng thực tế, cập nhật SPEC §3 (bỏ nhãn [GIẢ ĐỊNH]) (R27, R30)
- [ ] Tải + kiểm tra license nguồn bổ sung: Marketing Funnel, ngày lễ, bang→vùng (R30)
- [ ] Chốt định nghĩa "trải nghiệm xấu", X, N; 8–12 câu hỏi phân tích ↔ KPI (R01, R25)
- [ ] Đọc trước slide Ch6–7 (DSS, modeling) (R33, R36)
**Sản phẩm:** `src/notebooks/01_profiling.ipynb`, SPEC v0.2.
**DoD:** G1–G6 có kết quả; đề tài **chốt**; không còn [GIẢ ĐỊNH] quan trọng chưa kiểm.
**Phụ thuộc:** Phase 0. **Rủi ro:** tuần nghỉ, ít người → chỉ làm profiling, không mở rộng phạm vi.

## Phase 2 — Thiết kế DW · 17/10 → 22/10
**Mục tiêu:** thiết kế đủ để code DDL/ETL không phải đoán.
- [ ] Sơ đồ kiến trúc tổng thể + lý do bottom-up data mart (R22, R02)
- [ ] ERD fact constellation; khai báo granularity từng fact (R04, R23)
- [ ] Hierarchy cho date, địa lý khách/seller, sản phẩm (R24)
- [ ] Bus matrix, chọn surrogate key, member Unknown, SCD (R41, R04)
- [ ] Source-to-target mapping + quy tắc làm sạch/biến đổi (R05, R29, R30)
- [ ] Data dictionary; ước lượng số dòng; chọn ROLAP + materialized views (R29, R26)
- [ ] Influence diagram bản nháp để kiểm tra DW đủ biến cho DSS (R36, R10)
**Sản phẩm:** `docs/DESIGN.md` đầy đủ.
**DoD:** mọi cột fact/dim có nguồn và quy tắc; cả nhóm review.
**Phụ thuộc:** Phase 1. **Rủi ro:** thiết kế quá rộng → giới hạn 3 fact.

## Phase 3 — Database và ETL · 21/10 → 31/10
**Mục tiêu:** DW nạp đầy đủ, tái chạy được bằng một lệnh.
- [ ] DDL `staging`, `dw`, `dss` + index (R06, R42)
- [ ] Extract CSV → staging có batch_id, audit (R07, R30)
- [ ] Clean + transform theo DESIGN (R07, R27)
- [ ] Load dims (surrogate key, SCD2 `dim_seller` nếu kịp) (R07, R41)
- [ ] Load `fact_order_item`, `fact_order`, `fact_seller_monthly` (R07, R02)
- [ ] Incremental load theo watermark tháng; demo nạp thêm 1 tháng (R28)
- [ ] Test DQ (pytest): đếm dòng, đối soát Σprice, orphan FK, unique grain (R27)
- [ ] Lịch chạy (cron/Task Scheduler) — nếu kịp (R40)
**Sản phẩm:** `src/sql/ddl/`, `src/etl/`, `src/tests/`.
**DoD:** `full` load trên `raw` và `sample` đều chạy; test xanh; audit ghi số dòng từng nguồn.
**Phụ thuộc:** Phase 2. **Rủi ro:** lỗi dữ liệu bất ngờ → dồn vào bảng reject, không chặn pipeline.

## Phase 4 — OLAP và dashboard · 29/10 → 06/11
**Mục tiêu:** khám phá dữ liệu đa chiều trên DW.
- [ ] Views + materialized views tổng hợp (R08, R42)
- [ ] 5 truy vấn OLAP: slice, dice, drill-down, roll-up, pivot — mỗi truy vấn 1 câu hỏi (R25, R08)
- [ ] Streamlit: trang Tổng quan KPI, OLAP Explorer, Hồ sơ seller (R09)
- [ ] Bộ lọc tương tác + drill theo hierarchy (R09, R24)
- [ ] (ĐC) so sánh thời gian truy vấn có/không materialized view (R42)
**Sản phẩm:** `src/sql/olap_queries/`, `src/sql/views/`, `src/frontend/`.
**DoD:** demo được đủ 5 phép trên UI, kết quả đúng với truy vấn SQL kiểm tra.
**Phụ thuộc:** Phase 3 (có thể bắt đầu trên `sample`). **Rủi ro:** UI tốn thời gian → ưu tiên chức năng, không trau chuốt.

## Phase 5 — DSS · 26/10 → 08/11
**Mục tiêu:** DSS model-driven đọc từ DW, có what-if.
- [ ] View `dss.v_seller_features` chỉ đọc từ `dw` (R31, R32)
- [ ] M2 mô phỏng chính sách + what-if (làm trước, dùng p_i đơn giản) (R34, R33, R10)
- [ ] M1 logistic regression, train/test theo thời gian, metric AUC/Brier (R33, R44)
- [ ] Goal seeking θ theo ràng buộc GMV; sensitivity tornado (R35)
- [ ] UI DSS: trang Điểm rủi ro, What-if, Goal seek, Quyết định & export (R32, R34)
- [ ] Ghi `dss.seller_risk_score`, `dss.decision_log` (R31, R37)
- [ ] Influence diagram bản cuối, bảng biến, phân loại DSS, ánh xạ pha (R36, R37, R38)
- [ ] (ĐC) luật khuyến nghị hành động theo hạng (R43)
**Sản phẩm:** `src/dss/`, trang DSS trong `src/frontend/`.
**DoD:** so sánh ≥ 3 phương án (P0/P1/P2) trên UI, kết quả lấy từ DW; không có đọc CSV trong `src/dss/`.
**Phụ thuộc:** Phase 3 (fact_seller_monthly). **Rủi ro:** M1 kém → giữ baseline, nêu ở hạn chế; M2 + what-if là tối thiểu bắt buộc.

## Phase 6 — Tích hợp, kiểm thử, đánh giá · 07/11 → 10/11
**Mục tiêu:** hệ thống chạy end-to-end, có đánh giá.
- [ ] Chạy end-to-end từ DB rỗng: ETL → OLAP → DSS trên `sample` và `raw` (R07, R10)
- [ ] Backtest chính sách: áp dụng tại tháng t, so dự báo vs thực tế t+1 (R44, R11)
- [ ] Bảng đánh giá: câu hỏi/KPI ban đầu ↔ đạt/chưa đạt (R11)
- [ ] Liệt kê hạn chế (dữ liệu, mô hình, giả định e_k/r) và hướng phát triển (R12)
- [ ] Viết `README.md` mục "Cách chạy" (R16)
**Sản phẩm:** kết quả test, số liệu đánh giá, hình cho báo cáo trong `docs/report/`.
**DoD:** người ngoài nhóm chạy được theo README.
**Phụ thuộc:** Phase 4–5. **Rủi ro:** lỗi tích hợp muộn → tích hợp sớm trên `sample` từ Phase 4.

## Phase 7 — Báo cáo, slide, video, đóng gói, tập thuyết trình · 09/11 → 15/11
**Mục tiêu:** nộp đúng hạn, đủ thành phần.
- [ ] Báo cáo PDF theo mục lục đề xuất trong file phân tích, phủ L.O.1.1–4.2 (R15, R21)
- [ ] Mục phương pháp phát triển (prototyping) + rủi ro dự án (R39)
- [ ] Mục đánh giá, hạn chế, hướng phát triển (R11, R12)
- [ ] Bìa: thành viên, MSSV, vai trò, link GitHub, link video nếu có (R14, R19)
- [ ] Slide PDF; chia phần cho **mọi thành viên** (R18, R13)
- [ ] Video 10–15' nếu không thuyết trình trực tiếp; YouTube unlisted/Drive (R13, R19)
- [ ] Đóng gói ZIP: báo cáo PDF, `src/`, `data/` (sample + link full), slide PDF; kiểm tra mở được (R20, R16, R17)
- [ ] Nộp LMS **trước 14/11** (dự phòng 1 ngày); tập thuyết trình + Q&A (R20, R13)
**Sản phẩm:** `CO4031_<Nhóm>.zip`.
**DoD:** đã nộp, đã kiểm tra file trên LMS.
**Phụ thuộc:** Phase 6. **Rủi ro:** dồn việc cuối → viết báo cáo dần từ Phase 2 (`docs/report/`).

---

## Kiểm tra chéo RTM

Mọi yêu cầu mức **BB** và **BB\*** trong SPEC §2 phải xuất hiện ở ≥ 1 task phía trên.

| Mức | Mã | Có task? |
|---|---|---|
| BB [ĐỀ] | R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20 | ☑ tất cả có task |
| BB\* [SUY LUẬN] | R21, R22, R23, R24, R25, R27, R30, R31, R32, R33, R34, R36, R37, R38 | ☑ tất cả có task |

**R-xx bắt buộc chưa có task:** không có. Yêu cầu NC/ĐC chưa có task: không có. Kiểm tra lại mỗi khi sửa SPEC hoặc PLAN (đã kiểm tự động ngày 10/10/2026).
