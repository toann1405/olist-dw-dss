# PROGRESS LOG

## Hướng dẫn cho AI/người mới
1. Thứ tự đọc: `README.md` → `docs/SPEC.md` → `docs/PLAN.md` → **mục đầu tiên** của nhật ký bên dưới (mới nhất ở trên).
2. Sau **mỗi phiên làm việc**, cập nhật khối "Trạng thái hiện tại" và thêm một mục nhật ký mới **ở trên cùng**.
3. Không đổi quyết định đã chốt trong SPEC mà không ghi lý do ở đây và cập nhật SPEC §10.
4. Ghi rõ ai làm gì (phục vụ peer review — đề mục 1.3).

## Trạng thái hiện tại

| Mục | Nội dung |
|---|---|
| Phase hiện tại | Phase 0 hoàn tất (công việc repo/tài liệu/dữ liệu/sample). Việc nhóm tự làm còn lại: GitHub, PostgreSQL, điền thành viên |
| Đang làm | — |
| Blocker | Không (dữ liệu Olist + Marketing Funnel đã có; sample đã tạo) |
| Việc tiếp theo | Phase 1, chạy G1–G6 |
| Cập nhật | 10/10/2026 |

---

## Nhật ký

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
