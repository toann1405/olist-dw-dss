# Data — Olist Brazilian E-Commerce

> **Status (10/10/2026): downloaded on 10/10/2026.** The 9 Olist CSVs are in `data/raw/` (none missing, none extra versus the expected list). Marketing Funnel is in `data/external/`. Counts below come from `python src/notebooks/00_verify_and_sample.py` on that date. Detail: `docs/PROGRESS_LOG.md`.

## 1. Sources and license

| Item | Content | Checked? |
|---|---|---|
| Main dataset | *Brazilian E-Commerce Public Dataset by Olist* — https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce | ✔ (Kaggle page read 10/10/2026); **downloaded** into `data/raw/` on 10/10/2026 |
| License | **CC BY-NC-SA 4.0** (Attribution – NonCommercial – ShareAlike) | ✔ read on the Kaggle page 10/10/2026 |
| Source description (Kaggle page) | About 100 thousand orders from 2016–2018 across marketplaces in Brazil; real anonymized commercial data; one order can have many items, and each item can be fulfilled by a different seller | ✔; script: **99,441** orders, `order_purchase_timestamp` **2016-09-04 21:15:19 → 2018-10-17 17:30:18** (99,441/99,441 non-null) |
| Extra source | *Marketing Funnel by Olist* — https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist — 2 files (`olist_closed_deals_dataset.csv`, `olist_marketing_qualified_leads_dataset.csv`), joined to the main dataset on `seller_id` | ✔ license **CC BY-NC-SA 4.0** (Kaggle page 10/10/2026); **downloaded** into `data/external/` on 10/10/2026 (842 closed deals, 8,000 MQLs — from the script) |
| Extra source (planned) | Brazilian national holidays 2016–2018 (for example the Python `holidays` package or the public Nager.Date API) | ✖ license not checked — Phase 1 |
| Extra source (planned) | State (UF) → region (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) map from IBGE — a small reference table the team will build and cite | ✖ cite the source when built in Phase 1 |

**CC BY-NC-SA 4.0 consequence (inference, not legal advice):** academic non-commercial use fits the license. When `data/sample/` is shared on GitHub or Drive, **cite Olist/Kaggle** and **keep the same license** on the shared excerpt.

## 2. How to download (manual)

**Option A — Kaggle CLI** (needs a Kaggle account):
1. Kaggle → *Settings* → *API* → *Create New Token* → save `kaggle.json` to `~/.kaggle/` (Windows: `C:\Users\<user>\.kaggle\`), or set `KAGGLE_USERNAME` / `KAGGLE_KEY` in `.env`.
2. From the repo root:
   ```bash
   pip install kaggle
   kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw --unzip
   # extra source (required for this project):
   kaggle datasets download -d olistbr/marketing-funnel-olist -p data/external --unzip
   ```

**Option B — `kagglehub`**: `pip install kagglehub` → `python -c "import kagglehub; print(kagglehub.dataset_download('olistbr/brazilian-ecommerce'))"` → copy the CSVs from the printed path into `data/raw/`.

**Option C — browser**: sign in to Kaggle → open the dataset → *Download* → extract every CSV into `data/raw/`.

**After the download**:
```bash
python src/notebooks/00_verify_and_sample.py      # print the stats table and build data/sample/
```
Paste the printed table into section 3, record the download date, and update `docs/PROGRESS_LOG.md`.

## 3. File list (script output, 10/10/2026)

Download date: **10/10/2026**. Row counts, column counts, and sizes come from `python src/notebooks/00_verify_and_sample.py` (10/10/2026).

| File (expected list) | Rows | Columns | Size | Short description (public schema — check in Phase 1) |
|---|---:|---:|---:|---|
| `olist_customers_dataset.csv` | 99,441 | 5 | 8.62 MB | Customers: `customer_id` (per order) and `customer_unique_id` (per person), zip prefix, city, state |
| `olist_geolocation_dataset.csv` | 1,000,163 | 5 | 58.44 MB | Zip prefix → lat/lng, city, state; many rows share one zip prefix |
| `olist_order_items_dataset.csv` | 112,650 | 7 | 14.72 MB | One row per item in an order; `product_id`, `seller_id`, carrier handoff deadline (`shipping_limit_date`), price, freight |
| `olist_order_payments_dataset.csv` | 103,886 | 5 | 5.51 MB | Payments per order; one order can have several rows (several methods), installments, value |
| `olist_order_reviews_dataset.csv` | 99,224 | 7 | 13.78 MB | Customer reviews: score 1–5, title/body (Portuguese), creation and answer timestamps |
| `olist_orders_dataset.csv` | 99,441 | 8 | 16.84 MB | Central table: one row per order; status and timestamps (purchase, approval, handoff to carrier, delivery to customer, estimated delivery) |
| `olist_products_dataset.csv` | 32,951 | 9 | 2.27 MB | Products: category (Portuguese), dimensions, weight, photo count, description length |
| `olist_sellers_dataset.csv` | 3,095 | 4 | 0.17 MB | Sellers: zip prefix, city, state |
| `product_category_name_translation.csv` | 71 | 2 | 0.00 MB | Portuguese → English category names |

**Difference versus the expected list:** none (script: Missing vs expected: none; Extra vs expected: none).

**Marketing Funnel** (`data/external/`, same script run):

| File | Rows | Columns | Size |
|---|---:|---:|---:|
| `olist_closed_deals_dataset.csv` | 842 | 14 | 0.16 MB |
| `olist_marketing_qualified_leads_dataset.csv` | 8,000 | 4 | 0.67 MB |

**Time span (light check, not profiling):** `order_purchase_timestamp` min=**2016-09-04 21:15:19**, max=**2018-10-17 17:30:18** (non-null=99,441/99,441).

## 4. Folders

| Folder | Contents | Commit to git? |
|---|---|---|
| `raw/` | 9 original Kaggle CSVs, original names, **do not edit by hand** | No (gitignored) |
| `external/` | Extra sources (Marketing Funnel is present; holidays and state → region: Phase 1) | Small reference files: yes; large files: no |
| `sample/` | Sample of **5,000** orders (seed **42**, script default), keys kept intact across tables, same file names as `raw/` | Yes (submission and a quick demo with `USE_SAMPLE=1`) |

The sample is built by `src/notebooks/00_verify_and_sample.py` (random orders with a fixed seed, then every related item, payment, review, customer, product, seller, and geolocation row). Run on 10/10/2026: default `--orders` 5,000, default `--seed` 42; integrity asserts passed; sample files: orders 5,000 · items 5,712 · payments 5,237 · reviews 4,980 · customers 5,000 · products 3,844 · sellers 1,222 · geolocation 481,054 · translation 71. Full dataset: add a Kaggle or Drive link here at submission time (assignment item 5.1 allows data via GitHub or Google Drive).

## 5. Unity Catalog Volume

Done in spike S1 (13/10/2026).

| Item | Value |
|---|---|
| Catalog | `olist_catalog` |
| Schemas | `bronze`, `silver`, `gold`, `dss` (`silver`, `gold`, and `dss` have no tables yet) |
| Volume | `/Volumes/olist_catalog/bronze/raw/` |
| `olist/` | 9 CSVs from `data/raw/`, original names |
| `funnel/` | `olist_closed_deals_dataset.csv`, `olist_marketing_qualified_leads_dataset.csv` |

File sizes on the Volume match section 3 (local measurement 10/10/2026). A notebook read `olist/olist_orders_dataset.csv` with `spark.read` (header, every column cast to `string`): **99,441** rows. `data/sample/` is the local rerun path (pyspark + delta-spark). It does not replace the full upload on Databricks.
