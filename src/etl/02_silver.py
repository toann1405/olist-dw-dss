# Databricks notebook source
"""Silver FULL LOAD OVERWRITE. Cast, within-file dedupe, city, category, region."""

# COMMAND ----------

# MAGIC %run ./_audit

# COMMAND ----------

# MAGIC %run ./_dq

# COMMAND ----------

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

# COMMAND ----------

TS_FMT = "yyyy-MM-dd HH:mm:ss"
ACCENT_FROM = "áàâãäåéèêëíìîïóòôõöúùûüçñ"
ACCENT_TO = "aaaaaaeeeeiiiiooooouuuucn"
LAT_MIN, LAT_MAX = -34.0, 6.0
LNG_MIN, LNG_MAX = -74.0, -28.0

# COMMAND ----------

def widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name)
    text = "" if value is None else str(value).strip()
    return text or default


def blank(column: str):
    trimmed = F.trim(F.col(column))
    return F.when(trimmed.isNull() | (trimmed == ""), F.lit(None)).otherwise(trimmed)


def city_norm(column: str):
    return F.translate(F.lower(blank(column)), ACCENT_FROM, ACCENT_TO)


def parse_ts(column: str):
    """Datetime first. A date-only value such as 2018-02-01 becomes midnight.

    try_to_timestamp returns null on a bad string. ANSI to_timestamp fails the task.
    """
    text = blank(column)
    return F.coalesce(
        F.try_to_timestamp(text, F.lit(TS_FMT)),
        F.try_to_timestamp(text, F.lit("yyyy-MM-dd")),
    )


def parse_int(column: str):
    return blank(column).cast("int")


def money(column: str):
    casted = blank(column).cast("decimal(18,2)")
    return F.when(casted < 0, F.lit(None).cast("decimal(18,2)")).otherwise(casted)


def keep_max_lex(df: DataFrame, keys: list[str], columns: list[str]) -> tuple[DataFrame, int]:
    lex = F.concat_ws("\u001f", *[F.coalesce(F.col(name).cast("string"), F.lit("")) for name in columns])
    window = Window.partitionBy(*keys).orderBy(lex.desc())
    ranked = df.withColumn("_rn", F.row_number().over(window))
    dropped = ranked.where(F.col("_rn") > 1).count()
    return ranked.where(F.col("_rn") == 1).drop("_rn"), int(dropped)


def reject_blank_keys(df: DataFrame, keys: list[str]) -> tuple[DataFrame, int]:
    bad = None
    for key in keys:
        piece = F.col(key).isNull()
        bad = piece if bad is None else (bad | piece)
    rejected = int(df.where(bad).count())
    return df.where(~bad), rejected


def overwrite(df: DataFrame, table: str) -> None:
    # The DDL cell created the types and NOT NULL. Replacing the schema would drop them.
    spark.table(table)
    df.write.format("delta").mode("overwrite").saveAsTable(table)


def publish(table: str, source: str, frame: DataFrame, rows_read: int, rows_rejected: int, rows_dropped: int) -> None:
    overwrite(frame, table)
    rows_loaded = int(spark.table(table).count())
    print_recon(table, rows_read, rows_loaded, rows_dropped, rows_rejected)
    append_audit(
        catalog,
        gold,
        run_id,
        "silver",
        table.split(".")[-1],
        source,
        rows_read,
        rows_loaded,
        rows_rejected,
        None,
    )

# COMMAND ----------

catalog = widget("uc_catalog", "olist_catalog")
bronze = widget("bronze_schema", "bronze")
silver = widget("silver_schema", "silver")
gold = widget("gold_schema", "gold")
run_id = widget("run_id", "manual")


def bronze_table(name: str) -> DataFrame:
    return spark.table(f"{catalog}.{bronze}.{name}")


def silver_name(name: str) -> str:
    return f"{catalog}.{silver}.{name}"

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Typed Silver tables. NOT NULL stays because the load overwrites rows, not the schema.
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.state_region (
# MAGIC   state_id STRING,
# MAGIC   state_code STRING NOT NULL,
# MAGIC   state_name STRING,
# MAGIC   region_id STRING,
# MAGIC   region_code STRING,
# MAGIC   region_name STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.category_translation (
# MAGIC   product_category_name STRING NOT NULL,
# MAGIC   product_category_name_english STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.geolocation_zip (
# MAGIC   zip_prefix STRING NOT NULL,
# MAGIC   lat DOUBLE,
# MAGIC   lng DOUBLE,
# MAGIC   city_name STRING,
# MAGIC   state_code STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.geolocation_city (
# MAGIC   city_norm STRING NOT NULL,
# MAGIC   state_code STRING NOT NULL,
# MAGIC   lat DOUBLE,
# MAGIC   lng DOUBLE
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.orders (
# MAGIC   order_id STRING NOT NULL,
# MAGIC   customer_id STRING,
# MAGIC   order_status STRING,
# MAGIC   order_purchase_timestamp TIMESTAMP,
# MAGIC   raw_approved_at TIMESTAMP,
# MAGIC   raw_delivered_carrier_date TIMESTAMP,
# MAGIC   raw_delivered_customer_date TIMESTAMP,
# MAGIC   raw_estimated_delivery_date TIMESTAMP,
# MAGIC   order_approved_at TIMESTAMP,
# MAGIC   order_delivered_carrier_date TIMESTAMP,
# MAGIC   order_delivered_customer_date TIMESTAMP,
# MAGIC   order_estimated_delivery_date TIMESTAMP,
# MAGIC   ts_inversion_flag INT NOT NULL
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.order_items (
# MAGIC   order_id STRING NOT NULL,
# MAGIC   order_item_id STRING NOT NULL,
# MAGIC   product_id STRING,
# MAGIC   seller_id STRING,
# MAGIC   shipping_limit_date TIMESTAMP,
# MAGIC   price DECIMAL(18, 2),
# MAGIC   freight_value DECIMAL(18, 2)
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.order_payments (
# MAGIC   order_id STRING NOT NULL,
# MAGIC   payment_sequential STRING NOT NULL,
# MAGIC   payment_type STRING,
# MAGIC   payment_installments INT,
# MAGIC   payment_value DECIMAL(18, 2)
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.products (
# MAGIC   product_id STRING NOT NULL,
# MAGIC   product_category_name STRING,
# MAGIC   product_name_lenght INT,
# MAGIC   product_description_lenght INT,
# MAGIC   product_photos_qty INT,
# MAGIC   product_weight_g INT,
# MAGIC   product_length_cm INT,
# MAGIC   product_height_cm INT,
# MAGIC   product_width_cm INT,
# MAGIC   category_name_en STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.customers (
# MAGIC   customer_id STRING NOT NULL,
# MAGIC   customer_unique_id STRING,
# MAGIC   customer_zip_code_prefix STRING,
# MAGIC   customer_city STRING,
# MAGIC   customer_state STRING,
# MAGIC   lat DOUBLE,
# MAGIC   lng DOUBLE,
# MAGIC   geo_match_level STRING NOT NULL,
# MAGIC   region_id STRING,
# MAGIC   region_code STRING,
# MAGIC   region_name STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.sellers (
# MAGIC   seller_id STRING NOT NULL,
# MAGIC   seller_zip_code_prefix STRING,
# MAGIC   seller_city STRING,
# MAGIC   seller_state STRING,
# MAGIC   lat DOUBLE,
# MAGIC   lng DOUBLE,
# MAGIC   geo_match_level STRING NOT NULL,
# MAGIC   region_id STRING,
# MAGIC   region_code STRING,
# MAGIC   region_name STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.order_reviews (
# MAGIC   review_id STRING NOT NULL,
# MAGIC   order_id STRING NOT NULL,
# MAGIC   review_score INT,
# MAGIC   review_comment_title STRING,
# MAGIC   review_comment_message STRING,
# MAGIC   review_creation_date TIMESTAMP,
# MAGIC   review_answer_timestamp TIMESTAMP
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.order_reviews_dedup (
# MAGIC   review_id STRING NOT NULL,
# MAGIC   order_id STRING NOT NULL,
# MAGIC   review_score INT,
# MAGIC   review_comment_title STRING,
# MAGIC   review_comment_message STRING,
# MAGIC   review_creation_date TIMESTAMP,
# MAGIC   review_answer_timestamp TIMESTAMP,
# MAGIC   shared_review_type STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.closed_deals (
# MAGIC   mql_id STRING,
# MAGIC   seller_id STRING,
# MAGIC   sdr_id STRING,
# MAGIC   sr_id STRING,
# MAGIC   won_date TIMESTAMP,
# MAGIC   business_segment STRING,
# MAGIC   lead_type STRING,
# MAGIC   lead_behaviour_profile STRING,
# MAGIC   has_company STRING,
# MAGIC   has_gtin STRING,
# MAGIC   average_stock STRING,
# MAGIC   business_type STRING,
# MAGIC   declared_product_catalog_size STRING,
# MAGIC   declared_monthly_revenue STRING
# MAGIC ) USING DELTA;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${silver_schema}.marketing_qualified_leads (
# MAGIC   mql_id STRING NOT NULL,
# MAGIC   first_contact_date TIMESTAMP,
# MAGIC   landing_page_id STRING,
# MAGIC   origin STRING
# MAGIC ) USING DELTA;

# COMMAND ----------

region_raw = bronze_table("state_region")
region_rows = int(region_raw.count())
region = region_raw.select(
    blank("state_id").alias("state_id"),
    F.upper(blank("state_code")).alias("state_code"),
    blank("state_name").alias("state_name"),
    blank("region_id").alias("region_id"),
    blank("region_code").alias("region_code"),
    blank("region_name").alias("region_name"),
)
region, region_rejected = reject_blank_keys(region, ["state_code"])
region_cols = ["state_id", "state_code", "state_name", "region_id", "region_code", "region_name"]
region, region_dropped = keep_max_lex(region, ["state_code"], region_cols)
publish(silver_name("state_region"), f"{bronze}.state_region", region, region_rows, region_rejected, region_dropped)

# COMMAND ----------

translation_raw = bronze_table("category_translation")
translation_rows = int(translation_raw.count())
translation = translation_raw.select(
    blank("product_category_name").alias("product_category_name"),
    blank("product_category_name_english").alias("product_category_name_english"),
)
translation, translation_rejected = reject_blank_keys(translation, ["product_category_name"])
translation, translation_dropped = keep_max_lex(
    translation,
    ["product_category_name"],
    ["product_category_name", "product_category_name_english"],
)
publish(
    silver_name("category_translation"),
    f"{bronze}.category_translation",
    translation,
    translation_rows,
    translation_rejected,
    translation_dropped,
)
dup_names = (
    spark.table(silver_name("category_translation"))
    .groupBy("product_category_name")
    .count()
    .where(F.col("count") > 1)
    .count()
)
print_warn("category_translation.duplicate_name", f"groups={dup_names} expected=0")

# COMMAND ----------

geo_raw = bronze_table("geolocation")
geo_rows = int(geo_raw.count())
geo = geo_raw.select(
    blank("geolocation_zip_code_prefix").alias("zip_prefix"),
    blank("geolocation_lat").cast("double").alias("lat"),
    blank("geolocation_lng").cast("double").alias("lng"),
    city_norm("geolocation_city").alias("city_norm"),
    F.upper(blank("geolocation_state")).alias("state_code"),
)
geo, geo_key_rejected = reject_blank_keys(geo, ["zip_prefix"])
in_bbox = (
    F.col("lat").isNotNull()
    & F.col("lng").isNotNull()
    & F.col("lat").between(LAT_MIN, LAT_MAX)
    & F.col("lng").between(LNG_MIN, LNG_MAX)
)
bad_points = int(geo.where(~in_bbox).count())
good = geo.where(in_bbox)
geo_rejected = geo_key_rejected + bad_points

city_counts = good.groupBy("zip_prefix", "city_norm").count()
city_mode = (
    city_counts.withColumn(
        "_rn",
        F.row_number().over(
            Window.partitionBy("zip_prefix").orderBy(F.col("count").desc(), F.col("city_norm").asc_nulls_last())
        ),
    )
    .where(F.col("_rn") == 1)
    .select("zip_prefix", F.col("city_norm").alias("city_name"))
)
state_counts = good.groupBy("zip_prefix", "state_code").count()
state_mode = (
    state_counts.withColumn(
        "_rn",
        F.row_number().over(
            Window.partitionBy("zip_prefix").orderBy(F.col("count").desc(), F.col("state_code").asc_nulls_last())
        ),
    )
    .where(F.col("_rn") == 1)
    .select("zip_prefix", "state_code")
)
zip_table = (
    good.groupBy("zip_prefix")
    .agg(
        F.expr("percentile_approx(lat, 0.5)").alias("lat"),
        F.expr("percentile_approx(lng, 0.5)").alias("lng"),
    )
    .join(city_mode, "zip_prefix", "left")
    .join(state_mode, "zip_prefix", "left")
    .select("zip_prefix", "lat", "lng", "city_name", "state_code")
)
good_points = int(good.count())
zip_loaded_preview = int(zip_table.count())
# read = zip rows + extra in-bbox points + blank keys + points outside the bbox
zip_dropped = good_points - zip_loaded_preview
publish(
    silver_name("geolocation_zip"),
    f"{bronze}.geolocation",
    zip_table,
    geo_rows,
    geo_rejected,
    zip_dropped,
)
dup_zip = (
    spark.table(silver_name("geolocation_zip")).groupBy("zip_prefix").count().where(F.col("count") > 1).count()
)
print_warn("geolocation_zip.duplicate_prefix", f"groups={dup_zip} expected=0")

city_table = (
    good.where(F.col("city_norm").isNotNull() & F.col("state_code").isNotNull())
    .groupBy("city_norm", "state_code")
    .agg(
        F.expr("percentile_approx(lat, 0.5)").alias("lat"),
        F.expr("percentile_approx(lng, 0.5)").alias("lng"),
    )
)
city_loaded_preview = int(city_table.count())
city_source_rows = int(good.where(F.col("city_norm").isNotNull() & F.col("state_code").isNotNull()).count())
publish(
    silver_name("geolocation_city"),
    f"{bronze}.geolocation",
    city_table,
    city_source_rows,
    0,
    city_source_rows - city_loaded_preview,
)

# COMMAND ----------

orders_raw = bronze_table("orders")
orders_rows = int(orders_raw.count())
purchase = parse_ts("order_purchase_timestamp")
raw_approved = parse_ts("order_approved_at")
raw_carrier = parse_ts("order_delivered_carrier_date")
raw_customer = parse_ts("order_delivered_customer_date")
raw_estimated = parse_ts("order_estimated_delivery_date")
orders = orders_raw.select(
    blank("order_id").alias("order_id"),
    blank("customer_id").alias("customer_id"),
    F.lower(blank("order_status")).alias("order_status"),
    purchase.alias("order_purchase_timestamp"),
    raw_approved.alias("raw_approved_at"),
    raw_carrier.alias("raw_delivered_carrier_date"),
    raw_customer.alias("raw_delivered_customer_date"),
    raw_estimated.alias("raw_estimated_delivery_date"),
)
at_or_after_purchase = lambda raw: raw.isNotNull() & F.col("order_purchase_timestamp").isNotNull() & (
    raw >= F.col("order_purchase_timestamp")
)
orders = (
    orders.withColumn(
        "order_approved_at",
        F.when(at_or_after_purchase(F.col("raw_approved_at")), F.col("raw_approved_at")),
    )
    .withColumn(
        "order_delivered_carrier_date",
        F.when(
            at_or_after_purchase(F.col("raw_delivered_carrier_date"))
            & (
                F.col("raw_approved_at").isNull()
                | (F.col("raw_delivered_carrier_date") >= F.col("raw_approved_at"))
            ),
            F.col("raw_delivered_carrier_date"),
        ),
    )
    .withColumn(
        "order_delivered_customer_date",
        F.when(
            at_or_after_purchase(F.col("raw_delivered_customer_date"))
            & (
                F.col("raw_delivered_carrier_date").isNull()
                | (F.col("raw_delivered_customer_date") >= F.col("raw_delivered_carrier_date"))
            ),
            F.col("raw_delivered_customer_date"),
        ),
    )
    .withColumn(
        "order_estimated_delivery_date",
        F.when(at_or_after_purchase(F.col("raw_estimated_delivery_date")), F.col("raw_estimated_delivery_date")),
    )
)
inverted = (
    (F.col("raw_approved_at").isNotNull() & F.col("order_approved_at").isNull())
    | (F.col("raw_delivered_carrier_date").isNotNull() & F.col("order_delivered_carrier_date").isNull())
    | (F.col("raw_delivered_customer_date").isNotNull() & F.col("order_delivered_customer_date").isNull())
    | (F.col("raw_estimated_delivery_date").isNotNull() & F.col("order_estimated_delivery_date").isNull())
)
orders = orders.withColumn("ts_inversion_flag", F.when(inverted, F.lit(1)).otherwise(F.lit(0)))
orders, orders_rejected = reject_blank_keys(orders, ["order_id"])
order_cols = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "raw_approved_at",
    "raw_delivered_carrier_date",
    "raw_delivered_customer_date",
    "raw_estimated_delivery_date",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "ts_inversion_flag",
]
orders, orders_dropped = keep_max_lex(orders, ["order_id"], order_cols)
publish(silver_name("orders"), f"{bronze}.orders", orders, orders_rows, orders_rejected, orders_dropped)
inverted_rows = int(spark.table(silver_name("orders")).where(F.col("ts_inversion_flag") == 1).count())
print_warn("orders.ts_inversion_flag", f"rows={inverted_rows}")

# COMMAND ----------

items_raw = bronze_table("order_items")
items_rows = int(items_raw.count())
price_cast = blank("price").cast("decimal(18,2)")
freight_cast = blank("freight_value").cast("decimal(18,2)")
negative_money = int(items_raw.select(price_cast.alias("price"), freight_cast.alias("freight")).where(
    (F.col("price") < 0) | (F.col("freight") < 0)
).count())
items = items_raw.select(
    blank("order_id").alias("order_id"),
    blank("order_item_id").alias("order_item_id"),
    blank("product_id").alias("product_id"),
    blank("seller_id").alias("seller_id"),
    parse_ts("shipping_limit_date").alias("shipping_limit_date"),
    money("price").alias("price"),
    money("freight_value").alias("freight_value"),
)
items, items_rejected = reject_blank_keys(items, ["order_id", "order_item_id"])
item_cols = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "shipping_limit_date",
    "price",
    "freight_value",
]
items, items_dropped = keep_max_lex(items, ["order_id", "order_item_id"], item_cols)
publish(silver_name("order_items"), f"{bronze}.order_items", items, items_rows, items_rejected, items_dropped)
if negative_money:
    print_warn("order_items.negative_money", f"rows_set_null={negative_money}")

# COMMAND ----------

pay_raw = bronze_table("order_payments")
pay_rows = int(pay_raw.count())
pay_value = blank("payment_value").cast("decimal(18,2)")
negative_pay = int(pay_raw.select(pay_value.alias("payment_value")).where(F.col("payment_value") < 0).count())
pay_type = F.lower(blank("payment_type"))
payments = pay_raw.select(
    blank("order_id").alias("order_id"),
    blank("payment_sequential").alias("payment_sequential"),
    F.when(pay_type.isNull() | (pay_type == "not_defined"), F.lit(None)).otherwise(pay_type).alias("payment_type"),
    parse_int("payment_installments").alias("payment_installments"),
    F.when(pay_value < 0, F.lit(None).cast("decimal(18,2)")).otherwise(pay_value).alias("payment_value"),
)
payments, pay_rejected = reject_blank_keys(payments, ["order_id", "payment_sequential"])
pay_cols = ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"]
payments, pay_dropped = keep_max_lex(payments, ["order_id", "payment_sequential"], pay_cols)
publish(silver_name("order_payments"), f"{bronze}.order_payments", payments, pay_rows, pay_rejected, pay_dropped)
if negative_pay:
    print_warn("order_payments.negative_value", f"rows_set_null={negative_pay}")

# COMMAND ----------

products_raw = bronze_table("products")
product_rows = int(products_raw.count())
products = products_raw.select(
    blank("product_id").alias("product_id"),
    blank("product_category_name").alias("product_category_name"),
    parse_int("product_name_lenght").alias("product_name_lenght"),
    parse_int("product_description_lenght").alias("product_description_lenght"),
    parse_int("product_photos_qty").alias("product_photos_qty"),
    parse_int("product_weight_g").alias("product_weight_g"),
    parse_int("product_length_cm").alias("product_length_cm"),
    parse_int("product_height_cm").alias("product_height_cm"),
    parse_int("product_width_cm").alias("product_width_cm"),
)
products, product_rejected = reject_blank_keys(products, ["product_id"])
product_cols = [
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]
products, product_dropped = keep_max_lex(products, ["product_id"], product_cols)
english = spark.table(silver_name("category_translation")).select(
    "product_category_name",
    F.col("product_category_name_english").alias("category_name_en"),
)
before_products = int(products.count())
products = products.join(english, "product_category_name", "left")
after_products = int(products.count())
if after_products != before_products:
    print_warn("products.translation_fanout", f"before={before_products} after={after_products}")
publish(silver_name("products"), f"{bronze}.products", products, product_rows, product_rejected, product_dropped)

# COMMAND ----------

def attach_place(df: DataFrame, zip_col: str, city_col: str, state_col: str) -> DataFrame:
    zips = spark.table(silver_name("geolocation_zip")).select(
        F.col("zip_prefix").alias("_zip"),
        F.col("lat").alias("_zlat"),
        F.col("lng").alias("_zlng"),
    )
    cities = spark.table(silver_name("geolocation_city")).select(
        F.col("city_norm").alias("_city"),
        F.col("state_code").alias("_state"),
        F.col("lat").alias("_clat"),
        F.col("lng").alias("_clng"),
    )
    regions = spark.table(silver_name("state_region")).select(
        F.col("state_code").alias("_region_state"),
        "region_id",
        "region_code",
        "region_name",
    )
    before = int(df.count())
    out = df.join(zips, F.col(zip_col) == F.col("_zip"), "left")
    out = out.join(
        cities,
        (F.col(city_col) == F.col("_city")) & (F.col(state_col) == F.col("_state")),
        "left",
    )
    out = out.withColumn(
        "lat",
        F.when(F.col("_zlat").isNotNull(), F.col("_zlat")).otherwise(F.col("_clat")),
    ).withColumn(
        "lng",
        F.when(F.col("_zlat").isNotNull(), F.col("_zlng")).otherwise(F.col("_clng")),
    ).withColumn(
        "geo_match_level",
        F.when(F.col("_zlat").isNotNull(), F.lit("zip"))
        .when(F.col("_clat").isNotNull(), F.lit("city"))
        .otherwise(F.lit("none")),
    )
    out = out.join(regions, F.col(state_col) == F.col("_region_state"), "left")
    after = int(out.count())
    if after != before:
        print_warn("geo_join.fanout", f"before={before} after={after}")
    drop_cols = ["_zip", "_zlat", "_zlng", "_city", "_state", "_clat", "_clng", "_region_state"]
    return out.drop(*drop_cols)


customers_raw = bronze_table("customers")
customer_rows = int(customers_raw.count())
customers = customers_raw.select(
    blank("customer_id").alias("customer_id"),
    blank("customer_unique_id").alias("customer_unique_id"),
    blank("customer_zip_code_prefix").alias("customer_zip_code_prefix"),
    city_norm("customer_city").alias("customer_city"),
    F.upper(blank("customer_state")).alias("customer_state"),
)
customers, customer_rejected = reject_blank_keys(customers, ["customer_id"])
customer_cols = [
    "customer_id",
    "customer_unique_id",
    "customer_zip_code_prefix",
    "customer_city",
    "customer_state",
]
customers, customer_dropped = keep_max_lex(customers, ["customer_id"], customer_cols)
customers = attach_place(customers, "customer_zip_code_prefix", "customer_city", "customer_state")
publish(
    silver_name("customers"),
    f"{bronze}.customers",
    customers,
    customer_rows,
    customer_rejected,
    customer_dropped,
)

sellers_raw = bronze_table("sellers")
seller_rows = int(sellers_raw.count())
sellers = sellers_raw.select(
    blank("seller_id").alias("seller_id"),
    blank("seller_zip_code_prefix").alias("seller_zip_code_prefix"),
    city_norm("seller_city").alias("seller_city"),
    F.upper(blank("seller_state")).alias("seller_state"),
)
sellers, seller_rejected = reject_blank_keys(sellers, ["seller_id"])
seller_cols = ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]
sellers, seller_dropped = keep_max_lex(sellers, ["seller_id"], seller_cols)
sellers = attach_place(sellers, "seller_zip_code_prefix", "seller_city", "seller_state")
publish(silver_name("sellers"), f"{bronze}.sellers", sellers, seller_rows, seller_rejected, seller_dropped)

# COMMAND ----------

reviews_raw = bronze_table("order_reviews")
review_rows = int(reviews_raw.count())
score = blank("review_score").cast("int")
bad_score = int(
    reviews_raw.select(score.alias("review_score"))
    .where(F.col("review_score").isNotNull() & ~F.col("review_score").between(1, 5))
    .count()
)
reviews = reviews_raw.select(
    blank("review_id").alias("review_id"),
    blank("order_id").alias("order_id"),
    F.when(score.between(1, 5), score).otherwise(F.lit(None).cast("int")).alias("review_score"),
    blank("review_comment_title").alias("review_comment_title"),
    blank("review_comment_message").alias("review_comment_message"),
    parse_ts("review_creation_date").alias("review_creation_date"),
    parse_ts("review_answer_timestamp").alias("review_answer_timestamp"),
)
reviews, review_rejected = reject_blank_keys(reviews, ["review_id", "order_id"])
review_window = Window.partitionBy("review_id", "order_id").orderBy(
    F.col("review_answer_timestamp").desc_nulls_last(),
    F.col("review_creation_date").desc_nulls_last(),
)
ranked_reviews = reviews.withColumn("_rn", F.row_number().over(review_window))
review_dropped = int(ranked_reviews.where(F.col("_rn") > 1).count())
reviews = ranked_reviews.where(F.col("_rn") == 1).drop("_rn")
conflict = (
    reviews_raw.select(
        blank("review_id").alias("review_id"),
        blank("order_id").alias("order_id"),
        blank("review_score").alias("review_score"),
        blank("review_comment_title").alias("review_comment_title"),
        blank("review_comment_message").alias("review_comment_message"),
        blank("review_creation_date").alias("review_creation_date"),
        blank("review_answer_timestamp").alias("review_answer_timestamp"),
    )
    .where(F.col("review_id").isNotNull() & F.col("order_id").isNotNull())
    .groupBy("review_id", "order_id")
    .agg(F.countDistinct(
        F.concat_ws(
            "\u001f",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        )
    ).alias("n_values"))
    .where(F.col("n_values") > 1)
    .count()
)
publish(
    silver_name("order_reviews"),
    f"{bronze}.order_reviews",
    reviews,
    review_rows,
    review_rejected,
    review_dropped,
)
print_warn("order_reviews.conflicting_keys", f"groups={conflict}")
if bad_score:
    print_warn("order_reviews.score_out_of_range", f"rows_set_null={bad_score}")

dedup_window = Window.partitionBy("order_id").orderBy(
    F.col("review_answer_timestamp").desc_nulls_last(),
    F.col("review_creation_date").desc_nulls_last(),
    F.col("review_id").asc(),
)
dedup_source = spark.table(silver_name("order_reviews"))
dedup_rows = int(dedup_source.count())
dedup = (
    dedup_source.withColumn("_rn", F.row_number().over(dedup_window))
    .where(F.col("_rn") == 1)
    .drop("_rn")
)
dedup_kept = int(dedup.count())
items_for_type = spark.table(silver_name("order_items")).select("order_id", "seller_id")
review_orders = dedup.groupBy("review_id").agg(F.countDistinct("order_id").alias("_n_orders"))
review_sellers = (
    dedup.select("review_id", "order_id")
    .join(items_for_type, "order_id", "left")
    .groupBy("review_id")
    .agg(F.countDistinct("seller_id").alias("_n_sellers"))
)
dedup = (
    dedup.join(review_orders, "review_id", "left")
    .join(review_sellers, "review_id", "left")
    .withColumn(
        "shared_review_type",
        F.when(F.col("_n_orders") <= 1, F.lit("none"))
        .when(F.col("_n_sellers") == 1, F.lit("same_seller"))
        .otherwise(F.lit("cross_seller")),
    )
    .drop("_n_orders", "_n_sellers")
)
publish(
    silver_name("order_reviews_dedup"),
    f"{silver}.order_reviews",
    dedup,
    dedup_rows,
    0,
    dedup_rows - dedup_kept,
)

# COMMAND ----------

deals_raw = bronze_table("closed_deals")
deal_rows = int(deals_raw.count())
deals = deals_raw.select(
    blank("mql_id").alias("mql_id"),
    blank("seller_id").alias("seller_id"),
    blank("sdr_id").alias("sdr_id"),
    blank("sr_id").alias("sr_id"),
    parse_ts("won_date").alias("won_date"),
    blank("business_segment").alias("business_segment"),
    blank("lead_type").alias("lead_type"),
    blank("lead_behaviour_profile").alias("lead_behaviour_profile"),
    blank("has_company").alias("has_company"),
    blank("has_gtin").alias("has_gtin"),
    blank("average_stock").alias("average_stock"),
    blank("business_type").alias("business_type"),
    blank("declared_product_catalog_size").alias("declared_product_catalog_size"),
    blank("declared_monthly_revenue").alias("declared_monthly_revenue"),
)
deal_cols = deals.columns
deals = deals.dropDuplicates(deal_cols)
deal_loaded = int(deals.count())
publish(
    silver_name("closed_deals"),
    f"{bronze}.closed_deals",
    deals,
    deal_rows,
    0,
    deal_rows - deal_loaded,
)

mql_raw = bronze_table("marketing_qualified_leads")
mql_rows = int(mql_raw.count())
mql = mql_raw.select(
    blank("mql_id").alias("mql_id"),
    parse_ts("first_contact_date").alias("first_contact_date"),
    blank("landing_page_id").alias("landing_page_id"),
    blank("origin").alias("origin"),
)
mql, mql_rejected = reject_blank_keys(mql, ["mql_id"])
mql, mql_dropped = keep_max_lex(
    mql,
    ["mql_id"],
    ["mql_id", "first_contact_date", "landing_page_id", "origin"],
)
publish(
    silver_name("marketing_qualified_leads"),
    f"{bronze}.marketing_qualified_leads",
    mql,
    mql_rows,
    mql_rejected,
    mql_dropped,
)
