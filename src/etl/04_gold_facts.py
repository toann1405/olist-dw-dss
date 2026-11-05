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

from pyspark.sql import DataFrame, SparkSession, Window
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

spark = _spark()
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
item_dup = item_fact.groupBy("order_id", "order_item_id").count().where(F.col("count") > 1).count()
print_warn("fact_order_item.duplicate_grain", f"groups={item_dup} expected=0")
item_loaded = int(item_fact.count())
merge_fact(item_table, item_fact, "t.order_id = s.order_id AND t.order_item_id = s.order_item_id")
print_recon(item_table, item_rows, item_loaded, 0, 0)
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
fact_price = spark.table(item_table).select(F.sum("price").alias("price")).first()["price"]
print_warn("fact_order_item.price_sum", f"silver={silver_price} fact={fact_price}")

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
order_loaded = int(order_calc.count())
merge_fact(order_table, order_calc, "t.order_id = s.order_id")
print_recon(order_table, order_rows, order_loaded, 0, 0)
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
