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
