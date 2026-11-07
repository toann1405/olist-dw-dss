# Databricks notebook source
"""Bronze FULL LOAD OVERWRITE. Every business column stays STRING."""

# COMMAND ----------

# MAGIC %run ./_audit

# COMMAND ----------

# MAGIC %run ./_dq

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

# Counts already measured in DESIGN section 2.2. A mismatch is a warning, not a new measurement.
BASELINE = {
    "orders": 99441,
    "order_items": 112650,
    "order_reviews": 99224,
    "order_payments": 103886,
    "customers": 99441,
    "sellers": 3095,
    "products": 32951,
    "geolocation": 1000163,
    "category_translation": 71,
    "closed_deals": 842,
    "marketing_qualified_leads": 8000,
    "state_region": 27,
}

TABLES = [
    (
        "orders",
        "olist/olist_orders_dataset.csv",
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    ),
    (
        "order_items",
        "olist/olist_order_items_dataset.csv",
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    ),
    (
        "order_reviews",
        "olist/olist_order_reviews_dataset.csv",
        [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    ),
    (
        "order_payments",
        "olist/olist_order_payments_dataset.csv",
        [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    ),
    (
        "customers",
        "olist/olist_customers_dataset.csv",
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    ),
    (
        "sellers",
        "olist/olist_sellers_dataset.csv",
        [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
    ),
    (
        "products",
        "olist/olist_products_dataset.csv",
        [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    ),
    (
        "geolocation",
        "olist/olist_geolocation_dataset.csv",
        [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
    ),
    (
        "category_translation",
        "olist/product_category_name_translation.csv",
        ["product_category_name", "product_category_name_english"],
    ),
    (
        "closed_deals",
        "funnel/olist_closed_deals_dataset.csv",
        [
            "mql_id",
            "seller_id",
            "sdr_id",
            "sr_id",
            "won_date",
            "business_segment",
            "lead_type",
            "lead_behaviour_profile",
            "has_company",
            "has_gtin",
            "average_stock",
            "business_type",
            "declared_product_catalog_size",
            "declared_monthly_revenue",
        ],
    ),
    (
        "marketing_qualified_leads",
        "funnel/olist_marketing_qualified_leads_dataset.csv",
        ["mql_id", "first_contact_date", "landing_page_id", "origin"],
    ),
    (
        "state_region",
        "ref/ibge_state_region.csv",
        ["state_id", "state_code", "state_name", "region_id", "region_code", "region_name"],
    ),
]

# COMMAND ----------

def widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name)
    text = "" if value is None else str(value).strip()
    return text or default


def normalize_columns(df):
    for name in df.columns:
        clean = name.replace("\ufeff", "").strip().strip('"')
        if clean != name:
            df = df.withColumnRenamed(name, clean)
    return df


def read_csv(path: str):
    frame = (
        spark.read.option("header", True)
        .option("inferSchema", False)
        .option("multiLine", True)
        .option("quote", '"')
        .option("escape", '"')
        .option("encoding", "UTF-8")
        .csv(path)
    )
    frame = normalize_columns(frame)
    for name in frame.columns:
        frame = frame.withColumn(name, F.col(name).cast("string"))
    return frame

# COMMAND ----------

catalog = widget("uc_catalog", "olist_catalog")
bronze = widget("bronze_schema", "bronze")
gold = widget("gold_schema", "gold")
volume_root = widget("volume_root", "/Volumes/olist_catalog/bronze/raw").rstrip("/")
run_id = widget("run_id", "manual")

# COMMAND ----------

for table, relative_path, columns in TABLES:
    path = f"{volume_root}/{relative_path}"
    raw = read_csv(path)
    selected = []
    for column in columns:
        if column in raw.columns:
            selected.append(F.col(column).cast("string").alias(column))
        else:
            selected.append(F.lit(None).cast("string").alias(column))
    loaded = (
        raw.select(*selected)
        .withColumn("_ingest_ts", F.current_timestamp())
        .withColumn("_source_file", F.lit(path))
    )
    rows_read = loaded.count()
    target = f"{catalog}.{bronze}.{table}"
    # No NOT NULL and no CHECK on Bronze. This write is the table definition:
    # every business column is STRING, plus _ingest_ts and _source_file.
    (
        loaded.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(target)
    )
    rows_loaded = spark.table(target).count()
    print_recon(target, rows_read, rows_loaded, 0, 0)
    baseline = BASELINE[table]
    if rows_loaded != baseline:
        print_warn(f"{table}.row_count", f"loaded={rows_loaded} baseline_design_2_2={baseline}")
    append_audit(
        catalog,
        gold,
        run_id,
        "bronze",
        table,
        relative_path,
        rows_read,
        rows_loaded,
        0,
        None,
    )
