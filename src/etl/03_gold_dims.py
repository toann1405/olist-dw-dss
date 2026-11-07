# Databricks notebook source
"""Gold dimensions. SCD Type 1. Member -1 is inserted before business keys. No SCD2 history."""

# COMMAND ----------

# MAGIC %run ./_audit

# COMMAND ----------

# MAGIC %run ./_dq

# COMMAND ----------

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

# COMMAND ----------

CATEGORY_GROUPS = {
    "home_furniture_decor": [
        "cama_mesa_banho",
        "moveis_decoracao",
        "moveis_escritorio",
        "moveis_sala",
        "moveis_cozinha_area_de_servico_jantar_e_jardim",
        "moveis_quarto",
        "moveis_colchao_e_estofado",
        "utilidades_domesticas",
        "casa_conforto",
        "casa_conforto_2",
        "la_cuisine",
        "portateis_cozinha_e_preparadores_de_alimentos",
        "climatizacao",
        "flores",
    ],
    "health_beauty_fashion": [
        "beleza_saude",
        "perfumaria",
        "relogios_presentes",
        "fashion_bolsas_e_acessorios",
        "fashion_calcados",
        "fashion_roupa_masculina",
        "fashion_roupa_feminina",
        "fashion_roupa_infanto_juvenil",
        "fashion_underwear_e_moda_praia",
        "fashion_esporte",
        "malas_acessorios",
        "fraldas_higiene",
    ],
    "electronics_it_telephony": [
        "informatica_acessorios",
        "pcs",
        "tablets_impressao_imagem",
        "telefonia",
        "telefonia_fixa",
        "eletronicos",
        "audio",
        "cine_foto",
        "consoles_games",
        "eletrodomesticos",
        "eletrodomesticos_2",
        "portateis_casa_forno_e_cafe",
        "eletroportateis",
    ],
    "sports_leisure_toys": [
        "esporte_lazer",
        "brinquedos",
        "cool_stuff",
        "instrumentos_musicais",
        "artes",
        "artes_e_artesanato",
        "artigos_de_festas",
        "artigos_de_natal",
    ],
    "auto_tools_construction": [
        "automotivo",
        "ferramentas_jardim",
        "construcao_ferramentas_construcao",
        "construcao_ferramentas_iluminacao",
        "construcao_ferramentas_jardim",
        "construcao_ferramentas_seguranca",
        "construcao_ferramentas_ferramentas",
        "casa_construcao",
        "sinalizacao_e_seguranca",
        "agro_industria_e_comercio",
        "industria_comercio_e_negocios",
    ],
    "books_stationery_media": [
        "papelaria",
        "livros_interesse_geral",
        "livros_tecnicos",
        "livros_importados",
        "cds_dvds_musicais",
        "dvds_blu_ray",
        "musica",
    ],
    "baby_pets_food_drinks": [
        "bebes",
        "pet_shop",
        "alimentos",
        "alimentos_bebidas",
        "bebidas",
    ],
}

# COMMAND ----------

def widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name)
    text = "" if value is None else str(value).strip()
    return text or default


def align(df: DataFrame, table: str) -> DataFrame:
    return df.select(*spark.table(table).columns)


def merge_unknown(table: str, overrides: dict) -> None:
    schema = spark.table(table).schema
    values = [overrides.get(field.name) for field in schema.fields]
    frame = spark.createDataFrame([tuple(values)], schema)
    frame.createOrReplaceTempView("unknown_src")
    key = schema.fields[0].name
    spark.sql(
        f"""
        MERGE INTO {table} t
        USING unknown_src s
        ON t.{key} = -1
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    )


def assign_keys(table: str, source: DataFrame, key_col: str, natural_col: str) -> DataFrame:
    existing = (
        spark.table(table)
        .where(F.col(key_col) != -1)
        .select(F.col(natural_col).alias(natural_col), F.col(key_col).alias("_existing_key"))
    )
    max_key = spark.table(table).where(F.col(key_col) != -1).agg(F.max(key_col).alias("m")).first()["m"]
    max_key = 0 if max_key is None else int(max_key)
    joined = source.join(existing, natural_col, "left")
    is_new = F.col("_existing_key").isNull()
    ranked = joined.withColumn(
        key_col,
        F.when(~is_new, F.col("_existing_key").cast("bigint")).otherwise(
            F.lit(max_key)
            + F.row_number().over(Window.partitionBy(is_new).orderBy(F.col(natural_col).asc()))
        ),
    ).drop("_existing_key")
    return ranked


def merge_natural(table: str, frame: DataFrame, natural_col: str, update_cols: list[str]) -> None:
    align(frame, table).createOrReplaceTempView("dim_src")
    assignments = ", ".join(f"t.{column} = s.{column}" for column in update_cols)
    spark.sql(
        f"""
        MERGE INTO {table} t
        USING dim_src s
        ON t.{natural_col} = s.{natural_col}
        WHEN MATCHED THEN UPDATE SET {assignments}
        WHEN NOT MATCHED THEN INSERT *
        """
    )


def publish_dim(table: str, source_name: str, rows_read: int, rows_loaded: int) -> None:
    print_recon(table, rows_read, rows_loaded, max(rows_read - rows_loaded, 0), 0)
    append_audit(
        catalog,
        gold,
        run_id,
        "gold",
        table.split(".")[-1],
        source_name,
        rows_read,
        rows_loaded,
        0,
        None,
    )

# COMMAND ----------

catalog = widget("uc_catalog", "olist_catalog")
silver = widget("silver_schema", "silver")
gold = widget("gold_schema", "gold")
run_id = widget("run_id", "manual")


def silver_table(name: str) -> DataFrame:
    return spark.table(f"{catalog}.{silver}.{name}")


def gold_table(name: str) -> str:
    return f"{catalog}.{gold}.{name}"

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Gold dimensions. Unknown member -1 is inserted by the cells below, not by this DDL.
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.dim_date (
# MAGIC   date_key INT NOT NULL COMMENT 'yyyyMMdd. Unknown member is -1',
# MAGIC   full_date DATE COMMENT 'Calendar date. Null only on member -1',
# MAGIC   year INT COMMENT 'Year of full_date',
# MAGIC   quarter INT COMMENT 'Quarter 1-4',
# MAGIC   month INT COMMENT 'Month 1-12',
# MAGIC   day_of_month INT COMMENT 'Day of month',
# MAGIC   day_of_week INT COMMENT 'Spark dayofweek. 1 = Sunday',
# MAGIC   is_weekend INT COMMENT '1 when day_of_week is 1 or 7. Null on member -1',
# MAGIC   month_key INT COMMENT 'yyyyMM link to dim_month'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'Role-playing date dimension. One row per calendar day in the observed range';
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.dim_month (
# MAGIC   month_key INT NOT NULL COMMENT 'yyyyMM. Unknown member is -1',
# MAGIC   year INT COMMENT 'Year',
# MAGIC   quarter INT COMMENT 'Quarter 1-4',
# MAGIC   month INT COMMENT 'Month 1-12',
# MAGIC   year_month STRING NOT NULL COMMENT 'yyyy-MM label. Unknown on member -1'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'Shrunken month dimension taken from dim_date';
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.dim_customer (
# MAGIC   customer_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
# MAGIC   customer_unique_id STRING COMMENT 'Natural key of the person. Null on member -1'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'One row per customer_unique_id. Address stays on fact_order';
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.dim_seller (
# MAGIC   seller_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
# MAGIC   seller_id STRING COMMENT 'Natural key. Null on member -1',
# MAGIC   effective_from DATE COMMENT 'SCD2-ready constant 1900-01-01. Null on member -1',
# MAGIC   effective_to DATE COMMENT 'Null while the single current row is open',
# MAGIC   is_current INT COMMENT '1 on a real seller. Null on member -1',
# MAGIC   zip_prefix STRING COMMENT 'Seller zip prefix',
# MAGIC   city_name STRING COMMENT 'Normalized city',
# MAGIC   state_code STRING COMMENT 'Seller state',
# MAGIC   region_id STRING COMMENT 'IBGE region id',
# MAGIC   region_code STRING COMMENT 'IBGE region code',
# MAGIC   region_name STRING COMMENT 'IBGE region name',
# MAGIC   has_closed_deal INT COMMENT '1 when at least one closed deal exists',
# MAGIC   mql_id STRING COMMENT 'Earliest won deal. Null when the seller has no deal',
# MAGIC   sdr_id STRING COMMENT 'From the chosen deal',
# MAGIC   sr_id STRING COMMENT 'From the chosen deal',
# MAGIC   won_date DATE COMMENT 'Date portion of the chosen deal won_date',
# MAGIC   business_segment STRING COMMENT 'Null when there is no deal. Unknown only on member -1',
# MAGIC   lead_type STRING COMMENT 'From the chosen deal',
# MAGIC   business_type STRING COMMENT 'From the chosen deal',
# MAGIC   lead_behaviour_profile STRING COMMENT 'From the chosen deal',
# MAGIC   has_company STRING COMMENT 'Source string from the chosen deal',
# MAGIC   has_gtin STRING COMMENT 'Source string from the chosen deal',
# MAGIC   average_stock STRING COMMENT 'Source string from the chosen deal',
# MAGIC   declared_product_catalog_size STRING COMMENT 'Source string from the chosen deal',
# MAGIC   declared_monthly_revenue STRING COMMENT 'Source string from the chosen deal'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'One current row per seller_id. SCD2 columns are present. History is not built';
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.dim_product (
# MAGIC   product_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
# MAGIC   product_id STRING COMMENT 'Natural key. Null on member -1',
# MAGIC   category_pt STRING NOT NULL COMMENT 'Portuguese category or Unknown',
# MAGIC   category_en STRING NOT NULL COMMENT 'English category, else Portuguese name, else Unknown',
# MAGIC   category_group STRING NOT NULL COMMENT 'Eight groups plus Unknown',
# MAGIC   weight_g INT COMMENT 'Weight in grams',
# MAGIC   length_cm INT COMMENT 'Length in centimeters',
# MAGIC   height_cm INT COMMENT 'Height in centimeters',
# MAGIC   width_cm INT COMMENT 'Width in centimeters',
# MAGIC   name_length INT COMMENT 'Renamed from product_name_lenght',
# MAGIC   description_length INT COMMENT 'Renamed from product_description_lenght',
# MAGIC   photos_qty INT COMMENT 'Photo count',
# MAGIC   volume_cm3 INT COMMENT 'length * height * width when all three exist',
# MAGIC   size_band STRING NOT NULL COMMENT 'bulky, medium, small, or Unknown'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'One row per product_id. A missing category keeps a positive key';
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.dim_order_status (
# MAGIC   order_status_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
# MAGIC   order_status STRING NOT NULL COMMENT 'Lowercase source status. Unknown on member -1'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'Distinct order statuses. No guessed shipped, approved, or created value';
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.dim_payment_type (
# MAGIC   payment_type_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
# MAGIC   payment_type STRING NOT NULL COMMENT 'Lowercase payment type. Unknown on member -1'
# MAGIC ) USING DELTA
# MAGIC COMMENT 'Distinct non-null payment types. not_defined does not become a member';

# COMMAND ----------

date_parts = []
for table, column in (
    ("orders", "order_purchase_timestamp"),
    ("orders", "order_approved_at"),
    ("orders", "order_delivered_carrier_date"),
    ("orders", "order_delivered_customer_date"),
    ("orders", "order_estimated_delivery_date"),
    ("order_items", "shipping_limit_date"),
    ("order_reviews", "review_creation_date"),
    ("order_reviews", "review_answer_timestamp"),
):
    date_parts.append(silver_table(table).select(F.to_date(column).alias("full_date")))
all_dates = date_parts[0]
for part in date_parts[1:]:
    all_dates = all_dates.unionByName(part)
bounds = all_dates.where(F.col("full_date").isNotNull()).agg(
    F.min("full_date").alias("min_date"),
    F.max("full_date").alias("max_date"),
).first()
date_table = gold_table("dim_date")
merge_unknown(date_table, {"date_key": -1})
if bounds["min_date"] is not None:
    span = spark.sql(
        f"""
        SELECT explode(sequence(DATE '{bounds["min_date"]}', DATE '{bounds["max_date"]}', INTERVAL 1 DAY)) AS full_date
        """
    )
    dates = span.select(
        (F.year("full_date") * 10000 + F.month("full_date") * 100 + F.dayofmonth("full_date"))
        .cast("int")
        .alias("date_key"),
        F.col("full_date"),
        F.year("full_date").alias("year"),
        F.quarter("full_date").alias("quarter"),
        F.month("full_date").alias("month"),
        F.dayofmonth("full_date").alias("day_of_month"),
        F.dayofweek("full_date").alias("day_of_week"),
        F.when(F.dayofweek("full_date").isin(1, 7), F.lit(1)).otherwise(F.lit(0)).alias("is_weekend"),
        (F.year("full_date") * 100 + F.month("full_date")).cast("int").alias("month_key"),
    )
    date_rows = int(dates.count())
    merge_natural(
        date_table,
        dates,
        "date_key",
        ["full_date", "year", "quarter", "month", "day_of_month", "day_of_week", "is_weekend", "month_key"],
    )
else:
    date_rows = 0
publish_dim(date_table, f"{silver}.orders", date_rows, date_rows)

month_table = gold_table("dim_month")
merge_unknown(month_table, {"month_key": -1, "year_month": "Unknown"})
months = (
    spark.table(date_table)
    .where(F.col("date_key") != -1)
    .select("month_key", "year", "quarter", "month")
    .dropDuplicates(["month_key"])
    .withColumn("year_month", F.format_string("%04d-%02d", F.col("year"), F.col("month")))
)
month_rows = int(months.count())
merge_natural(month_table, months, "month_key", ["year", "quarter", "month", "year_month"])
publish_dim(month_table, f"{gold}.dim_date", month_rows, month_rows)

# COMMAND ----------

customer_table = gold_table("dim_customer")
merge_unknown(customer_table, {"customer_key": -1})
people = (
    silver_table("customers")
    .where(F.col("customer_unique_id").isNotNull())
    .select("customer_unique_id")
    .dropDuplicates(["customer_unique_id"])
)
people_rows = int(people.count())
people = assign_keys(customer_table, people, "customer_key", "customer_unique_id")
merge_natural(customer_table, people, "customer_unique_id", ["customer_unique_id"])
publish_dim(customer_table, f"{silver}.customers", people_rows, people_rows)

# COMMAND ----------

seller_table = gold_table("dim_seller")
merge_unknown(
    seller_table,
    {
        "seller_key": -1,
        "zip_prefix": "Unknown",
        "city_name": "Unknown",
        "state_code": "Unknown",
        "region_id": "Unknown",
        "region_code": "Unknown",
        "region_name": "Unknown",
        "business_segment": "Unknown",
        "lead_type": "Unknown",
        "business_type": "Unknown",
        "lead_behaviour_profile": "Unknown",
        "has_company": "Unknown",
        "has_gtin": "Unknown",
        "average_stock": "Unknown",
        "declared_product_catalog_size": "Unknown",
        "declared_monthly_revenue": "Unknown",
    },
)
deal_window = Window.partitionBy("seller_id").orderBy(
    F.col("won_date").asc_nulls_last(),
    F.col("mql_id").asc_nulls_last(),
)
deals = (
    silver_table("closed_deals")
    .where(F.col("seller_id").isNotNull())
    .withColumn("_rn", F.row_number().over(deal_window))
    .where(F.col("_rn") == 1)
    .drop("_rn")
)
sellers = silver_table("sellers").select(
    "seller_id",
    F.col("seller_zip_code_prefix").alias("zip_prefix"),
    F.col("seller_city").alias("city_name"),
    F.col("seller_state").alias("state_code"),
    "region_id",
    "region_code",
    "region_name",
)
seller_rows = int(sellers.count())
has_deal = deals.select("seller_id").dropDuplicates().withColumn("has_closed_deal", F.lit(1))
chosen = deals.select(
    "seller_id",
    "mql_id",
    "sdr_id",
    "sr_id",
    F.to_date("won_date").alias("won_date"),
    "business_segment",
    "lead_type",
    "business_type",
    "lead_behaviour_profile",
    "has_company",
    "has_gtin",
    "average_stock",
    "declared_product_catalog_size",
    "declared_monthly_revenue",
)
seller_attrs = (
    sellers.join(has_deal, "seller_id", "left")
    .join(chosen, "seller_id", "left")
    .withColumn("has_closed_deal", F.coalesce(F.col("has_closed_deal"), F.lit(0)))
    .withColumn("effective_from", F.lit("1900-01-01").cast("date"))
    .withColumn("effective_to", F.lit(None).cast("date"))
    .withColumn("is_current", F.lit(1))
)
seller_attrs = assign_keys(seller_table, seller_attrs, "seller_key", "seller_id")
merge_natural(
    seller_table,
    seller_attrs,
    "seller_id",
    [
        "seller_id",
        "effective_from",
        "effective_to",
        "is_current",
        "zip_prefix",
        "city_name",
        "state_code",
        "region_id",
        "region_code",
        "region_name",
        "has_closed_deal",
        "mql_id",
        "sdr_id",
        "sr_id",
        "won_date",
        "business_segment",
        "lead_type",
        "business_type",
        "lead_behaviour_profile",
        "has_company",
        "has_gtin",
        "average_stock",
        "declared_product_catalog_size",
        "declared_monthly_revenue",
    ],
)
publish_dim(seller_table, f"{silver}.sellers", seller_rows, seller_rows)
seller_dup = (
    spark.table(seller_table)
    .where(F.col("seller_id").isNotNull())
    .groupBy("seller_id")
    .count()
    .where(F.col("count") > 1)
    .count()
)
current_mismatch = int(
    spark.table(seller_table)
    .where(F.col("seller_id").isNotNull() & (F.col("is_current") != 1))
    .count()
)
print_warn("dim_seller.duplicate_or_not_current", f"duplicate_ids={seller_dup} not_current={current_mismatch}")

# COMMAND ----------

product_table = gold_table("dim_product")
merge_unknown(
    product_table,
    {
        "product_key": -1,
        "category_pt": "Unknown",
        "category_en": "Unknown",
        "category_group": "Unknown",
        "size_band": "Unknown",
    },
)
group_expr = F.when(F.col("product_category_name").isNull(), F.lit("Unknown"))
for group_name, names in CATEGORY_GROUPS.items():
    group_expr = group_expr.when(F.col("product_category_name").isin(names), F.lit(group_name))
group_expr = group_expr.otherwise(F.lit("services_others"))
volume = (
    F.when(
        F.col("product_length_cm").isNotNull()
        & F.col("product_height_cm").isNotNull()
        & F.col("product_width_cm").isNotNull(),
        F.col("product_length_cm") * F.col("product_height_cm") * F.col("product_width_cm"),
    )
    .otherwise(F.lit(None))
    .cast("int")
)
products = silver_table("products").select(
    "product_id",
    F.coalesce(F.col("product_category_name"), F.lit("Unknown")).alias("category_pt"),
    F.coalesce(F.col("category_name_en"), F.col("product_category_name"), F.lit("Unknown")).alias("category_en"),
    group_expr.alias("category_group"),
    F.col("product_weight_g").alias("weight_g"),
    F.col("product_length_cm").alias("length_cm"),
    F.col("product_height_cm").alias("height_cm"),
    F.col("product_width_cm").alias("width_cm"),
    F.col("product_name_lenght").alias("name_length"),
    F.col("product_description_lenght").alias("description_length"),
    F.col("product_photos_qty").alias("photos_qty"),
    volume.alias("volume_cm3"),
    "product_category_name",
)
products = products.withColumn(
    "size_band",
    F.when(
        F.col("weight_g").isNull()
        | F.col("volume_cm3").isNull()
        | (F.col("weight_g") <= 0)
        | (F.col("volume_cm3") <= 0),
        F.lit("Unknown"),
    )
    .when((F.col("weight_g") >= 10000) | (F.col("volume_cm3") >= 30000), F.lit("bulky"))
    .when((F.col("weight_g") >= 2000) | (F.col("volume_cm3") >= 8000), F.lit("medium"))
    .otherwise(F.lit("small")),
).drop("product_category_name")
product_rows = int(products.count())
products = assign_keys(product_table, products, "product_key", "product_id")
merge_natural(
    product_table,
    products,
    "product_id",
    [
        "product_id",
        "category_pt",
        "category_en",
        "category_group",
        "weight_g",
        "length_cm",
        "height_cm",
        "width_cm",
        "name_length",
        "description_length",
        "photos_qty",
        "volume_cm3",
        "size_band",
    ],
)
publish_dim(product_table, f"{silver}.products", product_rows, product_rows)
silver_products = int(silver_table("products").count())
gold_products = int(spark.table(product_table).where(F.col("product_key") != -1).count())
if silver_products != gold_products:
    print_warn("dim_product.row_count", f"silver={silver_products} gold_without_unknown={gold_products}")

# COMMAND ----------

status_table = gold_table("dim_order_status")
merge_unknown(status_table, {"order_status_key": -1, "order_status": "Unknown"})
statuses = (
    silver_table("orders")
    .where(F.col("order_status").isNotNull() & (F.col("order_status") != "Unknown"))
    .select("order_status")
    .dropDuplicates(["order_status"])
)
status_rows = int(statuses.count())
statuses = assign_keys(status_table, statuses, "order_status_key", "order_status")
merge_natural(status_table, statuses, "order_status", ["order_status"])
publish_dim(status_table, f"{silver}.orders", status_rows, status_rows)

pay_table = gold_table("dim_payment_type")
merge_unknown(pay_table, {"payment_type_key": -1, "payment_type": "Unknown"})
pay_types = (
    silver_table("order_payments")
    .where(F.col("payment_type").isNotNull() & (F.col("payment_type") != "Unknown"))
    .select("payment_type")
    .dropDuplicates(["payment_type"])
)
pay_rows = int(pay_types.count())
pay_types = assign_keys(pay_table, pay_types, "payment_type_key", "payment_type")
merge_natural(pay_table, pay_types, "payment_type", ["payment_type"])
publish_dim(pay_table, f"{silver}.order_payments", pay_rows, pay_rows)

# COMMAND ----------

for name in (
    "dim_date",
    "dim_month",
    "dim_customer",
    "dim_seller",
    "dim_product",
    "dim_order_status",
    "dim_payment_type",
):
    unknown_rows = int(spark.table(gold_table(name)).where(F.col(spark.table(gold_table(name)).columns[0]) == -1).count())
    print_warn(f"{name}.unknown_member", f"rows={unknown_rows} expected=1")
