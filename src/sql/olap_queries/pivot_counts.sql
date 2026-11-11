-- operator: pivot
-- question: Late handoff by category group and quarter, with the sample size
-- requirement: R25
-- tables: gold.fact_order_item, gold.dim_product, gold.dim_date
-- rates from numerator and denominator
-- Same population as 05_pivot_category_quarter_late.sql. Counts stay beside the rate.

SELECT
  p.category_group,
  d.quarter,
  SUM(CASE WHEN i.seller_ship_late_flag = 1 THEN 1 ELSE 0 END) AS late_items,
  SUM(CASE WHEN i.seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) AS eligible_items
FROM {catalog}.{gold}.fact_order_item AS i
INNER JOIN {catalog}.{gold}.dim_product AS p
  ON i.product_key = p.product_key
INNER JOIN {catalog}.{gold}.dim_date AS d
  ON i.purchase_date_key = d.date_key
WHERE i.seller_key <> -1
  AND p.product_key <> -1
  AND d.date_key <> -1
GROUP BY p.category_group, d.quarter
ORDER BY p.category_group, d.quarter
