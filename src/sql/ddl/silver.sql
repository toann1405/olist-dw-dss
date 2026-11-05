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
