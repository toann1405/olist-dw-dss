# olist-dw-dss

Course project **CO4031 – Data Warehouse and Decision Support Systems (HK261)**: a data warehouse, an OLAP dashboard, and a decision support system on the **Olist Brazilian E-Commerce** dataset (Kaggle).

**Topic:** *Seller performance management* (T1 – Olist Seller Performance DW & DSS), locked on 15/10/2026 after gates G1–G6. It helps the Seller Quality manager choose a monthly ranking and intervention policy that minimizes expected bad-experience orders within a GMV impact limit.

**Stack:** Databricks Free Edition, Delta Lake, Unity Catalog, PySpark and Spark SQL. The DSS is Python (scikit-learn / statsmodels) with a Streamlit UI. One local Streamlit app is the OLAP dashboard and the DSS UI. It reads `gold` and `dss` through a Databricks SQL Warehouse. Power BI is future work. Phase 3 warehouse ETL runs on Databricks only. A local rerun on `data/sample/` remains R46 (S6, Phase 6, Phase 7), not part of the Phase 3 job.

**Architecture:** medallion lakehouse with schemas `bronze`, `silver`, `gold`, and `dss`. Bronze and Silver are full-load overwrites. Gold is a Kimball star schema of Delta tables loaded with `MERGE` (`WHEN MATCHED THEN UPDATE` and `WHEN NOT MATCHED THEN INSERT` only): `fact_order`, `fact_order_item`, and `fact_seller_monthly`, plus conformed dimensions. Streamlit appends `dss.decision_log` through the SQL Warehouse. The Gold ETL job does not write that table. The diagram is in [docs/architecture.md](docs/architecture.md). The ERD is in [docs/DESIGN.md](docs/DESIGN.md) §4.

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
    ├── sql/               # views/ and olap_queries/ (Phase 4). Phase 3 DDL is in src/etl/
    ├── etl/               # Databricks notebooks: Bronze, Silver, Gold, and their DDL
    ├── dss/               # models that read gold.* and write dss.*
    ├── frontend/          # one Streamlit app: KPI, OLAP, and DSS UI
    ├── notebooks/         # Bronze profiling; 00_verify_and_sample.py
    └── tests/             # ETL and data-quality checks
```

## How to run
1. Put the CSVs in `data/raw/` as described in [data/README.md](data/README.md), then:
   ```bash
   python src/notebooks/00_verify_and_sample.py
   ```
2. Copy `.env.example` to `.env` and fill in the Databricks variables. `DATABRICKS_TOKEN` stays empty in `.env.example`. Do not commit `.env`.
3. **Databricks:** catalog `olist_catalog`. CSVs live at `/Volumes/olist_catalog/bronze/raw/` (`olist/`, `funnel/`, `ref/`). Workspace Git folder: repo `toann1405/olist-dw-dss`, branch `main`. Phase 3 ETL is Databricks-only: setup → bronze → silver → gold dims → gold facts → `fact_seller_monthly`. Create that job in the workspace UI. `src/etl/olist_etl.job.yml` is a skeleton, not a deploy file. Notebooks under `src/etl/` do not use `USE_SAMPLE`.
4. **Local sample** (pyspark + delta-spark, `USE_SAMPLE=1`): not part of Phase 3. It stays with R46 after spike S6 (Phase 6 and Phase 7).
5. **Streamlit** (local, after spike S2): `.\.venv\Scripts\python.exe -m streamlit run src\frontend\app.py`

## Status
On 10/11/2026 the UI decision changed to a single Streamlit app. Power BI is future work. S2 is still open. Phase 2 (warehouse design) is locked. The load contract of 26/10/2026 was corrected on 05/11/2026 (MERGE without delete-by-source, Streamlit-only `decision_log`, seller GMV as sum of price). Phase 3 ETL notebooks are in `src/etl/`. Table DDL lives in the notebook that owns the table. `src/etl/olist_etl.job.yml` is a skeleton, not a deploy file. The job has not been run on the workspace. Topic T1 was locked on 15/10/2026. Spikes S1, S4, and S5 passed on Databricks Free Edition (13/10/2026). S2 and S6 are still open. S3 is future work. S6 does not block Phase 3. See [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md).
