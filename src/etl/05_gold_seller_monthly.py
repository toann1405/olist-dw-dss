# Databricks notebook source
"""fact_seller_monthly.

grain: one row = one seller x one purchase month with at least one item.
gmv = SUM(price) excluding canceled and unavailable. A null status stays in gmv. Freight is not added.
"""

# COMMAND ----------

# MAGIC %run ./_audit

# COMMAND ----------

# MAGIC %run ./_dq

# COMMAND ----------

from pyspark.sql import functions as F

# COMMAND ----------

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

catalog = widget("uc_catalog", "olist_catalog")
gold = widget("gold_schema", "gold")
run_id = widget("run_id", "manual")


def gold_table(name: str) -> str:
    return f"{catalog}.{gold}.{name}"

# COMMAND ----------

# MAGIC %sql
# MAGIC -- grain: one row = one seller x one month with at least one item
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.fact_seller_monthly (
# MAGIC   seller_key BIGINT NOT NULL COMMENT 'FK dim_seller and grain',
# MAGIC   month_key INT NOT NULL COMMENT 'FK dim_month. Purchase month',
# MAGIC   seller_id STRING NOT NULL COMMENT 'Degenerate seller id',
# MAGIC   year_month STRING NOT NULL COMMENT 'yyyy-MM of the purchase month',
# MAGIC   n_orders_placed INT NOT NULL COMMENT 'Distinct orders, every status. Not additive across sellers',
# MAGIC   n_orders_valid INT NOT NULL COMMENT 'Distinct orders excluding canceled and unavailable',
# MAGIC   n_items_placed INT NOT NULL COMMENT 'Item rows, every status',
# MAGIC   n_items_valid INT NOT NULL COMMENT 'Item rows excluding canceled and unavailable',
# MAGIC   gmv DECIMAL(18, 2) NOT NULL COMMENT 'Sum of price excluding canceled and unavailable. Freight is excluded',
# MAGIC   aov DOUBLE COMMENT 'gmv / n_orders_valid when the denominator is positive',
# MAGIC   late_ship_count INT NOT NULL COMMENT 'Items with seller_ship_late_flag = 1',
# MAGIC   late_ship_eligible INT NOT NULL COMMENT 'Items with a non-null ship-late flag',
# MAGIC   late_ship_rate DOUBLE COMMENT 'late_ship_count / late_ship_eligible',
# MAGIC   late_delivery_count INT NOT NULL COMMENT 'Distinct orders with late_flag = 1',
# MAGIC   late_delivery_eligible INT NOT NULL COMMENT 'Distinct orders with a non-null late_flag',
# MAGIC   late_delivery_rate DOUBLE COMMENT 'late_delivery_count / late_delivery_eligible',
# MAGIC   review_score_sum INT NOT NULL COMMENT 'Sum of scores on seller-eligible orders',
# MAGIC   review_count INT NOT NULL COMMENT 'Distinct seller-eligible orders with a score',
# MAGIC   avg_review DOUBLE COMMENT 'review_score_sum / review_count',
# MAGIC   negative_review_count INT NOT NULL COMMENT 'Seller-eligible orders with a negative score',
# MAGIC   negative_review_eligible INT NOT NULL COMMENT 'Same denominator as review_count',
# MAGIC   negative_review_rate DOUBLE COMMENT 'negative_review_count / negative_review_eligible',
# MAGIC   bad_experience_count INT NOT NULL COMMENT 'Seller bad review or late_flag = 1',
# MAGIC   bad_experience_eligible INT NOT NULL COMMENT 'Seller review set or a non-null late_flag',
# MAGIC   bad_experience_rate DOUBLE COMMENT 'bad_experience_count / bad_experience_eligible',
# MAGIC   cancel_count INT NOT NULL COMMENT 'Distinct canceled or unavailable orders',
# MAGIC   cancel_eligible INT NOT NULL COMMENT 'Equals n_orders_placed',
# MAGIC   cancel_rate DOUBLE COMMENT 'cancel_count / n_orders_placed',
# MAGIC   handling_days_sum DOUBLE NOT NULL COMMENT 'Sum of non-null seller_handling_days',
# MAGIC   handling_days_count INT NOT NULL COMMENT 'Items with non-null handling days',
# MAGIC   avg_handling_days DOUBLE COMMENT 'handling_days_sum / handling_days_count'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'grain: one row = one seller x one purchase month with at least one item';
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_seller_monthly DROP CONSTRAINT IF EXISTS chk_fsm_totals;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_seller_monthly ADD CONSTRAINT chk_fsm_totals CHECK (
# MAGIC   n_orders_placed >= 1
# MAGIC   AND n_items_placed >= 1
# MAGIC   AND n_orders_valid >= 0
# MAGIC   AND n_orders_valid <= n_orders_placed
# MAGIC   AND n_items_valid >= 0
# MAGIC   AND n_items_valid <= n_items_placed
# MAGIC   AND gmv >= 0
# MAGIC   AND cancel_eligible = n_orders_placed
# MAGIC   AND ((n_orders_valid = 0 AND aov IS NULL) OR (n_orders_valid > 0 AND aov >= 0))
# MAGIC );
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_seller_monthly DROP CONSTRAINT IF EXISTS chk_fsm_num_den;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_seller_monthly ADD CONSTRAINT chk_fsm_num_den CHECK (
# MAGIC   late_ship_count >= 0 AND late_ship_eligible >= late_ship_count
# MAGIC   AND late_delivery_count >= 0 AND late_delivery_eligible >= late_delivery_count
# MAGIC   AND negative_review_count >= 0 AND negative_review_eligible >= negative_review_count
# MAGIC   AND bad_experience_count >= 0 AND bad_experience_eligible >= bad_experience_count
# MAGIC   AND cancel_count >= 0 AND cancel_eligible >= cancel_count
# MAGIC   AND review_count >= 0
# MAGIC   AND review_score_sum >= 0
# MAGIC   AND handling_days_count >= 0
# MAGIC   AND handling_days_sum >= 0
# MAGIC );
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_seller_monthly DROP CONSTRAINT IF EXISTS chk_fsm_rates;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_seller_monthly ADD CONSTRAINT chk_fsm_rates CHECK (
# MAGIC   (late_ship_rate IS NULL OR (late_ship_rate >= 0 AND late_ship_rate <= 1))
# MAGIC   AND (late_delivery_rate IS NULL OR (late_delivery_rate >= 0 AND late_delivery_rate <= 1))
# MAGIC   AND (negative_review_rate IS NULL OR (negative_review_rate >= 0 AND negative_review_rate <= 1))
# MAGIC   AND (bad_experience_rate IS NULL OR (bad_experience_rate >= 0 AND bad_experience_rate <= 1))
# MAGIC   AND (cancel_rate IS NULL OR (cancel_rate >= 0 AND cancel_rate <= 1))
# MAGIC   AND (avg_review IS NULL OR (avg_review >= 1 AND avg_review <= 5))
# MAGIC );

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
# Unknown seller (-1) has no seller_id. This grain is one real seller x one
# purchase month. Drop those items and items with no purchase month. Count
# them in rows_rejected. Do not invent a seller-month for member -1.
eligible = (
    joined.where(F.col("seller_key") != -1)
    .join(sellers, "seller_key", "inner")
    .join(dates, "purchase_date_key", "inner")
)
rows_rejected = rows_read - int(eligible.count())
# Null status is not canceled or unavailable, so it stays in GMV.
excluded_status = F.col("order_status").isin("canceled", "unavailable")
in_gmv = F.col("order_status").isNull() | ~excluded_status
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
    F.sum(F.when(in_gmv, F.lit(1)).otherwise(F.lit(0))).alias("valid_items"),
    F.sum(F.when(in_gmv, F.col("price"))).alias("gmv_part"),
    F.sum(F.when(F.col("seller_ship_late_flag") == 1, F.lit(1)).otherwise(F.lit(0))).alias("late_ship_count"),
    F.sum(F.when(F.col("seller_ship_late_flag").isNotNull(), F.lit(1)).otherwise(F.lit(0))).alias("late_ship_eligible"),
    F.sum("seller_handling_days").alias("handling_days_sum"),
    F.sum(F.when(F.col("seller_handling_days").isNotNull(), F.lit(1)).otherwise(F.lit(0))).alias("handling_days_count"),
)

monthly = by_order.groupBy("seller_key", "month_key", "seller_id", "year_month").agg(
    F.count("*").cast("int").alias("n_orders_placed"),
    F.sum(F.when(in_gmv, F.lit(1)).otherwise(F.lit(0))).cast("int").alias("n_orders_valid"),
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
    F.sum(F.when(excluded_status, F.lit(1)).otherwise(F.lit(0))).cast("int").alias("cancel_count"),
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
grain_keys = ["seller_key", "month_key"]
grain_before = spark.table(target).select(*grain_keys).dropDuplicates(grain_keys).count()
source_keys = monthly_src.select(*grain_keys).dropDuplicates(grain_keys)
# rows_loaded is this run's source row count, not the Gold table count after MERGE.
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
    0,
)
grain_after = spark.table(target).select(*grain_keys).dropDuplicates(grain_keys).count()
orphans = (
    spark.table(target)
    .join(source_keys, grain_keys, "left_anti")
    .select(*grain_keys)
    .dropDuplicates(grain_keys)
    .count()
)
print_grain_retention(target, int(grain_before), int(source_keys.count()), int(grain_after), int(orphans))

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

item_gmv = eligible.where(in_gmv).select(F.sum("price").alias("gmv")).first()["gmv"]
source_gmv = monthly_src.select(F.sum("gmv").alias("gmv")).first()["gmv"]
table_gmv = spark.table(target).select(F.sum("gmv").alias("gmv")).first()["gmv"]
print_warn(
    "fact_seller_monthly.gmv",
    f"source_item_price={item_gmv} source_batch={source_gmv} gold_table={table_gmv} freight_excluded=true",
)
