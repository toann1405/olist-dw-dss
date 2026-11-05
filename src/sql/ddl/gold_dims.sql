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
