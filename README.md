# olist-dw-dss

Bài tập lớn **CO4031 – Kho dữ liệu và Hệ hỗ trợ Quyết định (HK261)**: xây dựng kho dữ liệu, OLAP dashboard và hệ hỗ trợ quyết định trên dataset **Olist Brazilian E-Commerce** (Kaggle).

**Đề tài (đã chốt có điều kiện, 10/10/2026):** *Quản lý hiệu suất người bán* (T1 – Olist Seller Performance DW & DSS) — giúp Trưởng bộ phận Quản lý chất lượng seller chọn chính sách phân hạng và can thiệp seller hằng tháng, tối thiểu số đơn trải nghiệm xấu dự kiến trong giới hạn GMV bị ảnh hưởng. Chốt cuối sau cổng G1–G6 (đầu Phase 1); nếu không đạt thì chuyển T2 Delivery Promise, dùng lại cùng DW.

**Công nghệ (đã chốt, 10/10/2026):** PostgreSQL (staging / dw / dss cùng một database, tách schema) + Python 3.11+ (pandas, SQLAlchemy, psycopg) + Streamlit + scikit-learn / statsmodels + pytest.

**Hạn nộp:** 23:59, 15/11/2026 (ZIP qua LMS).

## Thứ tự đọc tài liệu (cho người/AI mới)
1. [README.md](README.md) (file này)
2. [docs/SPEC.md](docs/SPEC.md) — dự án là gì, yêu cầu R-xx, kiến trúc, DSS
3. [docs/PLAN.md](docs/PLAN.md) — các phase, task, Definition of Done
4. [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md) — mục đầu tiên = trạng thái mới nhất

Tham khảo thêm: [docs/TOPIC_EVALUATION.md](docs/TOPIC_EVALUATION.md) (vì sao chọn đề tài) · [docs/DESIGN.md](docs/DESIGN.md) (schema, ETL mapping) · [data/README.md](data/README.md) (nguồn, license, cách tải) · [docs/assignment/](docs/assignment/) (đề gốc + phân tích đề).

## Cấu trúc thư mục

```
olist-dw-dss/
├── README.md, .gitignore, .env.example
├── docs/
│   ├── assignment/        # đề PDF + file phân tích đề
│   ├── TOPIC_EVALUATION.md, SPEC.md, PLAN.md, DESIGN.md, PROGRESS_LOG.md
│   └── report/            # nháp báo cáo + hình
├── data/
│   ├── README.md          # nguồn, license, cách tải, mô tả file
│   ├── raw/               # CSV Olist gốc (gitignore)
│   ├── external/          # nguồn bổ sung
│   └── sample/            # mẫu nhỏ giữ toàn vẹn khóa (commit để nộp)
└── src/
    ├── sql/               # ddl/, olap_queries/, views/
    ├── etl/               # pipeline staging → DW
    ├── dss/               # mô hình rủi ro, mô phỏng chính sách, what-if
    ├── frontend/          # Streamlit dashboard + DSS UI
    ├── notebooks/         # EDA, profiling; 00_verify_and_sample.py
    └── tests/             # kiểm thử ETL và chất lượng dữ liệu
```

## Cách chạy
1. Tải dữ liệu vào `data/raw/` theo [data/README.md](data/README.md), rồi:
   ```bash
   python src/notebooks/00_verify_and_sample.py
   ```
2. `cp .env.example .env` và điền thông tin PostgreSQL.
3. ETL / dashboard / DSS: _điền sau khi hiện thực (Phase 3–6)._

## Thành viên và vai trò

> Đề yêu cầu nhóm 2–3 sinh viên, **mỗi thành viên phải có vai trò rõ ràng**, và **tất cả** phải tham gia thuyết trình (mục 1.3, 4 của đề).

| Họ tên | MSSV | Vai trò | Ghi chú |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

## Trạng thái
Phase 0 — hoàn tất phần repo/tài liệu/dữ liệu/sample (10/10/2026). Đề tài T1 và stack đã chốt có điều kiện G1–G6. Việc nhóm tự làm: tạo repo GitHub, mỗi người cài PostgreSQL, điền bảng thành viên. Việc tiếp theo: Phase 1, chạy G1–G6. Xem [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md).
