# olist-dw-dss

Course project **CO4031 – Data Warehouse and Decision Support Systems (HK261)**: a data warehouse, an OLAP dashboard, and a decision support system on the **Olist Brazilian E-Commerce** dataset (Kaggle).

**Topic:** *Seller performance management* (T1 – Olist Seller Performance DW & DSS), locked on 15/10/2026 after gates G1–G6. It helps the Seller Quality manager choose a monthly ranking and intervention policy that minimizes expected bad-experience orders within a GMV impact limit.

**Stack:** Databricks Free Edition, Delta Lake, Unity Catalog, PySpark and Spark SQL. The DSS is Python (scikit-learn / statsmodels) with a Streamlit UI. The OLAP dashboard is Power BI (ROLAP through a Databricks SQL Warehouse). Local rerun path: pyspark + delta-spark on `data/sample/`.

**Architecture:** medallion lakehouse with schemas `bronze`, `silver`, `gold`, and `dss`. Bronze and Silver are full-load overwrites. Gold is a Kimball star schema of Delta tables loaded with `MERGE`: `fact_order`, `fact_order_item`, and `fact_seller_monthly`, plus conformed dimensions. The diagram is in [docs/architecture.md](docs/architecture.md). The ERD is in [docs/DESIGN.md](docs/DESIGN.md) §4.

## Read this first
1. [README.md](README.md) (this file)
2. [docs/SPEC.md](docs/SPEC.md) — what the system is, requirement codes R-xx, architecture, DSS
3. [docs/PLAN.md](docs/PLAN.md) — phases, tasks, definition of done
4. [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md) — the first entry is the latest status
5. [docs/architecture.md](docs/architecture.md) — layer objects, load, and the job order

Also: [docs/TOPIC_EVALUATION.md](docs/TOPIC_EVALUATION.md) (why this topic) · [docs/DESIGN.md](docs/DESIGN.md) (schema, ETL mapping) · [data/README.md](data/README.md) (sources, license, download) · [docs/assignment/](docs/assignment/) (assignment PDF and analysis). Files under `docs/` stay in Vietnamese.

## Layout

```
olist-dw-dss/
├── README.md, .gitignore, .env.example
├── docs/
│   ├── assignment/        # assignment PDF and analysis
│   ├── TOPIC_EVALUATION.md, SPEC.md, PLAN.md, DESIGN.md, architecture.md, PROGRESS_LOG.md
│   └── report/            # report draft and figures
├── data/
│   ├── README.md          # sources, license, download, file notes
│   ├── raw/               # original Olist CSVs (gitignored)
│   ├── external/          # extra sources
│   └── sample/            # small key-consistent sample (committed for submission)
└── src/
    ├── sql/               # ddl/ (Delta DDL), views/, olap_queries/ (Spark SQL on Gold)
    ├── etl/               # Bronze → Silver → Gold
    ├── dss/               # models that read gold.* and write dss.*
    ├── frontend/          # Power BI dashboard; Streamlit query and DSS UI
    ├── notebooks/         # Bronze profiling; 00_verify_and_sample.py
    └── tests/             # ETL and data-quality checks
```

## How to run
1. Put the CSVs in `data/raw/` as described in [data/README.md](data/README.md), then:
   ```bash
   python src/notebooks/00_verify_and_sample.py
   ```
2. Copy `.env.example` to `.env` and fill in the Databricks variables. `DATABRICKS_TOKEN` stays empty in `.env.example`. Do not commit `.env`.
3. **Databricks:** catalog `olist_catalog`. CSVs live at `/Volumes/olist_catalog/bronze/raw/` (`olist/`, `funnel/`, `ref/`). Workspace Git folder: repo `toann1405/olist-dw-dss`, branch `main`. Bronze → Silver → Gold ETL is filled in during Phase 3.
4. **Local sample** (pyspark + delta-spark, `USE_SAMPLE=1`): filled in after spike S6.

## Status
Phase 2 (warehouse design) is locked. Next is Phase 3 (ETL). Topic T1 was locked on 15/10/2026. Spikes S1, S4, and S5 passed on Databricks Free Edition (13/10/2026). S2, S3, and S6 are still open. See [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md).
