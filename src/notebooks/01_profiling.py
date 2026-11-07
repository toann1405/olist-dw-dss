# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
"""Phase 1 read-only profiling of the Olist CSVs.

Official numbers come from a Databricks Run All with SOURCE=volume.
A local smoke sets USE_LOCAL_RAW=1, reads data/raw plus data/external, and
prints NOT OFFICIAL. It does not read data/sample/.

This file does not write Delta tables, MERGE, or CSV files.

Databricks widgets (defaults):
  VOLUME_ROOT=/Volumes/olist_catalog/bronze/raw
  USE_LOCAL_RAW=0

Local smoke (PowerShell):
  $env:USE_LOCAL_RAW='1'
  python src/notebooks/01_profiling.py
"""

# COMMAND ----------

from __future__ import annotations

import os
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

# COMMAND ----------

OLIST_FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

CLOSED_DEALS_FILE = "olist_closed_deals_dataset.csv"

BUSINESS_KEYS = {
    "olist_customers_dataset.csv": ["customer_id"],
    "olist_geolocation_dataset.csv": [],
    "olist_order_items_dataset.csv": ["order_id", "order_item_id"],
    "olist_order_payments_dataset.csv": ["order_id", "payment_sequential"],
    "olist_order_reviews_dataset.csv": ["review_id"],
    "olist_orders_dataset.csv": ["order_id"],
    "olist_products_dataset.csv": ["product_id"],
    "olist_sellers_dataset.csv": ["seller_id"],
    "product_category_name_translation.csv": ["product_category_name"],
}

TIMESTAMP_COLUMNS = {
    "olist_orders_dataset.csv": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items_dataset.csv": ["shipping_limit_date"],
    "olist_order_reviews_dataset.csv": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}

TS_FMT = "yyyy-MM-dd HH:mm:ss"

# translate() needs equal-length strings. Lowercase the city first.
ACCENT_FROM = "áàâãäåéèêëíìîïóòôõöúùûüçñ"
ACCENT_TO = "aaaaaaeeeeiiiiooooouuuucn"

# Approximate filter for SPEC §3, not a legal border.
BRAZIL_LAT_MIN = -34.0
BRAZIL_LAT_MAX = 6.0
BRAZIL_LNG_MIN = -74.0
BRAZIL_LNG_MAX = -28.0

DEFAULT_VOLUME_ROOT = "/Volumes/olist_catalog/bronze/raw"

# Thresholds from docs/TOPIC_EVALUATION.md §1.7.
G1_MIN_ITEMS = 10
G1_MIN_MONTHS = 6
G1_MIN_SELLERS = 150
G2_MIN_RATE = 0.95
G3_MAX_RATE = 0.05
G4_MIN_RATE = 0.05
G4_MAX_RATE = 0.25
G5_MIN_ORDERS = 1000
G5_MIN_MONTHS = 15
G6_ATTRIBUTE_RATE = 0.10

# COMMAND ----------


def get_spark() -> SparkSession:
    existing = globals().get("spark")
    if isinstance(existing, SparkSession):
        return existing
    active = SparkSession.getActiveSession()
    if active is not None:
        return active
    return (
        SparkSession.builder.master("local[*]")
        .appName("phase1-profiling")
        .getOrCreate()
    )


def widget_or_env(name: str, default: str) -> str:
    dbutils = globals().get("dbutils")
    if dbutils is not None:
        try:
            dbutils.widgets.text(name, default)
            value = dbutils.widgets.get(name)
            if value is not None and str(value).strip() != "":
                return str(value).strip()
        except Exception:
            pass
    env_value = os.environ.get(name)
    if env_value is not None and env_value.strip() != "":
        return env_value.strip()
    return default


def repo_root() -> Path:
    try:
        return Path(__file__).resolve().parents[2]
    except NameError:
        return Path.cwd()


def resolve_source() -> dict[str, str | bool]:
    use_local = widget_or_env("USE_LOCAL_RAW", "0") == "1"
    volume_root = widget_or_env("VOLUME_ROOT", DEFAULT_VOLUME_ROOT).rstrip("/")
    if use_local:
        root = repo_root()
        return {
            "source": "local_raw",
            "not_official": True,
            "olist_dir": (root / "data" / "raw").as_posix(),
            "funnel_dir": (root / "data" / "external").as_posix(),
            "volume_root": "",
        }
    return {
        "source": "volume",
        "not_official": False,
        "olist_dir": f"{volume_root}/olist",
        "funnel_dir": f"{volume_root}/funnel",
        "volume_root": volume_root,
    }


def blank_col(column: F.Column) -> F.Column:
    text = F.trim(column.cast("string"))
    return F.when(text.isNull() | (text == ""), F.lit(None).cast("string")).otherwise(text)


def blank(name: str) -> F.Column:
    return blank_col(F.col(name))


def parsed_ts(name: str) -> F.Column:
    return F.to_timestamp(blank(name), TS_FMT)


def fold_city(name: str) -> F.Column:
    return F.translate(F.lower(blank(name)), ACCENT_FROM, ACCENT_TO)


def normalize_columns(df: DataFrame) -> DataFrame:
    for name in df.columns:
        clean = name.replace("\ufeff", "").strip().strip('"')
        if clean != name:
            df = df.withColumnRenamed(name, clean)
    return df


def read_csv(spark: SparkSession, path: str) -> DataFrame:
    try:
        frame = (
            spark.read.option("header", True)
            .option("inferSchema", False)
            .option("multiLine", True)
            .option("quote", '"')
            .option("escape", '"')
            .option("encoding", "UTF-8")
            .csv(path)
        )
    except Exception as exc:
        raise RuntimeError(f"Cannot read CSV: {path}") from exc
    frame = normalize_columns(frame)
    for name in frame.columns:
        frame = frame.withColumn(name, F.col(name).cast("string"))
    return frame


def require_columns(df: DataFrame, path: str, columns: list[str]) -> None:
    missing = [name for name in columns if name not in df.columns]
    if missing:
        raise RuntimeError(
            f"Missing columns {missing} in {path}. Found: {df.columns}"
        )


def fmt(value: object) -> str:
    if value is None:
        return "na"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def one(df: DataFrame, column: F.Column) -> object:
    return df.select(column.alias("value")).collect()[0]["value"]


def count_if(df: DataFrame, condition: F.Column) -> int:
    value = one(df, F.sum(F.when(condition, 1).otherwise(0)))
    return int(value or 0)


def distinct_values(df: DataFrame, column: F.Column) -> int:
    return df.select(column.alias("value")).where(F.col("value").isNotNull()).distinct().count()


# COMMAND ----------


def duplicate_stats(df: DataFrame, keys: list[str]) -> tuple[str, str]:
    if not keys:
        return "na", "na"
    if any(key not in df.columns for key in keys):
        return "na", "na"
    grouped = df.groupBy(*[blank(key).alias(key) for key in keys]).count()
    duplicated = grouped.where(F.col("count") > 1)
    groups = duplicated.count()
    extra = duplicated.agg(F.sum(F.col("count") - 1).alias("extra")).collect()[0]["extra"]
    return str(groups), str(int(extra or 0))


def null_counts(df: DataFrame, row_count: int) -> list[tuple[str, int, str]]:
    if row_count == 0:
        return [(name, 0, "na") for name in df.columns]
    expressions = [
        F.sum(F.when(blank(name).isNull(), 1).otherwise(0)).alias(name)
        for name in df.columns
    ]
    row = df.agg(*expressions).collect()[0]
    result = []
    for name in df.columns:
        null_rows = int(row[name] or 0)
        result.append((name, null_rows, fmt(rate(null_rows, row_count))))
    return result


def timestamp_stats(df: DataFrame, columns: list[str]) -> list[dict[str, object]]:
    present = [name for name in columns if name in df.columns]
    if not present:
        return []
    expressions = []
    for name in present:
        parsed = parsed_ts(name)
        raw = blank(name)
        expressions.extend(
            [
                F.min(parsed).alias(f"{name}__min"),
                F.max(parsed).alias(f"{name}__max"),
                F.sum(F.when(raw.isNull(), 1).otherwise(0)).alias(f"{name}__null"),
                F.sum(F.when(raw.isNotNull() & parsed.isNull(), 1).otherwise(0)).alias(
                    f"{name}__bad"
                ),
            ]
        )
    row = df.agg(*expressions).collect()[0]
    stats = []
    for name in present:
        stats.append(
            {
                "column": name,
                "min": row[f"{name}__min"],
                "max": row[f"{name}__max"],
                "null_rows": int(row[f"{name}__null"] or 0),
                "unparseable": int(row[f"{name}__bad"] or 0),
            }
        )
    return stats


def print_file_profile(
    name: str,
    row_count: int,
    column_count: int,
    dup_groups: str,
    extra_rows: str,
    nulls: list[tuple[str, int, str]],
    timestamps: list[dict[str, object]],
    keys: list[str],
) -> None:
    key_label = ", ".join(keys) if keys else "none (no single-row business key)"
    print(f"\n## `{name}`")
    print(f"rows: {row_count}")
    print(f"columns: {column_count}")
    print(f"business key: {key_label}")
    print(f"duplicate key groups: {dup_groups}")
    print(f"extra duplicate rows: {extra_rows}")
    print("\n| column | null_rows | null_rate |")
    print("|---|---:|---:|")
    for column, null_rows, null_rate in nulls:
        print(f"| `{column}` | {null_rows} | {null_rate} |")
    if timestamps:
        print("\n| timestamp | min | max | null_rows | unparseable |")
        print("|---|---|---|---:|---:|")
        for item in timestamps:
            print(
                f"| `{item['column']}` | {fmt(item['min'])} | {fmt(item['max'])} | "
                f"{item['null_rows']} | {item['unparseable']} |"
            )


def remember_profile(result: list[str], name: str, row_count: int, column_count: int, dup_groups: str, extra_rows: str, nulls: list[tuple[str, int, str]], timestamps: list[dict[str, object]]) -> None:
    result.append(f"file.{name}.rows={row_count}")
    result.append(f"file.{name}.cols={column_count}")
    result.append(f"file.{name}.dup_key_groups={dup_groups}")
    result.append(f"file.{name}.extra_dup_rows={extra_rows}")
    for column, null_rows, null_rate in nulls:
        if null_rows > 0:
            result.append(f"null.{name}.{column}={null_rows}/{row_count} rate={null_rate}")
    for item in timestamps:
        result.append(f"ts.{name}.{item['column']}.min={fmt(item['min'])}")
        result.append(f"ts.{name}.{item['column']}.max={fmt(item['max'])}")
        result.append(f"ts.{name}.{item['column']}.null={item['null_rows']}")
        result.append(f"ts.{name}.{item['column']}.unparseable={item['unparseable']}")


# COMMAND ----------


def inversion_count(df: DataFrame, earlier: str, later: str) -> int:
    earlier_ts = parsed_ts(earlier)
    later_ts = parsed_ts(later)
    return count_if(df, earlier_ts.isNotNull() & later_ts.isNotNull() & (later_ts < earlier_ts))


def city_fold_stats(df: DataFrame, column: str) -> tuple[int, int, int]:
    lowered = F.lower(blank(column))
    folded = fold_city(column)
    distinct_lower = distinct_values(df, lowered)
    distinct_folded = distinct_values(df, folded)
    accent_rows = count_if(df, lowered.isNotNull() & (folded != lowered))
    return distinct_lower, distinct_folded, accent_rows


def zip_stats(df: DataFrame, column: str) -> tuple[int, object]:
    text = blank(column)
    short_rows = count_if(df, text.isNotNull() & (F.length(text) < 5))
    min_length = one(df, F.min(F.length(text)))
    return short_rows, min_length


def add_gate(
    result: list[str],
    rows: list[tuple[str, str, str, str, str, str]],
    code: str,
    numerator: int,
    denominator: int,
    value: object,
    threshold: str,
    status: str,
) -> None:
    rows.append((code, str(numerator), str(denominator), fmt(value), threshold, status))
    result.append(f"{code}.numerator={numerator}")
    result.append(f"{code}.denominator={denominator}")
    result.append(f"{code}.value={fmt(value)}")
    result.append(f"{code}.threshold={threshold}")
    result.append(f"{code}.status={status}")


def status_at_least(value: int, minimum: int) -> str:
    return "pass" if value >= minimum else "fail"


def status_rate_at_least(value: float | None, minimum: float) -> str:
    if value is None:
        return "fail"
    return "pass" if value >= minimum else "fail"


def status_rate_at_most(value: float | None, maximum: float) -> str:
    if value is None:
        return "fail"
    return "pass" if value <= maximum else "fail"


def status_rate_between(value: float | None, low: float, high: float) -> str:
    if value is None:
        return "fail"
    return "pass" if low <= value <= high else "fail"


# COMMAND ----------


def profile_frames(spark: SparkSession, olist_dir: str) -> dict[str, DataFrame]:
    frames: dict[str, DataFrame] = {}
    for name in OLIST_FILES:
        path = f"{olist_dir}/{name}"
        # Serverless rejects DataFrame.cache() (PERSIST TABLE). Recompute on each action.
        frame = read_csv(spark, path)
        frames[name] = frame
    return frames


def run_file_profiles(frames: dict[str, DataFrame], result: list[str]) -> None:
    for name in OLIST_FILES:
        frame = frames[name]
        row_count = frame.count()
        keys = BUSINESS_KEYS[name]
        dup_groups, extra_rows = duplicate_stats(frame, keys)
        nulls = null_counts(frame, row_count)
        timestamps = timestamp_stats(frame, TIMESTAMP_COLUMNS.get(name, []))
        print_file_profile(
            name,
            row_count,
            len(frame.columns),
            dup_groups,
            extra_rows,
            nulls,
            timestamps,
            keys,
        )
        remember_profile(
            result,
            name,
            row_count,
            len(frame.columns),
            dup_groups,
            extra_rows,
            nulls,
            timestamps,
        )


def run_quality(
    frames: dict[str, DataFrame],
    deals: DataFrame,
    result: list[str],
) -> None:
    orders = frames["olist_orders_dataset.csv"]
    items = frames["olist_order_items_dataset.csv"]
    reviews = frames["olist_order_reviews_dataset.csv"]
    payments = frames["olist_order_payments_dataset.csv"]
    customers = frames["olist_customers_dataset.csv"]
    sellers = frames["olist_sellers_dataset.csv"]
    products = frames["olist_products_dataset.csv"]
    translation = frames["product_category_name_translation.csv"]
    geo = frames["olist_geolocation_dataset.csv"]

    print("\n## Quality checks")

    status_rows = (
        orders.groupBy(blank("order_status").alias("order_status"))
        .count()
        .orderBy(F.desc("count"))
        .collect()
    )
    print("\n| order_status | rows |")
    print("|---|---:|")
    for row in status_rows:
        label = row["order_status"] if row["order_status"] is not None else "(null)"
        print(f"| `{label}` | {row['count']} |")
        result.append(f"status.{label}={row['count']}")

    inversions = [
        ("approved_before_purchase", "order_purchase_timestamp", "order_approved_at"),
        ("carrier_before_approved", "order_approved_at", "order_delivered_carrier_date"),
        ("carrier_before_purchase", "order_purchase_timestamp", "order_delivered_carrier_date"),
        ("customer_before_carrier", "order_delivered_carrier_date", "order_delivered_customer_date"),
        ("customer_before_purchase", "order_purchase_timestamp", "order_delivered_customer_date"),
        ("estimated_before_purchase", "order_purchase_timestamp", "order_estimated_delivery_date"),
    ]
    print("\n| timestamp inversion | rows |")
    print("|---|---:|")
    for label, earlier, later in inversions:
        count = inversion_count(orders, earlier, later)
        print(f"| `{label}` | {count} |")
        result.append(f"ts.inversion.{label}={count}")

    item_orders = items.select(blank("order_id").alias("order_id")).where(F.col("order_id").isNotNull())
    order_ids = orders.select(blank("order_id").alias("order_id")).where(F.col("order_id").isNotNull())
    items_missing_order = item_orders.join(order_ids, "order_id", "left_anti").count()
    result.append(f"items.missing_order={items_missing_order}")
    print(f"\nitems whose order_id is absent from orders: {items_missing_order}")

    seller_counts = (
        items.groupBy(blank("order_id").alias("order_id"))
        .agg(F.countDistinct(blank("seller_id")).alias("n_sellers"))
        .where(F.col("order_id").isNotNull())
    )
    multi_seller_orders = seller_counts.where(F.col("n_sellers") > 1).count()
    orders_with_items = seller_counts.count()
    result.append(f"items.orders_with_items={orders_with_items}")
    result.append(f"items.multi_seller_orders={multi_seller_orders}")
    print(f"orders with items: {orders_with_items}")
    print(f"orders with more than one seller: {multi_seller_orders}")

    review_dup_groups, review_extra = duplicate_stats(reviews, ["review_id"])
    reviews_per_order = (
        reviews.groupBy(blank("order_id").alias("order_id"))
        .count()
        .where(F.col("order_id").isNotNull() & (F.col("count") > 1))
    )
    orders_many_reviews = reviews_per_order.count()
    score_rows = (
        reviews.groupBy(blank("review_score").alias("review_score"))
        .count()
        .orderBy("review_score")
        .collect()
    )
    result.append(f"review.dup_key_groups={review_dup_groups}")
    result.append(f"review.extra_dup_rows={review_extra}")
    result.append(f"review.orders_with_many_reviews={orders_many_reviews}")
    print(f"duplicate review_id groups: {review_dup_groups}")
    print(f"extra duplicate review rows: {review_extra}")
    print(f"orders with more than one review row: {orders_many_reviews}")
    print("\n| review_score | rows |")
    print("|---|---:|")
    for row in score_rows:
        label = row["review_score"] if row["review_score"] is not None else "(null)"
        print(f"| `{label}` | {row['count']} |")
        result.append(f"score.{label}={row['count']}")

    not_defined = count_if(payments, F.lower(blank("payment_type")) == F.lit("not_defined"))
    value_zero = count_if(payments, blank("payment_value").cast("double") == F.lit(0.0))
    installments_zero = count_if(
        payments, blank("payment_installments").cast("int") == F.lit(0)
    )
    result.append(f"pay.not_defined={not_defined}")
    result.append(f"pay.value_zero={value_zero}")
    result.append(f"pay.installments_zero={installments_zero}")
    print(f"\npayment_type = not_defined: {not_defined}")
    print(f"payment_value = 0: {value_zero}")
    print(f"payment_installments = 0: {installments_zero}")

    item_totals = items.groupBy(blank("order_id").alias("order_id")).agg(
        F.sum(blank("price").cast("double")).alias("item_price"),
        F.sum(blank("freight_value").cast("double")).alias("item_freight"),
    )
    pay_totals = payments.groupBy(blank("order_id").alias("order_id")).agg(
        F.sum(blank("payment_value").cast("double")).alias("paid")
    )
    compared = item_totals.join(pay_totals, "order_id", "inner").where(F.col("order_id").isNotNull())
    mismatch = count_if(
        compared,
        F.abs(
            F.coalesce(F.col("item_price"), F.lit(0.0))
            + F.coalesce(F.col("item_freight"), F.lit(0.0))
            - F.coalesce(F.col("paid"), F.lit(0.0))
        )
        > F.lit(0.01),
    )
    compared_orders = compared.count()
    result.append(f"pay.orders_compared={compared_orders}")
    result.append(f"pay.orders_abs_diff_gt_0_01={mismatch}")
    print(f"orders with both items and payments: {compared_orders}")
    print(f"orders where abs(price + freight - payment) > 0.01: {mismatch}")

    customer_rows = customers.count()
    customer_ids = distinct_values(customers, blank("customer_id"))
    customer_unique = distinct_values(customers, blank("customer_unique_id"))
    result.append(f"customer.rows={customer_rows}")
    result.append(f"customer.distinct_id={customer_ids}")
    result.append(f"customer.distinct_unique_id={customer_unique}")
    print(f"\ncustomer rows: {customer_rows}")
    print(f"distinct customer_id: {customer_ids}")
    print(f"distinct customer_unique_id: {customer_unique}")

    seller_ids = distinct_values(sellers, blank("seller_id"))
    seller_states = distinct_values(sellers, blank("seller_state"))
    seller_cities = distinct_values(sellers, blank("seller_city"))
    result.append(f"seller.distinct_id={seller_ids}")
    result.append(f"seller.distinct_state={seller_states}")
    result.append(f"seller.distinct_city={seller_cities}")
    print(f"distinct seller_id: {seller_ids}")
    print(f"distinct seller_state: {seller_states}")
    print(f"distinct seller_city: {seller_cities}")

    print("\n| city column | distinct_lower | distinct_folded | rows_with_accent |")
    print("|---|---:|---:|---:|")
    for label, frame, column in (
        ("customer_city", customers, "customer_city"),
        ("seller_city", sellers, "seller_city"),
        ("geolocation_city", geo, "geolocation_city"),
    ):
        distinct_lower, distinct_folded, accent_rows = city_fold_stats(frame, column)
        print(f"| `{label}` | {distinct_lower} | {distinct_folded} | {accent_rows} |")
        result.append(f"city.{label}.distinct_lower={distinct_lower}")
        result.append(f"city.{label}.distinct_folded={distinct_folded}")
        result.append(f"city.{label}.rows_with_accent={accent_rows}")

    missing_category = count_if(products, blank("product_category_name").isNull())
    product_categories = (
        products.select(blank("product_category_name").alias("cat"))
        .where(F.col("cat").isNotNull())
        .distinct()
    )
    translated = (
        translation.select(blank("product_category_name").alias("cat"))
        .where(F.col("cat").isNotNull())
        .distinct()
    )
    missing_translation = product_categories.join(translated, "cat", "left_anti").count()
    result.append(f"product.missing_category={missing_category}")
    result.append(f"product.category_missing_translation={missing_translation}")
    print(f"\nproducts missing category: {missing_category}")
    print(f"categories with no translation row: {missing_translation}")

    lat = blank("geolocation_lat").cast("double")
    lng = blank("geolocation_lng").cast("double")
    null_coord = lat.isNull() | lng.isNull()
    outside = (~null_coord) & (
        (lat < F.lit(BRAZIL_LAT_MIN))
        | (lat > F.lit(BRAZIL_LAT_MAX))
        | (lng < F.lit(BRAZIL_LNG_MIN))
        | (lng > F.lit(BRAZIL_LNG_MAX))
    )
    geo_rows = geo.count()
    outside_rows = count_if(geo, outside)
    null_coord_rows = count_if(geo, null_coord)
    per_zip = geo.groupBy(blank("geolocation_zip_code_prefix").alias("zip")).count()
    zip_row = per_zip.agg(
        F.count(F.lit(1)).alias("zips"),
        F.max("count").alias("max_rows"),
        F.avg("count").alias("avg_rows"),
        F.sum(F.when(F.col("count") > 1, 1).otherwise(0)).alias("zips_multi"),
    ).collect()[0]
    result.append(f"geo.rows={geo_rows}")
    result.append(f"geo.distinct_zip={int(zip_row['zips'] or 0)}")
    result.append(f"geo.max_rows_per_zip={fmt(zip_row['max_rows'])}")
    result.append(f"geo.avg_rows_per_zip={fmt(float(zip_row['avg_rows']) if zip_row['avg_rows'] is not None else None)}")
    result.append(f"geo.zips_with_many_rows={int(zip_row['zips_multi'] or 0)}")
    result.append(f"geo.outside_bbox={outside_rows}")
    result.append(f"geo.null_coord={null_coord_rows}")
    print(f"geolocation rows: {geo_rows}")
    print(f"distinct zip prefix: {int(zip_row['zips'] or 0)}")
    print(f"max rows per zip: {fmt(zip_row['max_rows'])}")
    print(f"avg rows per zip: {fmt(float(zip_row['avg_rows']) if zip_row['avg_rows'] is not None else None)}")
    print(f"zip prefixes with more than one row: {int(zip_row['zips_multi'] or 0)}")
    print(f"points outside Brazil bbox: {outside_rows}")
    print(f"rows with null lat or lng: {null_coord_rows}")

    print("\n| zip column | rows_shorter_than_5 | min_length |")
    print("|---|---:|---:|")
    for label, frame, column in (
        ("customer_zip_code_prefix", customers, "customer_zip_code_prefix"),
        ("seller_zip_code_prefix", sellers, "seller_zip_code_prefix"),
        ("geolocation_zip_code_prefix", geo, "geolocation_zip_code_prefix"),
    ):
        short_rows, min_length = zip_stats(frame, column)
        print(f"| `{label}` | {short_rows} | {fmt(min_length)} |")
        result.append(f"zip.{label}.short_lt5={short_rows}")
        result.append(f"zip.{label}.min_length={fmt(min_length)}")

    deal_rows = deals.count()
    deal_sellers = distinct_values(deals, blank("seller_id"))
    result.append(f"closed_deals.rows={deal_rows}")
    result.append(f"closed_deals.distinct_seller_id={deal_sellers}")
    print(f"\nclosed_deals rows: {deal_rows}")
    print(f"closed_deals distinct seller_id: {deal_sellers}")


def run_gates(frames: dict[str, DataFrame], deals: DataFrame, result: list[str]) -> None:
    orders = frames["olist_orders_dataset.csv"]
    items = frames["olist_order_items_dataset.csv"]
    reviews = frames["olist_order_reviews_dataset.csv"]

    purchase_month = F.date_format(parsed_ts("order_purchase_timestamp"), "yyyy-MM")
    order_months = orders.select(
        blank("order_id").alias("order_id"),
        purchase_month.alias("year_month"),
        blank("order_status").alias("order_status"),
        parsed_ts("order_delivered_carrier_date").alias("carrier_ts"),
        parsed_ts("order_delivered_customer_date").alias("customer_ts"),
    )
    item_sellers = items.select(
        blank("order_id").alias("order_id"),
        blank("seller_id").alias("seller_id"),
    )
    monthly_items = (
        item_sellers.join(order_months.select("order_id", "year_month"), "order_id", "left")
        .where(F.col("seller_id").isNotNull() & F.col("year_month").isNotNull())
        .groupBy("seller_id", "year_month")
        .agg(F.count(F.lit(1)).alias("item_rows"))
    )
    g1_sellers = (
        monthly_items.where(F.col("item_rows") >= G1_MIN_ITEMS)
        .groupBy("seller_id")
        .agg(F.count(F.lit(1)).alias("n_months"))
        .where(F.col("n_months") >= G1_MIN_MONTHS)
        .count()
    )
    sellers_in_items = (
        item_sellers.where(F.col("seller_id").isNotNull()).select("seller_id").distinct().count()
    )

    delivered = order_months.where(F.col("order_status") == F.lit("delivered"))
    delivered_rows = delivered.count()
    delivered_both = delivered.where(
        F.col("carrier_ts").isNotNull() & F.col("customer_ts").isNotNull()
    ).count()
    g2_value = rate(delivered_both, delivered_rows)

    seller_counts = (
        item_sellers.where(F.col("order_id").isNotNull())
        .groupBy("order_id")
        .agg(F.countDistinct("seller_id").alias("n_sellers"))
    )
    orders_with_items = seller_counts.count()
    multi_seller = seller_counts.where(F.col("n_sellers") > 1).count()
    g3_value = rate(multi_seller, orders_with_items)

    review_rows = reviews.count()
    low_score = count_if(reviews, blank("review_score").cast("int") <= F.lit(2))
    g4_value = rate(low_score, review_rows)

    month_rows = (
        order_months.groupBy("year_month")
        .agg(F.count(F.lit(1)).alias("n_orders"))
        .orderBy("year_month")
        .collect()
    )
    parsed_months = [row for row in month_rows if row["year_month"] is not None]
    null_month_orders = sum(int(row["n_orders"]) for row in month_rows if row["year_month"] is None)
    months_ge_1000 = sum(1 for row in parsed_months if int(row["n_orders"]) >= G5_MIN_ORDERS)

    deal_sellers = (
        deals.select(blank("seller_id").alias("seller_id"))
        .where(F.col("seller_id").isNotNull())
        .distinct()
    )
    item_seller_ids = (
        item_sellers.where(F.col("seller_id").isNotNull()).select("seller_id").distinct()
    )
    matched_sellers = item_seller_ids.join(deal_sellers, "seller_id", "inner").count()
    g6_value = rate(matched_sellers, sellers_in_items)
    funnel_flag = "yes" if g6_value is None or g6_value < G6_ATTRIBUTE_RATE else "no"

    gate_rows: list[tuple[str, str, str, str, str, str]] = []
    add_gate(
        result,
        gate_rows,
        "G1",
        g1_sellers,
        sellers_in_items,
        g1_sellers,
        f">={G1_MIN_SELLERS}",
        status_at_least(g1_sellers, G1_MIN_SELLERS),
    )
    add_gate(
        result,
        gate_rows,
        "G2",
        delivered_both,
        delivered_rows,
        g2_value,
        f">={G2_MIN_RATE}",
        status_rate_at_least(g2_value, G2_MIN_RATE),
    )
    add_gate(
        result,
        gate_rows,
        "G3",
        multi_seller,
        orders_with_items,
        g3_value,
        f"<={G3_MAX_RATE}",
        status_rate_at_most(g3_value, G3_MAX_RATE),
    )
    add_gate(
        result,
        gate_rows,
        "G4",
        low_score,
        review_rows,
        g4_value,
        f"{G4_MIN_RATE}-{G4_MAX_RATE}",
        status_rate_between(g4_value, G4_MIN_RATE, G4_MAX_RATE),
    )
    add_gate(
        result,
        gate_rows,
        "G5",
        months_ge_1000,
        len(parsed_months),
        months_ge_1000,
        f">={G5_MIN_MONTHS}",
        status_at_least(months_ge_1000, G5_MIN_MONTHS),
    )
    add_gate(
        result,
        gate_rows,
        "G6",
        matched_sellers,
        sellers_in_items,
        g6_value,
        f"record; flag if <{G6_ATTRIBUTE_RATE}",
        "record",
    )
    result.append(f"G6.funnel_as_attribute_only={funnel_flag}")

    print("\n## Gates")
    print("\n| gate | numerator | denominator | value | threshold | status |")
    print("|---|---:|---:|---:|---|---|")
    for code, numerator, denominator, value, threshold, status in gate_rows:
        print(f"| {code} | {numerator} | {denominator} | {value} | {threshold} | {status} |")
    print(f"G6.funnel_as_attribute_only={funnel_flag}")

    print("\n## Orders by month")
    print("\n| year_month | orders |")
    print("|---|---:|")
    for row in parsed_months:
        print(f"| {row['year_month']} | {row['n_orders']} |")
        result.append(f"month.{row['year_month']}={row['n_orders']}")
    print(f"| (null purchase timestamp) | {null_month_orders} |")
    result.append(f"month.null={null_month_orders}")


def print_result_block(source: dict[str, str | bool], result: list[str]) -> None:
    print("\n===== PHASE1_RESULT =====")
    print(f"SOURCE={source['source']}")
    print(f"NOT_OFFICIAL={'yes' if source['not_official'] else 'no'}")
    if source["source"] == "volume":
        print(f"VOLUME_ROOT={source['volume_root']}")
    else:
        print("NOT OFFICIAL")
    for line in result:
        print(line)
    print("===== END PHASE1_RESULT =====")


def main() -> None:
    source = resolve_source()
    print(f"SOURCE={source['source']}")
    print(f"NOT_OFFICIAL={'yes' if source['not_official'] else 'no'}")
    if source["not_official"]:
        print("NOT OFFICIAL")
    else:
        print(f"VOLUME_ROOT={source['volume_root']}")

    spark = get_spark()
    if source["not_official"]:
        spark.sparkContext.setLogLevel("WARN")

    olist_dir = str(source["olist_dir"])
    funnel_dir = str(source["funnel_dir"])
    frames = profile_frames(spark, olist_dir)
    for name, columns in (
        ("olist_orders_dataset.csv", [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]),
        ("olist_order_items_dataset.csv", ["order_id", "order_item_id", "seller_id", "price", "freight_value"]),
        ("olist_order_reviews_dataset.csv", ["review_id", "order_id", "review_score"]),
        ("olist_order_payments_dataset.csv", ["order_id", "payment_type", "payment_installments", "payment_value"]),
        ("olist_customers_dataset.csv", ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city"]),
        ("olist_sellers_dataset.csv", ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]),
        ("olist_products_dataset.csv", ["product_id", "product_category_name"]),
        ("product_category_name_translation.csv", ["product_category_name"]),
        ("olist_geolocation_dataset.csv", [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
        ]),
    ):
        require_columns(frames[name], f"{olist_dir}/{name}", columns)

    deals_path = f"{funnel_dir}/{CLOSED_DEALS_FILE}"
    deals = read_csv(spark, deals_path)
    require_columns(deals, deals_path, ["seller_id"])

    result: list[str] = []
    run_file_profiles(frames, result)
    run_quality(frames, deals, result)
    run_gates(frames, deals, result)
    print_result_block(source, result)


# COMMAND ----------

main()