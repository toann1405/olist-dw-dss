-- operator: pivot
-- question: After seeing seller state by quarter, which category groups drive late handoff by quarter?
-- requirement: R25
-- tables: gold.fact_order_item, gold.dim_product, gold.dim_date

-- Run after USE CATALOG olist_catalog.
-- Same late-handoff counts as the roll-up query, at category group x quarter, then pivoted.

WITH rates AS (
  SELECT
    p.category_group,
    d.quarter,
    SUM(CASE WHEN i.seller_ship_late_flag = 1 THEN 1 ELSE 0 END) AS late_items,
    SUM(CASE WHEN i.seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) AS eligible_items
  FROM gold.fact_order_item AS i
  INNER JOIN gold.dim_product AS p
    ON i.product_key = p.product_key
  INNER JOIN gold.dim_date AS d
    ON i.purchase_date_key = d.date_key
  WHERE i.seller_key <> -1
    AND p.product_key <> -1
    AND d.date_key <> -1
  GROUP BY p.category_group, d.quarter
),
long_rates AS (
  SELECT
    category_group,
    quarter,
    CASE
      WHEN eligible_items > 0 THEN late_items / eligible_items
    END AS late_ship_rate
  FROM rates
)
SELECT *
FROM long_rates
PIVOT (
  FIRST(late_ship_rate)
  FOR quarter IN (1 AS q1, 2 AS q2, 3 AS q3, 4 AS q4)
)
ORDER BY category_group;
