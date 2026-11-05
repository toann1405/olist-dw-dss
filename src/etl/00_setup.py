# Databricks notebook source
"""Create schemas and Delta tables for the Phase 3 cloud ETL.

The SQL below is the same text as src/sql/ddl/. It is inlined so a serverless
job does not need a Workspace file path. Placeholders are filled from widgets.
"""

# COMMAND ----------

from pyspark.sql import SparkSession

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


spark = _spark()
catalog = widget("uc_catalog", "olist_catalog")
bronze = widget("bronze_schema", "bronze")
silver = widget("silver_schema", "silver")
gold = widget("gold_schema", "gold")
dss = widget("dss_schema", "dss")

DDL = """
-- Schemas for the Phase 3 cloud ETL. {catalog} is replaced by the setup widget.
-- No business tables in {dss}.

CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{bronze}`;
CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{silver}`;
CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{gold}`;
CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{dss}`;


-- Bronze: one current CSV image per table. Business columns stay STRING.
-- {catalog} and {bronze} are replaced by setup widgets.

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`orders` (
  order_id STRING,
  customer_id STRING,
  order_status STRING,
  order_purchase_timestamp STRING,
  order_approved_at STRING,
  order_delivered_carrier_date STRING,
  order_delivered_customer_date STRING,
  order_estimated_delivery_date STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`order_items` (
  order_id STRING,
  order_item_id STRING,
  product_id STRING,
  seller_id STRING,
  shipping_limit_date STRING,
  price STRING,
  freight_value STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`order_reviews` (
  review_id STRING,
  order_id STRING,
  review_score STRING,
  review_comment_title STRING,
  review_comment_message STRING,
  review_creation_date STRING,
  review_answer_timestamp STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`order_payments` (
  order_id STRING,
  payment_sequential STRING,
  payment_type STRING,
  payment_installments STRING,
  payment_value STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`customers` (
  customer_id STRING,
  customer_unique_id STRING,
  customer_zip_code_prefix STRING,
  customer_city STRING,
  customer_state STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`sellers` (
  seller_id STRING,
  seller_zip_code_prefix STRING,
  seller_city STRING,
  seller_state STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`products` (
  product_id STRING,
  product_category_name STRING,
  product_name_lenght STRING,
  product_description_lenght STRING,
  product_photos_qty STRING,
  product_weight_g STRING,
  product_length_cm STRING,
  product_height_cm STRING,
  product_width_cm STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`geolocation` (
  geolocation_zip_code_prefix STRING,
  geolocation_lat STRING,
  geolocation_lng STRING,
  geolocation_city STRING,
  geolocation_state STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`category_translation` (
  product_category_name STRING,
  product_category_name_english STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`closed_deals` (
  mql_id STRING,
  seller_id STRING,
  sdr_id STRING,
  sr_id STRING,
  won_date STRING,
  business_segment STRING,
  lead_type STRING,
  lead_behaviour_profile STRING,
  has_company STRING,
  has_gtin STRING,
  average_stock STRING,
  business_type STRING,
  declared_product_catalog_size STRING,
  declared_monthly_revenue STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`marketing_qualified_leads` (
  mql_id STRING,
  first_contact_date STRING,
  landing_page_id STRING,
  origin STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{bronze}`.`state_region` (
  state_id STRING,
  state_code STRING,
  state_name STRING,
  region_id STRING,
  region_code STRING,
  region_name STRING,
  _ingest_ts TIMESTAMP,
  _source_file STRING
) USING DELTA;


-- Silver typed tables. {catalog} and {silver} are replaced by setup widgets.

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`state_region` (
  state_id STRING,
  state_code STRING NOT NULL,
  state_name STRING,
  region_id STRING,
  region_code STRING,
  region_name STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`category_translation` (
  product_category_name STRING NOT NULL,
  product_category_name_english STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`geolocation_zip` (
  zip_prefix STRING NOT NULL,
  lat DOUBLE,
  lng DOUBLE,
  city_name STRING,
  state_code STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`geolocation_city` (
  city_norm STRING NOT NULL,
  state_code STRING NOT NULL,
  lat DOUBLE,
  lng DOUBLE
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`orders` (
  order_id STRING NOT NULL,
  customer_id STRING,
  order_status STRING,
  order_purchase_timestamp TIMESTAMP,
  raw_approved_at TIMESTAMP,
  raw_delivered_carrier_date TIMESTAMP,
  raw_delivered_customer_date TIMESTAMP,
  raw_estimated_delivery_date TIMESTAMP,
  order_approved_at TIMESTAMP,
  order_delivered_carrier_date TIMESTAMP,
  order_delivered_customer_date TIMESTAMP,
  order_estimated_delivery_date TIMESTAMP,
  ts_inversion_flag INT NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`order_items` (
  order_id STRING NOT NULL,
  order_item_id STRING NOT NULL,
  product_id STRING,
  seller_id STRING,
  shipping_limit_date TIMESTAMP,
  price DECIMAL(18, 2),
  freight_value DECIMAL(18, 2)
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`order_payments` (
  order_id STRING NOT NULL,
  payment_sequential STRING NOT NULL,
  payment_type STRING,
  payment_installments INT,
  payment_value DECIMAL(18, 2)
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`products` (
  product_id STRING NOT NULL,
  product_category_name STRING,
  product_name_lenght INT,
  product_description_lenght INT,
  product_photos_qty INT,
  product_weight_g INT,
  product_length_cm INT,
  product_height_cm INT,
  product_width_cm INT,
  category_name_en STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`customers` (
  customer_id STRING NOT NULL,
  customer_unique_id STRING,
  customer_zip_code_prefix STRING,
  customer_city STRING,
  customer_state STRING,
  lat DOUBLE,
  lng DOUBLE,
  geo_match_level STRING NOT NULL,
  region_id STRING,
  region_code STRING,
  region_name STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`sellers` (
  seller_id STRING NOT NULL,
  seller_zip_code_prefix STRING,
  seller_city STRING,
  seller_state STRING,
  lat DOUBLE,
  lng DOUBLE,
  geo_match_level STRING NOT NULL,
  region_id STRING,
  region_code STRING,
  region_name STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`order_reviews` (
  review_id STRING NOT NULL,
  order_id STRING NOT NULL,
  review_score INT,
  review_comment_title STRING,
  review_comment_message STRING,
  review_creation_date TIMESTAMP,
  review_answer_timestamp TIMESTAMP
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`order_reviews_dedup` (
  review_id STRING NOT NULL,
  order_id STRING NOT NULL,
  review_score INT,
  review_comment_title STRING,
  review_comment_message STRING,
  review_creation_date TIMESTAMP,
  review_answer_timestamp TIMESTAMP,
  shared_review_type STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`closed_deals` (
  mql_id STRING,
  seller_id STRING,
  sdr_id STRING,
  sr_id STRING,
  won_date TIMESTAMP,
  business_segment STRING,
  lead_type STRING,
  lead_behaviour_profile STRING,
  has_company STRING,
  has_gtin STRING,
  average_stock STRING,
  business_type STRING,
  declared_product_catalog_size STRING,
  declared_monthly_revenue STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS `{catalog}`.`{silver}`.`marketing_qualified_leads` (
  mql_id STRING NOT NULL,
  first_contact_date TIMESTAMP,
  landing_page_id STRING,
  origin STRING
) USING DELTA;


-- Append-only load log. Ten columns from SPEC section 6. No MERGE.

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`etl_audit` (
  audit_id BIGINT NOT NULL,
  run_id STRING NOT NULL,
  layer STRING NOT NULL,
  target_table STRING NOT NULL,
  source_name STRING NOT NULL,
  rows_read BIGINT NOT NULL,
  rows_loaded BIGINT NOT NULL,
  rows_rejected BIGINT NOT NULL,
  rows_unknown_fk BIGINT,
  loaded_at TIMESTAMP NOT NULL
) USING DELTA
COMMENT 'One appended row per target table per run_id';


-- Gold dimensions. Unknown member -1 is inserted by the dims notebook, not here.
-- {catalog} and {gold} are replaced by setup widgets.

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`dim_date` (
  date_key INT NOT NULL COMMENT 'yyyyMMdd. Unknown member is -1',
  full_date DATE COMMENT 'Calendar date. Null only on member -1',
  year INT COMMENT 'Year of full_date',
  quarter INT COMMENT 'Quarter 1-4',
  month INT COMMENT 'Month 1-12',
  day_of_month INT COMMENT 'Day of month',
  day_of_week INT COMMENT 'Spark dayofweek. 1 = Sunday',
  is_weekend INT COMMENT '1 when day_of_week is 1 or 7. Null on member -1',
  month_key INT COMMENT 'yyyyMM link to dim_month'
) USING DELTA
COMMENT 'Role-playing date dimension. One row per calendar day in the observed range';

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`dim_month` (
  month_key INT NOT NULL COMMENT 'yyyyMM. Unknown member is -1',
  year INT COMMENT 'Year',
  quarter INT COMMENT 'Quarter 1-4',
  month INT COMMENT 'Month 1-12',
  year_month STRING NOT NULL COMMENT 'yyyy-MM label. Unknown on member -1'
) USING DELTA
COMMENT 'Shrunken month dimension taken from dim_date';

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`dim_customer` (
  customer_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
  customer_unique_id STRING COMMENT 'Natural key of the person. Null on member -1'
) USING DELTA
COMMENT 'One row per customer_unique_id. Address stays on fact_order';

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`dim_seller` (
  seller_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
  seller_id STRING COMMENT 'Natural key. Null on member -1',
  effective_from DATE COMMENT 'SCD2-ready constant 1900-01-01. Null on member -1',
  effective_to DATE COMMENT 'Null while the single current row is open',
  is_current INT COMMENT '1 on a real seller. Null on member -1',
  zip_prefix STRING COMMENT 'Seller zip prefix',
  city_name STRING COMMENT 'Normalized city',
  state_code STRING COMMENT 'Seller state',
  region_id STRING COMMENT 'IBGE region id',
  region_code STRING COMMENT 'IBGE region code',
  region_name STRING COMMENT 'IBGE region name',
  has_closed_deal INT COMMENT '1 when at least one closed deal exists',
  mql_id STRING COMMENT 'Earliest won deal. Null when the seller has no deal',
  sdr_id STRING COMMENT 'From the chosen deal',
  sr_id STRING COMMENT 'From the chosen deal',
  won_date DATE COMMENT 'Date portion of the chosen deal won_date',
  business_segment STRING COMMENT 'Null when there is no deal. Unknown only on member -1',
  lead_type STRING COMMENT 'From the chosen deal',
  business_type STRING COMMENT 'From the chosen deal',
  lead_behaviour_profile STRING COMMENT 'From the chosen deal',
  has_company STRING COMMENT 'Source string from the chosen deal',
  has_gtin STRING COMMENT 'Source string from the chosen deal',
  average_stock STRING COMMENT 'Source string from the chosen deal',
  declared_product_catalog_size STRING COMMENT 'Source string from the chosen deal',
  declared_monthly_revenue STRING COMMENT 'Source string from the chosen deal'
) USING DELTA
COMMENT 'One current row per seller_id. SCD2 columns are present. History is not built';

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`dim_product` (
  product_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
  product_id STRING COMMENT 'Natural key. Null on member -1',
  category_pt STRING NOT NULL COMMENT 'Portuguese category or Unknown',
  category_en STRING NOT NULL COMMENT 'English category, else Portuguese name, else Unknown',
  category_group STRING NOT NULL COMMENT 'Eight groups plus Unknown',
  weight_g INT COMMENT 'Weight in grams',
  length_cm INT COMMENT 'Length in centimeters',
  height_cm INT COMMENT 'Height in centimeters',
  width_cm INT COMMENT 'Width in centimeters',
  name_length INT COMMENT 'Renamed from product_name_lenght',
  description_length INT COMMENT 'Renamed from product_description_lenght',
  photos_qty INT COMMENT 'Photo count',
  volume_cm3 INT COMMENT 'length * height * width when all three exist',
  size_band STRING NOT NULL COMMENT 'bulky, medium, small, or Unknown'
) USING DELTA
COMMENT 'One row per product_id. A missing category keeps a positive key';

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`dim_order_status` (
  order_status_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
  order_status STRING NOT NULL COMMENT 'Lowercase source status. Unknown on member -1'
) USING DELTA
COMMENT 'Distinct order statuses. No guessed shipped, approved, or created value';

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`dim_payment_type` (
  payment_type_key BIGINT NOT NULL COMMENT 'Surrogate. Unknown member is -1',
  payment_type STRING NOT NULL COMMENT 'Lowercase payment type. Unknown on member -1'
) USING DELTA
COMMENT 'Distinct non-null payment types. not_defined does not become a member';


-- Gold facts. Placeholders {catalog} and {gold} are replaced by setup widgets.
-- grain: one row = one order item (order_id, order_item_id)

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`fact_order_item` (
  order_id STRING NOT NULL COMMENT 'Degenerate grain key',
  order_item_id STRING NOT NULL COMMENT 'Degenerate grain key',
  purchase_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when purchase is null',
  shipping_limit_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when the limit is null',
  customer_key BIGINT NOT NULL COMMENT 'FK dim_customer. -1 when the person key is missing',
  seller_key BIGINT NOT NULL COMMENT 'FK dim_seller. -1 when seller_id does not match',
  product_key BIGINT NOT NULL COMMENT 'FK dim_product. -1 when product_id does not match',
  order_status_key BIGINT NOT NULL COMMENT 'FK dim_order_status from the order',
  price DECIMAL(18, 2) COMMENT 'Item price. Not freight',
  freight_value DECIMAL(18, 2) COMMENT 'Item freight. Not part of seller gmv',
  seller_ship_late_flag INT COMMENT '0, 1, or null. Do not sum across items of different orders',
  seller_handling_days DOUBLE COMMENT 'Official carrier minus official approved, in days',
  delivery_days DOUBLE COMMENT 'Copied from the order',
  delay_days DOUBLE COMMENT 'Copied from the order. Do not sum',
  late_delivery_flag INT COMMENT 'Copy of fact_order.late_flag. Do not sum',
  distance_km DOUBLE COMMENT 'Haversine kilometers. Null when a coordinate is missing'
) USING DELTA
COMMENT 'grain: one row = one order item (order_id, order_item_id)';

-- grain: one row = one order
CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`fact_order` (
  order_id STRING NOT NULL COMMENT 'Grain',
  purchase_date_key INT NOT NULL COMMENT 'FK dim_date',
  approved_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official approved is null',
  delivered_carrier_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official carrier is null',
  delivered_customer_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official customer is null',
  estimated_date_key INT NOT NULL COMMENT 'FK dim_date. -1 when official estimated is null',
  customer_key BIGINT NOT NULL COMMENT 'FK dim_customer via customer_unique_id',
  customer_zip_prefix STRING COMMENT 'Zip of this order customer_id',
  customer_city_name STRING COMMENT 'Normalized city of this order',
  customer_state_code STRING COMMENT 'State of this order',
  customer_region_id STRING COMMENT 'IBGE region of this order',
  customer_region_code STRING COMMENT 'IBGE region code of this order',
  customer_region_name STRING COMMENT 'IBGE region name of this order',
  order_status_key BIGINT NOT NULL COMMENT 'FK dim_order_status',
  payment_type_key BIGINT NOT NULL COMMENT 'FK dim_payment_type. Primary type, else -1',
  items_value DECIMAL(18, 2) NOT NULL COMMENT 'Sum of price for every status. 0 when the order has no items',
  freight_total DECIMAL(18, 2) NOT NULL COMMENT 'Sum of freight. Not subtracted from items_value',
  payment_total DECIMAL(18, 2) NOT NULL COMMENT 'Sum of every payment_value. 0 when none',
  n_items INT NOT NULL COMMENT 'Item rows. 0 when the order has no items',
  n_sellers INT NOT NULL COMMENT 'Distinct sellers. 0 when the order has no items',
  delivery_days DOUBLE COMMENT 'Official customer minus purchase, in days',
  estimated_days DOUBLE COMMENT 'Date diff of official estimated and purchase',
  delay_days DOUBLE COMMENT 'Date diff of official customer and official estimated',
  late_flag INT COMMENT '1 when delay_days > 0. Null for canceled, unavailable, or a missing date',
  review_score INT COMMENT 'Score from order_reviews_dedup. Null when the order has no review',
  shared_review_type STRING COMMENT 'none, same_seller, or cross_seller. Null when there is no review',
  negative_review_flag INT COMMENT '1 when score <= 2. Null when there is no score',
  bad_experience_flag INT COMMENT 'Order-level flag. Not copied onto the seller-month snapshot',
  ts_inversion_flag INT NOT NULL COMMENT 'Copied from silver.orders'
) USING DELTA
COMMENT 'grain: one row = one order';

-- grain: one row = one seller x one month with at least one item
CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`fact_seller_monthly` (
  seller_key BIGINT NOT NULL COMMENT 'FK dim_seller and grain',
  month_key INT NOT NULL COMMENT 'FK dim_month. Purchase month',
  seller_id STRING NOT NULL COMMENT 'Degenerate seller id',
  year_month STRING NOT NULL COMMENT 'yyyy-MM of the purchase month',
  n_orders_placed INT NOT NULL COMMENT 'Distinct orders, every status. Not additive across sellers',
  n_orders_valid INT NOT NULL COMMENT 'Distinct orders excluding canceled and unavailable',
  n_items_placed INT NOT NULL COMMENT 'Item rows, every status',
  n_items_valid INT NOT NULL COMMENT 'Item rows excluding canceled and unavailable',
  gmv DECIMAL(18, 2) NOT NULL COMMENT 'Sum of price excluding canceled and unavailable. Freight is excluded',
  aov DOUBLE COMMENT 'gmv / n_orders_valid when the denominator is positive',
  late_ship_count INT NOT NULL COMMENT 'Items with seller_ship_late_flag = 1',
  late_ship_eligible INT NOT NULL COMMENT 'Items with a non-null ship-late flag',
  late_ship_rate DOUBLE COMMENT 'late_ship_count / late_ship_eligible',
  late_delivery_count INT NOT NULL COMMENT 'Distinct orders with late_flag = 1',
  late_delivery_eligible INT NOT NULL COMMENT 'Distinct orders with a non-null late_flag',
  late_delivery_rate DOUBLE COMMENT 'late_delivery_count / late_delivery_eligible',
  review_score_sum INT NOT NULL COMMENT 'Sum of scores on seller-eligible orders',
  review_count INT NOT NULL COMMENT 'Distinct seller-eligible orders with a score',
  avg_review DOUBLE COMMENT 'review_score_sum / review_count',
  negative_review_count INT NOT NULL COMMENT 'Seller-eligible orders with a negative score',
  negative_review_eligible INT NOT NULL COMMENT 'Same denominator as review_count',
  negative_review_rate DOUBLE COMMENT 'negative_review_count / negative_review_eligible',
  bad_experience_count INT NOT NULL COMMENT 'Seller bad review or late_flag = 1',
  bad_experience_eligible INT NOT NULL COMMENT 'Seller review set or a non-null late_flag',
  bad_experience_rate DOUBLE COMMENT 'bad_experience_count / bad_experience_eligible',
  cancel_count INT NOT NULL COMMENT 'Distinct canceled or unavailable orders',
  cancel_eligible INT NOT NULL COMMENT 'Equals n_orders_placed',
  cancel_rate DOUBLE COMMENT 'cancel_count / n_orders_placed',
  handling_days_sum DOUBLE NOT NULL COMMENT 'Sum of non-null seller_handling_days',
  handling_days_count INT NOT NULL COMMENT 'Items with non-null handling days',
  avg_handling_days DOUBLE COMMENT 'handling_days_sum / handling_days_count'
) USING DELTA
COMMENT 'grain: one row = one seller x one purchase month with at least one item';

ALTER TABLE `{catalog}`.`{gold}`.`fact_order_item` DROP CONSTRAINT IF EXISTS chk_foi_money;
ALTER TABLE `{catalog}`.`{gold}`.`fact_order_item` ADD CONSTRAINT chk_foi_money CHECK (
  (price IS NULL OR price >= 0) AND (freight_value IS NULL OR freight_value >= 0)
);

ALTER TABLE `{catalog}`.`{gold}`.`fact_order_item` DROP CONSTRAINT IF EXISTS chk_foi_flags;
ALTER TABLE `{catalog}`.`{gold}`.`fact_order_item` ADD CONSTRAINT chk_foi_flags CHECK (
  (seller_ship_late_flag IS NULL OR seller_ship_late_flag IN (0, 1))
  AND (late_delivery_flag IS NULL OR late_delivery_flag IN (0, 1))
);

ALTER TABLE `{catalog}`.`{gold}`.`fact_order` DROP CONSTRAINT IF EXISTS chk_fo_amounts_counts;
ALTER TABLE `{catalog}`.`{gold}`.`fact_order` ADD CONSTRAINT chk_fo_amounts_counts CHECK (
  items_value >= 0 AND freight_total >= 0 AND payment_total >= 0 AND n_items >= 0 AND n_sellers >= 0
);

ALTER TABLE `{catalog}`.`{gold}`.`fact_order` DROP CONSTRAINT IF EXISTS chk_fo_review;
ALTER TABLE `{catalog}`.`{gold}`.`fact_order` ADD CONSTRAINT chk_fo_review CHECK (
  (review_score IS NULL OR review_score BETWEEN 1 AND 5)
  AND (shared_review_type IS NULL OR shared_review_type IN ('none', 'same_seller', 'cross_seller'))
  AND (
    (review_score IS NULL AND shared_review_type IS NULL)
    OR (review_score IS NOT NULL AND shared_review_type IS NOT NULL)
  )
);

ALTER TABLE `{catalog}`.`{gold}`.`fact_order` DROP CONSTRAINT IF EXISTS chk_fo_flags;
ALTER TABLE `{catalog}`.`{gold}`.`fact_order` ADD CONSTRAINT chk_fo_flags CHECK (
  (late_flag IS NULL OR late_flag IN (0, 1))
  AND (negative_review_flag IS NULL OR negative_review_flag IN (0, 1))
  AND (bad_experience_flag IS NULL OR bad_experience_flag IN (0, 1))
  AND ts_inversion_flag IN (0, 1)
);

ALTER TABLE `{catalog}`.`{gold}`.`fact_seller_monthly` DROP CONSTRAINT IF EXISTS chk_fsm_totals;
ALTER TABLE `{catalog}`.`{gold}`.`fact_seller_monthly` ADD CONSTRAINT chk_fsm_totals CHECK (
  n_orders_placed >= 1
  AND n_items_placed >= 1
  AND n_orders_valid >= 0
  AND n_orders_valid <= n_orders_placed
  AND n_items_valid >= 0
  AND n_items_valid <= n_items_placed
  AND gmv >= 0
  AND cancel_eligible = n_orders_placed
  AND ((n_orders_valid = 0 AND aov IS NULL) OR (n_orders_valid > 0 AND aov >= 0))
);

ALTER TABLE `{catalog}`.`{gold}`.`fact_seller_monthly` DROP CONSTRAINT IF EXISTS chk_fsm_num_den;
ALTER TABLE `{catalog}`.`{gold}`.`fact_seller_monthly` ADD CONSTRAINT chk_fsm_num_den CHECK (
  late_ship_count >= 0 AND late_ship_eligible >= late_ship_count
  AND late_delivery_count >= 0 AND late_delivery_eligible >= late_delivery_count
  AND negative_review_count >= 0 AND negative_review_eligible >= negative_review_count
  AND bad_experience_count >= 0 AND bad_experience_eligible >= bad_experience_count
  AND cancel_count >= 0 AND cancel_eligible >= cancel_count
  AND review_count >= 0
  AND review_score_sum >= 0
  AND handling_days_count >= 0
  AND handling_days_sum >= 0
);

ALTER TABLE `{catalog}`.`{gold}`.`fact_seller_monthly` DROP CONSTRAINT IF EXISTS chk_fsm_rates;
ALTER TABLE `{catalog}`.`{gold}`.`fact_seller_monthly` ADD CONSTRAINT chk_fsm_rates CHECK (
  (late_ship_rate IS NULL OR (late_ship_rate >= 0 AND late_ship_rate <= 1))
  AND (late_delivery_rate IS NULL OR (late_delivery_rate >= 0 AND late_delivery_rate <= 1))
  AND (negative_review_rate IS NULL OR (negative_review_rate >= 0 AND negative_review_rate <= 1))
  AND (bad_experience_rate IS NULL OR (bad_experience_rate >= 0 AND bad_experience_rate <= 1))
  AND (cancel_rate IS NULL OR (cancel_rate >= 0 AND cancel_rate <= 1))
  AND (avg_review IS NULL OR (avg_review >= 1 AND avg_review <= 5))
);

"""

# COMMAND ----------

def statements(script: str):
    filled = script.format(
        catalog=catalog,
        bronze=bronze,
        silver=silver,
        gold=gold,
        dss=dss,
    )
    chunk = []
    for line in filled.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        chunk.append(line)
        if stripped.endswith(";"):
            text = "\n".join(chunk).strip()
            chunk = []
            if text:
                yield text[:-1].strip()
    tail = "\n".join(chunk).strip()
    if tail:
        yield tail


for statement in statements(DDL):
    spark.sql(statement)

# COMMAND ----------

schemas = [row[0] for row in spark.sql(f"SHOW SCHEMAS IN `{catalog}`").collect()]
for name in (bronze, silver, gold, dss):
    if name not in schemas:
        raise RuntimeError(f"Missing schema {catalog}.{name}")
audit_cols = spark.table(f"`{catalog}`.`{gold}`.`etl_audit`").columns
print(f"schemas ok: {bronze}, {silver}, {gold}, {dss}")
print(f"etl_audit columns ({len(audit_cols)}): {audit_cols}")
if len(audit_cols) != 10:
    raise RuntimeError("gold.etl_audit must have 10 columns")
dss_tables = spark.sql(f"SHOW TABLES IN `{catalog}`.`{dss}`").collect()
if dss_tables:
    raise RuntimeError(f"Phase 3 leaves the dss schema empty, found {len(dss_tables)} tables")
print("dss schema has no tables")
