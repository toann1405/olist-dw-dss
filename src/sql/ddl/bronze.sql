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
