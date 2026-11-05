# Sơ đồ kiến trúc

Quyết định 26/10/2026, sửa MERGE và `decision_log` ngày 05/11/2026. Lý do: `docs/DESIGN.md`, mục Decision update và mục Sửa hợp đồng. Grain, star schema, SCD và surrogate key không nằm trong sơ đồ này vì không đổi.

## Luồng

```mermaid
flowchart TB
  gh["GitHub<br/>toann1405/olist-dw-dss"]
  vol["Volume CSV<br/>olist / funnel / ref"]
  wh["Databricks SQL Warehouse<br/>ROLAP"]
  pbi["Power BI<br/>dashboard"]
  st["Streamlit<br/>truy van va DSS"]
  audit[(gold.etl_audit)]
  dss[(schema dss)]

  subgraph jobs [Databricks Jobs]
    direction LR
    setup[setup] ==> bronze[bronze]
    bronze ==> silver[silver]
    silver ==> dims[gold dims]
    dims ==> facts[gold facts]
    facts ==> monthly[fact_seller_monthly]
    monthly ==> dssjob[dss job]
  end

  gh -->|Git folder S5| setup
  vol --> bronze
  dims --> dssjob
  dssjob --> dss

  bronze -.-> audit
  silver -.-> audit
  dims -.-> audit
  facts -.-> audit
  monthly -.-> audit

  facts --> wh
  monthly --> wh
  dims --> wh
  dss --> wh
  wh --> pbi
  wh --> st
  st -->|append decision_log| dss
```

## Từng lớp

| Lớp | Object Type | Load | Transformations | Data Model |
|---|---|---|---|---|
| Volume | File CSV trên Unity Catalog | Upload tay. Không phải bước Job | Không đổi nội dung file | 9 CSV Olist, 2 CSV Marketing Funnel, `ibge_state_region.csv` |
| Bronze | Bảng Delta | Batch. FULL LOAD, OVERWRITE (truncate rồi insert) | Mọi cột nghiệp vụ `STRING`, as-is. Thêm `_ingest_ts`, `_source_file`. Không join, không cast nghiệp vụ | Staging. Một dòng CSV của lần nạp hiện tại. 12 bảng |
| Silver | Bảng Delta | Batch. FULL LOAD, OVERWRITE | Cast, chuẩn hóa, luật làm sạch DESIGN §7. Dedup trong file: `order_reviews` bằng `ROW_NUMBER`, `order_reviews_dedup`, `geolocation_zip` một dòng mỗi prefix. Không chọn bản giữa các lần nạp | Integration. Grain sau làm sạch, DESIGN §2.3 |
| Gold dims | Bảng Delta. 7 dimension. Không phải view | `MERGE` theo grain. Chỉ `WHEN MATCHED THEN UPDATE` và `WHEN NOT MATCHED THEN INSERT`. Không `WHEN NOT MATCHED BY SOURCE THEN DELETE` | Surrogate key. SCD Type 1. `dim_seller` SCD2-ready, vẫn một dòng mỗi `seller_id` | Star schema, dimension conformed |
| Gold facts | Bảng Delta. `fact_order`, `fact_order_item`. Không phải view | `MERGE` theo grain. Chỉ `WHEN MATCHED THEN UPDATE` và `WHEN NOT MATCHED THEN INSERT` | Measure DESIGN §3.6. `snapshot_date` = `DATE '2018-10-17'` trong config | `fact_order_item`: transaction. `fact_order`: accumulating snapshot |
| `fact_seller_monthly` | Bảng Delta. Không phải view | `MERGE` theo (`seller_key`, `month_key`), cùng hai nhánh trên, không xóa theo nguồn. Chạy sau hai fact kia | `source_name` = `gold.fact_order_item`. Tháng là tháng mua | Periodic snapshot. Một seller × một tháng có ít nhất một item |
| `dss` | Bảng Delta đầu ra mô hình. Phase 5 mới thiết kế cột | Job DSS ghi `seller_risk_score` và `policy_scenario`. Streamlit ghi `decision_log`. Job ETL Gold không ghi `decision_log` | M1, M2, what-if. Huấn luyện trên Gold | Ba tên bảng đã đặt. Cột chưa thuộc Phase 2 |
| `gold.etl_audit` | Bảng Delta | Mỗi bước ghi thêm một dòng log cho mỗi bảng đích. Không MERGE đè lịch sử | Chỉ đếm dòng. `rows_rejected` là dòng bỏ hẳn. Cảnh báo và `rows_dropped_by_dedup` in ở notebook | `audit_id`, `run_id`, `layer`, `target_table`, `source_name`, `rows_read`, `rows_loaded`, `rows_rejected`, `rows_unknown_fk`, `loaded_at` |
| SQL Warehouse | Endpoint truy vấn | Không lưu mart | SQL trên bảng Gold và `dss` | ROLAP |
| Power BI | Dashboard | Đọc. Không ghi kho | Lọc, drill, 5 phép OLAP | Đọc Gold qua SQL Warehouse |
| Streamlit | App local | Đọc Gold và `dss`. Chỉ ghi thêm `dss.decision_log` (append) | Truy vấn, what-if, goal seek, xuất quyết định | Qua SQL Warehouse. Không sở hữu schema `dss` ngoài `decision_log`. Không ghi hai bảng điểm và kịch bản. Job ETL Gold không ghi `decision_log` |
| GitHub | Repo mã nguồn | Không phải lớp dữ liệu | — | Notebook `.py`, SQL, tài liệu. Git folder Databricks đã nối (S5, nhánh `main`) |

## Legend

| Nét | Nghĩa |
|---|---|
| `==>` | Thứ tự Databricks Jobs: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly` → dss job |
| `-->` | Luồng dữ liệu: Volume → bronze, gold dims → job DSS, Gold và `dss` → SQL Warehouse → Power BI và Streamlit, Streamlit → `dss.decision_log` |
| `-.->` | Ghi `gold.etl_audit`. Một dòng mỗi bảng đích mỗi `run_id` |

Kết nối Power BI (S3) và Streamlit (S2) từ máy local tới SQL Warehouse chưa chạy. Công cụ đã chốt; hai spike chỉ kiểm kết nối.
