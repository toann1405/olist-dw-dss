# Databricks notebook source
"""fact_seller_monthly.

grain: one row = one seller x one purchase month with at least one item.
gmv = SUM(price) excluding canceled and unavailable. Freight is not added.
"""

# COMMAND ----------

# MAGIC %run ./_audit

# COMMAND ----------

# MAGIC %run ./_dq

# COMMAND ----------

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

# COMMAND ----------

def _spark() -> SparkSession:
    existing = globals().get("spark")
    if isinstance(existing, SparkSession):
        return existing
    active = SparkSession.getActiveSession()
    if active is None:
        raise RuntimeError("No active Spark session")
    return active


def widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name)
    text = "" if value is None else str(value).strip()
    return text or default


def rate(numerator: str, denominator: str):
    return F.when(
        F.col(denominator) > 0,
        F.col(numerator).cast("double") / F.col(denominator),
    ).otherwise(F.lit(None).cast("double"))

# COMMAND ----------

spark = _spark()
catalog = widget("uc_catalog", "olist_catalog")
gold = widget("gold_schema", "gold")
run_id = widget("run_id", "manual")


def gold_table(name: str) -> str:
    return f"{catalog}.{gold}.{name}"

# COMMAND ----------

items = spark.table(gold_table("fact_order_item")).select(
    "order_id",
    "seller_key",
    "purchase_date_key",
    "price",
    "seller_ship_late_flag",
    "seller_handling_days",
)
orders = spark.table(gold_table("fact_order")).select(
    "order_id",
    "order_status_key",
    "late_flag",
    "n_sellers",
    "review_score",
    "shared_review_type",
    "negative_review_flag",
)
status = spark.table(gold_table("dim_order_status")).select("order_status_key", "order_status")
dates = (
    spark.table(gold_table("dim_date"))
    .where(F.col("date_key") != -1)
    .select(
        F.col("date_key").alias("purchase_date_key"),
        "month_key",
        F.format_string("%04d-%02d", F.col("year"), F.col("month")).alias("year_month"),
    )
)
sellers = (
    spark.table(gold_table("dim_seller"))
    .where(F.col("seller_key") != -1)
    .select("seller_key", "seller_id")
)

rows_read = int(items.count())
joined = items.join(orders, "order_id", "left").join(status, "order_status_key", "left")
eligible = (
    joined.where(F.col("seller_key") != -1)
    .join(sellers, "seller_key", "inner")
    .join(dates, "purchase_date_key", "inner")
)
rows_rejected = rows_read - int(eligible.count())
canceled = F.col("order_status").isin("canceled", "unavailable")
review_ok = (
    (F.col("n_sellers") == 1)
    & F.col("shared_review_type").isin("none", "same_seller")
    & F.col("review_score").isNotNull()
)

by_order = eligible.groupBy("seller_key", "month_key", "seller_id", "year_month", "order_id").agg(
    F.first("order_status").alias("order_status"),
    F.first("late_flag").alias("late_flag"),
    F.first("n_sellers").alias("n_sellers"),
    F.first("review_score").alias("review_score"),
    F.first("shared_review_type").alias("shared_review_type"),
    F.first("negative_review_flag").alias("negative_review_flag"),
    F.count("*").alias("item_rows"),
    F.sum(F.when(~canceled, F.lit(1)).otherwise(F.lit(0))).alias("valid_items"),
    F.sum(F.when(~canceled, F.col("price"))).alias("gmv_part"),
    F.sum(F.when(F.col("seller_ship_late_flag") == 1, F.lit(1)).otherwise(F.lit(0))).alias("late_ship_count"),
    F.sum(F.when(F.col("seller_ship_late_flag").isNotNull(), F.lit(1)).otherwise(F.lit(0))).alias("late_ship_eligible"),
    F.sum("seller_handling_days").alias("handling_days_sum"),
    F.sum(F.when(F.col("seller_handling_days").isNotNull(), F.lit(1)).otherwise(F.lit(0))).alias("handling_days_count"),
)

monthly = by_order.groupBy("seller_key", "month_key", "seller_id", "year_month").agg(
    F.count("*").cast("int").alias("n_orders_placed"),
    F.sum(F.when(~canceled, F.lit(1)).otherwise(F.lit(0))).cast("int").alias("n_orders_valid"),
    F.sum("item_rows").cast("int").alias("n_items_placed"),
    F.sum("valid_items").cast("int").alias("n_items_valid"),
    F.coalesce(F.sum("gmv_part"), F.lit(0)).cast("decimal(18,2)").alias("gmv"),
    F.sum("late_ship_count").cast("int").alias("late_ship_count"),
    F.sum("late_ship_eligible").cast("int").alias("late_ship_eligible"),
    F.sum(F.when(F.col("late_flag") == 1, F.lit(1)).otherwise(F.lit(0))).cast("int").alias("late_delivery_count"),
    F.sum(F.when(F.col("late_flag").isNotNull(), F.lit(1)).otherwise(F.lit(0))).cast("int").alias("late_delivery_eligible"),
    F.sum(F.when(review_ok, F.col("review_score")).otherwise(F.lit(0))).cast("int").alias("review_score_sum"),
    F.sum(F.when(review_ok, F.lit(1)).otherwise(F.lit(0))).cast("int").alias("review_count"),
    F.sum(F.when(review_ok & (F.col("negative_review_flag") == 1), F.lit(1)).otherwise(F.lit(0)))
    .cast("int")
    .alias("negative_review_count"),
    F.sum(
        F.when((review_ok & (F.col("negative_review_flag") == 1)) | (F.col("late_flag") == 1), F.lit(1)).otherwise(F.lit(0))
    )
    .cast("int")
    .alias("bad_experience_count"),
    F.sum(F.when(review_ok | F.col("late_flag").isNotNull(), F.lit(1)).otherwise(F.lit(0)))
    .cast("int")
    .alias("bad_experience_eligible"),
    F.sum(F.when(canceled, F.lit(1)).otherwise(F.lit(0))).cast("int").alias("cancel_count"),
    F.coalesce(F.sum("handling_days_sum"), F.lit(0.0)).cast("double").alias("handling_days_sum"),
    F.sum("handling_days_count").cast("int").alias("handling_days_count"),
)
monthly = (
    monthly.withColumn("cancel_eligible", F.col("n_orders_placed"))
    .withColumn("negative_review_eligible", F.col("review_count"))
    .withColumn(
        "aov",
        F.when(F.col("n_orders_valid") > 0, F.col("gmv").cast("double") / F.col("n_orders_valid")),
    )
    .withColumn("late_ship_rate", rate("late_ship_count", "late_ship_eligible"))
    .withColumn("late_delivery_rate", rate("late_delivery_count", "late_delivery_eligible"))
    .withColumn("negative_review_rate", rate("negative_review_count", "negative_review_eligible"))
    .withColumn("bad_experience_rate", rate("bad_experience_count", "bad_experience_eligible"))
    .withColumn("cancel_rate", rate("cancel_count", "cancel_eligible"))
    .withColumn("avg_review", rate("review_score_sum", "review_count"))
    .withColumn(
        "avg_handling_days",
        F.when(
            F.col("handling_days_count") > 0,
            F.col("handling_days_sum") / F.col("handling_days_count"),
        ),
    )
)

target = gold_table("fact_seller_monthly")
columns = spark.table(target).columns
monthly_src = monthly.select(*columns)
rows_loaded = int(monthly_src.count())
rows_dropped = rows_read - rows_loaded - rows_rejected
monthly_src.createOrReplaceTempView("seller_month_src")
spark.sql(
    f"""
    MERGE INTO {target} t
    USING seller_month_src s
    ON t.seller_key = s.seller_key AND t.month_key = s.month_key
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
    """
)
print_recon(target, rows_read, rows_loaded, rows_dropped, rows_rejected)
append_audit(
    catalog,
    gold,
    run_id,
    "gold",
    "fact_seller_monthly",
    f"{gold}.fact_order_item",
    rows_read,
    rows_loaded,
    rows_rejected,
    None,
)

dup = (
    spark.table(target)
    .groupBy("seller_key", "month_key")
    .count()
    .where(F.col("count") > 1)
    .count()
)
print_warn("fact_seller_monthly.duplicate_grain", f"groups={dup} expected=0")
below_one = int(spark.table(target).where(F.col("n_orders_placed") < 1).count())
print_warn("fact_seller_monthly.n_orders_placed", f"rows_below_1={below_one}")

item_gmv = (
    eligible.where(~F.col("order_status").isin("canceled", "unavailable"))
    .select(F.sum("price").alias("gmv"))
    .first()["gmv"]
)
fact_gmv = spark.table(target).select(F.sum("gmv").alias("gmv")).first()["gmv"]
print_warn("fact_seller_monthly.gmv", f"item_price_sum={item_gmv} fact_gmv={fact_gmv} freight_excluded=true")
