-- operator: drill-down
-- question: Which month stands out for negative reviews along year, quarter, month, day?
-- requirement: R25
-- tables: gold.fact_order, gold.dim_date

-- Run after USE CATALOG olist_catalog.
-- Marketplace KPI: keep cross_seller. One row per purchase day. Drill the date columns.

SELECT
  d.year,
  d.quarter,
  d.month,
  d.day_of_month,
  d.full_date,
  SUM(CASE WHEN o.negative_review_flag = 1 THEN 1 ELSE 0 END) AS negative_orders,
  SUM(CASE WHEN o.negative_review_flag IS NOT NULL THEN 1 ELSE 0 END) AS reviewed_orders,
  CASE
    WHEN SUM(CASE WHEN o.negative_review_flag IS NOT NULL THEN 1 ELSE 0 END) > 0
      THEN SUM(CASE WHEN o.negative_review_flag = 1 THEN 1 ELSE 0 END)
        / SUM(CASE WHEN o.negative_review_flag IS NOT NULL THEN 1 ELSE 0 END)
  END AS negative_review_rate
FROM gold.fact_order AS o
INNER JOIN gold.dim_date AS d
  ON o.purchase_date_key = d.date_key
WHERE d.date_key <> -1
GROUP BY d.year, d.quarter, d.month, d.day_of_month, d.full_date
ORDER BY d.full_date;
