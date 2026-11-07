# Databricks notebook source
"""Gold facts.

grain fact_order_item: one row = one order item (order_id, order_item_id).
grain fact_order: one row = one order.

The order flag is calculated from Silver once. fact_order_item is merged first
and repeats that flag. fact_order is merged second with the same flag.
"""

# COMMAND ----------

# MAGIC %run ./_audit

# COMMAND ----------

# MAGIC %run ./_dq

# COMMAND ----------

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

# COMMAND ----------

def widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name)
    text = "" if value is None else str(value).strip()
    return text or default


def align(df: DataFrame, table: str) -> DataFrame:
    return df.select(*spark.table(table).columns)


def date_key(column: str):
    day = F.to_date(column)
    return F.when(day.isNull(), F.lit(-1)).otherwise(
        (F.year(day) * 10000 + F.month(day) * 100 + F.dayofmonth(day)).cast("int")
    )


def fk_or_unknown(df: DataFrame, lookup: DataFrame, natural: str, key: str) -> DataFrame:
    slim = lookup.where(F.col(key) != -1).select(natural, key)
    joined = df.join(slim, natural, "left")
    return joined.withColumn(key, F.coalesce(F.col(key), F.lit(-1).cast(slim.schema[key].dataType)))


def unknown_pointers(df: DataFrame, columns: list[str]) -> int:
    if df.limit(1).count() == 0:
        return 0
    total = None
    for column in columns:
        piece = F.when(F.col(column) == -1, F.lit(1)).otherwise(F.lit(0))
        total = piece if total is None else (total + piece)
    value = df.select(F.sum(total).alias("n")).first()["n"]
    return 0 if value is None else int(value)


def merge_fact(table: str, frame: DataFrame, on_sql: str) -> None:
    align(frame, table).createOrReplaceTempView("fact_src")
    spark.sql(
        f"""
        MERGE INTO {table} t
        USING fact_src s
        ON {on_sql}
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )


def haversine(lat1, lng1, lat2, lng2):
    lat1_r = F.radians(lat1)
    lat2_r = F.radians(lat2)
    dlat = F.radians(lat2 - lat1)
    dlng = F.radians(lng2 - lng1)
    arc = F.pow(F.sin(dlat / 2), 2) + F.cos(lat1_r) * F.cos(lat2_r) * F.pow(F.sin(dlng / 2), 2)
    distance = F.lit(2.0 * 6371.0) * F.asin(F.sqrt(arc))
    missing = lat1.isNull() | lng1.isNull() | lat2.isNull() | lng2.isNull()
    return F.when(missing, F.lit(None).cast("double")).otherwise(distance)

# COMMAND ----------

catalog = widget("uc_catalog", "olist_catalog")
silver = widget("silver_schema", "silver")
gold = widget("gold_schema", "gold")
run_id = widget("run_id", "manual")
snapshot = F.to_date(F.lit(widget("snapshot_date", "2018-10-17")))


def silver_table(name: str) -> DataFrame:
    return spark.table(f"{catalog}.{silver}.{name}")


def gold_name(name: str) -> str:
    return f"{catalog}.{gold}.{name}"

# COMMAND ----------

# MAGIC %sql
# MAGIC -- grain: one row = one order item (order_id, order_item_id)
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.fact_order_item (
# MAGIC   order_id STRING NOT NULL COMMENT 'Degenerate grain key',
# MAGIC   order_item_id STRING NOT NULL COMMENT 'Degenerate grain key',
# MAGIC   purchase_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when purchase is null',
# MAGIC   shipping_limit_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when the limit is null',
# MAGIC   customer_key BIGINT NOT NULL COMMENT 'FK dim_customer. -1 when the person key is missing',
# MAGIC   seller_key BIGINT NOT NULL COMMENT 'FK dim_seller. -1 when seller_id does not match',
# MAGIC   product_key BIGINT NOT NULL COMMENT 'FK dim_product. -1 when product_id does not match',
# MAGIC   order_status_key BIGINT NOT NULL COMMENT 'FK dim_order_status from the order',
# MAGIC   price DECIMAL(18, 2) COMMENT 'Item price. Not freight',
# MAGIC   freight_value DECIMAL(18, 2) COMMENT 'Item freight. Not part of seller gmv',
# MAGIC   seller_ship_late_flag INT COMMENT '0, 1, or null. Do not sum across items of different orders',
# MAGIC   seller_handling_days DOUBLE COMMENT 'Official carrier minus official approved, in days',
# MAGIC   delivery_days DOUBLE COMMENT 'Copied from the order',
# MAGIC   delay_days DOUBLE COMMENT 'Copied from the order. Do not sum',
# MAGIC   late_delivery_flag INT COMMENT 'Copy of fact_order.late_flag. Do not sum',
# MAGIC   distance_km DOUBLE COMMENT 'Haversine kilometers. Null when a coordinate is missing'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'grain: one row = one order item (order_id, order_item_id)';
# MAGIC
# MAGIC -- grain: one row = one order
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.fact_order (
# MAGIC   order_id STRING NOT NULL COMMENT 'Grain',
# MAGIC   purchase_date_key INT NOT NULL COMMENT 'FK dim_date',
# MAGIC   approved_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official approved is null',
# MAGIC   delivered_carrier_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official carrier is null',
# MAGIC   delivered_customer_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official customer is null',
# MAGIC   estimated_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official estimated is null',
# MAGIC   customer_key BIGINT NOT NULL COMMENT 'FK dim_customer via customer_unique_id',
# MAGIC   customer_zip_prefix STRING COMMENT 'Zip of this order customer_id',
# MAGIC   customer_city_name STRING COMMENT 'Normalized city of this order',
# MAGIC   customer_state_code STRING COMMENT 'State of this order',
# MAGIC   customer_region_id STRING COMMENT 'IBGE region of this order',
# MAGIC   customer_region_code STRING COMMENT 'IBGE region code of this order',
# MAGIC   customer_region_name STRING COMMENT 'IBGE region name of this order',
# MAGIC   order_status_key BIGINT NOT NULL COMMENT 'FK dim_order_status',
# MAGIC   payment_type_key BIGINT NOT NULL COMMENT 'FK dim_payment_type. Primary type, else -1',
# MAGIC   items_value DECIMAL(18, 2) NOT NULL COMMENT 'Sum of price for every status. 0 when the order has no items',
# MAGIC   freight_total DECIMAL(18, 2) NOT NULL COMMENT 'Sum of freight. Not subtracted from items_value',
# MAGIC   payment_total DECIMAL(18, 2) NOT NULL COMMENT 'Sum of every payment_value. 0 when none',
# MAGIC   n_items INT NOT NULL COMMENT 'Item rows. 0 when the order has no items',
# MAGIC   n_sellers INT NOT NULL COMMENT 'Distinct sellers. 0 when the order has no items',
# MAGIC   delivery_days DOUBLE COMMENT 'Official customer minus purchase, in days',
# MAGIC   estimated_days DOUBLE COMMENT 'Date diff of official estimated and purchase',
# MAGIC   delay_days DOUBLE COMMENT 'Date diff of official customer and official estimated',
# MAGIC   late_flag INT COMMENT '1 when delay_days > 0. Null for canceled, unavailable, or a missing date',
# MAGIC   review_score INT COMMENT 'Score from order_reviews_dedup. Null when the order has no review',
# MAGIC   shared_review_type STRING COMMENT 'none, same_seller, or cross_seller. Null when there is no review',
# MAGIC   negative_review_flag INT COMMENT '1 when score <= 2. Null when there is no score',
# MAGIC   bad_experience_flag INT COMMENT 'Order-level flag. Not copied onto the seller-month snapshot',
# MAGIC   ts_inversion_flag INT NOT NULL COMMENT 'Copied from silver.orders'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'grain: one row = one order';
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order_item DROP CONSTRAINT IF EXISTS chk_foi_money;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order_item ADD CONSTRAINT chk_foi_money CHECK (
# MAGIC   (price IS NULL OR price >= 0) AND (freight_value IS NULL OR freight_value >= 0)
# MAGIC );
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order_item DROP CONSTRAINT IF EXISTS chk_foi_flags;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order_item ADD CONSTRAINT chk_foi_flags CHECK (
# MAGIC   (seller_ship_late_flag IS NULL OR seller_ship_late_flag IN (0, 1))
# MAGIC   AND (late_delivery_flag IS NULL OR late_delivery_flag IN (0, 1))
# MAGIC );
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order DROP CONSTRAINT IF EXISTS chk_fo_amounts_counts;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order ADD CONSTRAINT chk_fo_amounts_counts CHECK (
# MAGIC   items_value >= 0 AND freight_total >= 0 AND payment_total >= 0 AND n_items >= 0 AND n_sellers >= 0
# MAGIC );
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order DROP CONSTRAINT IF EXISTS chk_fo_review;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order ADD CONSTRAINT chk_fo_review CHECK (
# MAGIC   (review_score IS NULL OR review_score BETWEEN 1 AND 5)
# MAGIC   AND (shared_review_type IS NULL OR shared_review_type IN ('none', 'same_seller', 'cross_seller'))
# MAGIC   AND (
# MAGIC     (review_score IS NULL AND shared_review_type IS NULL)
# MAGIC     OR (review_score IS NOT NULL AND shared_review_type IS NOT NULL)
# MAGIC   )
# MAGIC );
# MAGIC
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order DROP CONSTRAINT IF EXISTS chk_fo_flags;
# MAGIC ALTER TABLE ${uc_catalog}.${gold_schema}.fact_order ADD CONSTRAINT chk_fo_flags CHECK (
# MAGIC   (late_flag IS NULL OR late_flag IN (0, 1))
# MAGIC   AND (negative_review_flag IS NULL OR negative_review_flag IN (0, 1))
# MAGIC   AND (bad_experience_flag IS NULL OR bad_experience_flag IN (0, 1))
# MAGIC   AND ts_inversion_flag IN (0, 1)
# MAGIC );

# COMMAND ----------

orders = silver_table("orders")
order_rows = int(orders.count())
customers = silver_table("customers").select(
    "customer_id",
    "customer_unique_id",
    F.col("customer_zip_code_prefix").alias("customer_zip_prefix"),
    F.col("customer_city").alias("customer_city_name"),
    F.col("customer_state").alias("customer_state_code"),
    F.col("region_id").alias("customer_region_id"),
    F.col("region_code").alias("customer_region_code"),
    F.col("region_name").alias("customer_region_name"),
    F.col("lat").alias("customer_lat"),
    F.col("lng").alias("customer_lng"),
)
reviews = silver_table("order_reviews_dedup").select(
    "order_id",
    "review_score",
    "shared_review_type",
)
items = silver_table("order_items")
item_rows = int(items.count())
payments = silver_table("order_payments")
sellers = silver_table("sellers").select(
    "seller_id",
    F.col("lat").alias("seller_lat"),
    F.col("lng").alias("seller_lng"),
)

item_totals = items.groupBy("order_id").agg(
    F.coalesce(F.sum("price"), F.lit(0)).cast("decimal(18,2)").alias("items_value"),
    F.coalesce(F.sum("freight_value"), F.lit(0)).cast("decimal(18,2)").alias("freight_total"),
    F.count("*").cast("int").alias("n_items"),
    F.countDistinct("seller_id").cast("int").alias("n_sellers"),
)
pay_totals = payments.groupBy("order_id").agg(
    F.coalesce(F.sum("payment_value"), F.lit(0)).cast("decimal(18,2)").alias("payment_total")
)
pay_groups = (
    payments.where(F.col("payment_type").isNotNull())
    .groupBy("order_id", "payment_type")
    .agg(
        F.sum("payment_value").alias("_pay_sum"),
        F.min(F.col("payment_sequential").cast("int")).alias("_pay_seq"),
    )
)
pay_rank = Window.partitionBy("order_id").orderBy(
    F.col("_pay_sum").desc_nulls_last(),
    F.col("_pay_seq").asc_nulls_last(),
    F.col("payment_type").asc(),
)
primary_pay = (
    pay_groups.withColumn("_rn", F.row_number().over(pay_rank))
    .where(F.col("_rn") == 1)
    .select("order_id", "payment_type")
)

order_calc = (
    orders.join(customers, "customer_id", "left")
    .join(reviews, "order_id", "left")
    .join(item_totals, "order_id", "left")
    .join(pay_totals, "order_id", "left")
    .join(primary_pay, "order_id", "left")
)
order_calc = (
    order_calc.withColumn("items_value", F.coalesce(F.col("items_value"), F.lit(0)).cast("decimal(18,2)"))
    .withColumn("freight_total", F.coalesce(F.col("freight_total"), F.lit(0)).cast("decimal(18,2)"))
    .withColumn("payment_total", F.coalesce(F.col("payment_total"), F.lit(0)).cast("decimal(18,2)"))
    .withColumn("n_items", F.coalesce(F.col("n_items"), F.lit(0)).cast("int"))
    .withColumn("n_sellers", F.coalesce(F.col("n_sellers"), F.lit(0)).cast("int"))
)
order_calc = order_calc.withColumn(
    "delivery_days",
    F.when(
        F.col("order_delivered_customer_date").isNotNull() & F.col("order_purchase_timestamp").isNotNull(),
        (F.unix_timestamp("order_delivered_customer_date") - F.unix_timestamp("order_purchase_timestamp")) / F.lit(86400.0),
    ),
).withColumn(
    "estimated_days",
    F.when(
        F.col("order_estimated_delivery_date").isNotNull(),
        F.datediff(F.to_date("order_estimated_delivery_date"), F.to_date("order_purchase_timestamp")).cast("double"),
    ),
).withColumn(
    "delay_days",
    F.when(
        F.col("order_delivered_customer_date").isNotNull() & F.col("order_estimated_delivery_date").isNotNull(),
        F.datediff(F.to_date("order_delivered_customer_date"), F.to_date("order_estimated_delivery_date")).cast("double"),
    ),
)
canceled = F.col("order_status").isin("canceled", "unavailable")
order_calc = order_calc.withColumn(
    "late_flag",
    F.when(canceled, F.lit(None).cast("int"))
    .when(F.col("delay_days") > 0, F.lit(1))
    .when(F.col("delay_days") <= 0, F.lit(0))
    .otherwise(F.lit(None).cast("int")),
).withColumn(
    "negative_review_flag",
    F.when(F.col("review_score").isNull(), F.lit(None).cast("int"))
    .when(F.col("review_score") <= 2, F.lit(1))
    .otherwise(F.lit(0)),
).withColumn(
    "bad_experience_flag",
    F.when((F.col("negative_review_flag") == 1) | (F.col("late_flag") == 1), F.lit(1))
    .when((F.col("late_flag") == 0) & (F.col("negative_review_flag").isNull() | (F.col("negative_review_flag") != 1)), F.lit(0))
    .otherwise(F.lit(None).cast("int")),
).withColumn(
    "shared_review_type",
    F.when(F.col("review_score").isNull(), F.lit(None).cast("string")).otherwise(F.col("shared_review_type")),
)

order_calc = fk_or_unknown(order_calc, spark.table(gold_name("dim_customer")), "customer_unique_id", "customer_key")
order_calc = fk_or_unknown(order_calc, spark.table(gold_name("dim_order_status")), "order_status", "order_status_key")
order_calc = fk_or_unknown(order_calc, spark.table(gold_name("dim_payment_type")), "payment_type", "payment_type_key")
for source_col, key_name in (
    ("order_purchase_timestamp", "purchase_date_key"),
    ("order_approved_at", "approved_date_key"),
    ("order_delivered_carrier_date", "delivered_carrier_date_key"),
    ("order_delivered_customer_date", "delivered_customer_date_key"),
    ("order_estimated_delivery_date", "estimated_date_key"),
):
    order_calc = order_calc.withColumn(key_name, date_key(source_col))

# COMMAND ----------

# grain: one row = one order item (order_id, order_item_id)
limit_before_purchase = F.col("shipping_limit_date").isNull() | F.col("order_purchase_timestamp").isNull() | (
    F.col("shipping_limit_date") < F.col("order_purchase_timestamp")
)
carrier_inverted = F.col("order_delivered_carrier_date").isNull() & F.col("raw_delivered_carrier_date").isNotNull()
carrier_present = F.col("order_delivered_carrier_date").isNotNull()
carrier_missing = F.col("order_delivered_carrier_date").isNull() & F.col("raw_delivered_carrier_date").isNull()
ship_late = (
    F.when(canceled, F.lit(None).cast("int"))
    .when(limit_before_purchase | carrier_inverted, F.lit(None).cast("int"))
    .when(
        carrier_present,
        F.when(F.col("order_delivered_carrier_date") > F.col("shipping_limit_date"), F.lit(1)).otherwise(F.lit(0)),
    )
    .when(carrier_missing & (F.to_date("shipping_limit_date") < snapshot), F.lit(1))
    .otherwise(F.lit(None).cast("int"))
)

item_fact = items.join(order_calc, "order_id", "left").join(sellers, "seller_id", "left")
item_fact = fk_or_unknown(item_fact, spark.table(gold_name("dim_seller")), "seller_id", "seller_key")
item_fact = fk_or_unknown(item_fact, spark.table(gold_name("dim_product")), "product_id", "product_key")
item_fact = (
    item_fact.withColumn("purchase_date_key", F.coalesce(F.col("purchase_date_key"), F.lit(-1)))
    .withColumn("shipping_limit_date_key", date_key("shipping_limit_date"))
    .withColumn("customer_key", F.coalesce(F.col("customer_key"), F.lit(-1)))
    .withColumn("order_status_key", F.coalesce(F.col("order_status_key"), F.lit(-1)))
    .withColumn("seller_ship_late_flag", ship_late)
    .withColumn(
        "seller_handling_days",
        F.when(
            F.col("order_delivered_carrier_date").isNotNull() & F.col("order_approved_at").isNotNull(),
            (F.unix_timestamp("order_delivered_carrier_date") - F.unix_timestamp("order_approved_at")) / F.lit(86400.0),
        ),
    )
    .withColumn("late_delivery_flag", F.col("late_flag"))
    .withColumn("distance_km", haversine(
        F.col("seller_lat"), F.col("seller_lng"), F.col("customer_lat"), F.col("customer_lng")
    ))
)
item_table = gold_name("fact_order_item")
item_unknown = unknown_pointers(
    item_fact,
    [
        "purchase_date_key",
        "shipping_limit_date_key",
        "customer_key",
        "seller_key",
        "product_key",
        "order_status_key",
    ],
)
item_keys = ["order_id", "order_item_id"]
item_dup = item_fact.groupBy(*item_keys).count().where(F.col("count") > 1).count()
print_warn("fact_order_item.duplicate_grain", f"groups={item_dup} expected=0")
item_grain_before = spark.table(item_table).select(*item_keys).dropDuplicates(item_keys).count()
item_source_keys = item_fact.select(*item_keys).dropDuplicates(item_keys)
# rows_loaded is this run's source row count, not the Gold table count after MERGE.
item_loaded = int(item_fact.count())
merge_fact(item_table, item_fact, "t.order_id = s.order_id AND t.order_item_id = s.order_item_id")
print_recon(item_table, item_rows, item_loaded, 0, 0)
item_grain_after = spark.table(item_table).select(*item_keys).dropDuplicates(item_keys).count()
item_orphans = (
    spark.table(item_table)
    .join(item_source_keys, item_keys, "left_anti")
    .select(*item_keys)
    .dropDuplicates(item_keys)
    .count()
)
print_grain_retention(
    item_table,
    int(item_grain_before),
    int(item_source_keys.count()),
    int(item_grain_after),
    int(item_orphans),
)
append_audit(
    catalog,
    gold,
    run_id,
    "gold",
    "fact_order_item",
    f"{silver}.order_items",
    item_rows,
    item_loaded,
    0,
    item_unknown,
)
silver_price = silver_table("order_items").select(F.sum("price").alias("price")).first()["price"]
source_price = item_fact.select(F.sum("price").alias("price")).first()["price"]
table_price = spark.table(item_table).select(F.sum("price").alias("price")).first()["price"]
print_warn(
    "fact_order_item.price_sum",
    f"silver={silver_price} source_batch={source_price} gold_table={table_price}",
)

# COMMAND ----------

# grain: one row = one order
order_table = gold_name("fact_order")
order_unknown = unknown_pointers(
    order_calc,
    [
        "purchase_date_key",
        "approved_date_key",
        "delivered_carrier_date_key",
        "delivered_customer_date_key",
        "estimated_date_key",
        "customer_key",
        "order_status_key",
        "payment_type_key",
    ],
)
order_dup = order_calc.groupBy("order_id").count().where(F.col("count") > 1).count()
print_warn("fact_order.duplicate_grain", f"groups={order_dup} expected=0")
order_grain_before = spark.table(order_table).select("order_id").dropDuplicates(["order_id"]).count()
order_source_keys = order_calc.select("order_id").dropDuplicates(["order_id"])
# rows_loaded is this run's source row count, not the Gold table count after MERGE.
order_loaded = int(order_calc.count())
merge_fact(order_table, order_calc, "t.order_id = s.order_id")
print_recon(order_table, order_rows, order_loaded, 0, 0)
order_grain_after = spark.table(order_table).select("order_id").dropDuplicates(["order_id"]).count()
order_orphans = (
    spark.table(order_table)
    .join(order_source_keys, "order_id", "left_anti")
    .select("order_id")
    .dropDuplicates(["order_id"])
    .count()
)
print_grain_retention(
    order_table,
    int(order_grain_before),
    int(order_source_keys.count()),
    int(order_grain_after),
    int(order_orphans),
)
append_audit(
    catalog,
    gold,
    run_id,
    "gold",
    "fact_order",
    f"{silver}.orders",
    order_rows,
    order_loaded,
    0,
    order_unknown,
)
inverted_rows = int(spark.table(order_table).where(F.col("ts_inversion_flag") == 1).count())
print_warn("fact_order.ts_inversion_flag", f"rows={inverted_rows}")
delivered = (
    spark.table(order_table)
    .join(
        spark.table(gold_name("dim_order_status")).select("order_status_key", "order_status"),
        "order_status_key",
        "left",
    )
    .where(F.col("order_status") == "delivered")
)
delivered_rows = int(delivered.count())
missing_milestone = int(
    delivered.where(
        (F.col("delivered_carrier_date_key") == -1) | (F.col("delivered_customer_date_key") == -1)
    ).count()
)
rate = None if delivered_rows == 0 else missing_milestone / delivered_rows
print_warn(
    "fact_order.g2_delivered_missing_milestone",
    f"missing={missing_milestone} delivered={delivered_rows} rate={rate} threshold=0.05",
)
