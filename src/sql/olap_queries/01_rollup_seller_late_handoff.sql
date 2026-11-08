-- operator: roll-up
-- question: Is late handoff a regional or a local seller problem?
-- requirement: R25
-- tables: gold.fact_order_item, gold.dim_seller

-- Run after USE CATALOG olist_catalog. Rates are recomputed from counts.
-- Null flags stay out of the denominator. Member -1 is not a place.

WITH items AS (
  SELECT
    s.region_name,
    s.state_code,
    s.city_name,
    i.seller_ship_late_flag
  FROM gold.fact_order_item AS i
  INNER JOIN gold.dim_seller AS s
    ON i.seller_key = s.seller_key
  WHERE i.seller_key <> -1
)
SELECT
  region_name,
  state_code,
  city_name,
  CASE
    WHEN GROUPING(region_name) = 1 THEN 'all'
    WHEN GROUPING(state_code) = 1 THEN 'region'
    WHEN GROUPING(city_name) = 1 THEN 'state'
    ELSE 'city'
  END AS rollup_level,
  SUM(CASE WHEN seller_ship_late_flag = 1 THEN 1 ELSE 0 END) AS late_items,
  SUM(CASE WHEN seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) AS eligible_items,
  CASE
    WHEN SUM(CASE WHEN seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) > 0
      THEN SUM(CASE WHEN seller_ship_late_flag = 1 THEN 1 ELSE 0 END)
        / SUM(CASE WHEN seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END)
  END AS late_ship_rate
FROM items
GROUP BY ROLLUP (region_name, state_code, city_name)
ORDER BY region_name, state_code, city_name;
