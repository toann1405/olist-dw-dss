# olist-dw-dss

Bài tập lớn **CO4031 – Kho dữ liệu và Hệ hỗ trợ Quyết định (HK261)**: xây dựng kho dữ liệu, OLAP dashboard và hệ hỗ trợ quyết định trên dataset **Olist Brazilian E-Commerce** (Kaggle).

**Đề tài:** *Quản lý hiệu suất người bán* (T1 – Olist Seller Performance DW & DSS) — giúp Trưởng bộ phận Quản lý chất lượng seller chọn chính sách phân hạng và can thiệp seller hằng tháng, tối thiểu số đơn trải nghiệm xấu dự kiến trong giới hạn GMV bị ảnh hưởng. Chốt cuối sau cổng G1–G6 (đầu Phase 1); nếu không đạt thì chuyển T2 Delivery Promise, dùng lại cùng DW.

**Công nghệ:** Databricks Free Edition, Delta Lake, Unity Catalog (schema `bronze` / `silver` / `gold` / `dss`), PySpark + Spark SQL; DSS bằng Python (scikit-learn / statsmodels), đọc Gold và ghi `dss.*`. Frontend OLAP chờ spike (Power BI Desktop / Databricks AI/BI Dashboard / Streamlit). Đường tái lập local: pyspark + delta-spark trên `data/sample/`.


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
    ├── sql/               # ddl/ (Delta DDL), views/, olap_queries/ (Spark SQL trên Gold)
    ├── etl/               # pipeline Bronze → Silver → Gold
    ├── dss/               # mô hình đọc gold.*, ghi dss.*
    ├── frontend/          # OLAP chờ spike; DSS UI dự kiến Streamlit local
    ├── notebooks/         # profiling trên Bronze; 00_verify_and_sample.py
    └── tests/             # kiểm thử ETL và chất lượng dữ liệu
```

## Cách chạy
1. Tải dữ liệu vào `data/raw/` theo [data/README.md](data/README.md), rồi:
   ```bash
   python src/notebooks/00_verify_and_sample.py
   ```
2. `cp .env.example .env` và điền biến Databricks. `DATABRICKS_TOKEN` để trống trong `.env.example`.

## Trạng thái
Phase 0 — S1, S4, S5 đạt trên Databricks Free Edition (13/10/2026). Còn S2, S3, S6. Đề tài T1 vẫn chốt có điều kiện G1–G6. Xem [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md).
