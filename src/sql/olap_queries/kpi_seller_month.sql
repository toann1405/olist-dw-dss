-- operator: kpi
-- question: GMV, late handoff, and the seller negative-review rate for one purchase-month range and seller region
-- requirement: R09
-- tables: gold.fact_seller_monthly, gold.dim_month, gold.dim_seller
-- rates from numerator and denominator

SELECT
  SUM(f.gmv) AS gmv,
  SUM(f.late_ship_count) AS late_ship_count,
  SUM(f.late_ship_eligible) AS late_ship_eligible,
  CASE
    WHEN SUM(f.late_ship_eligible) > 0
      THEN SUM(f.late_ship_count) / SUM(f.late_ship_eligible)
  END AS late_ship_rate,
  SUM(f.negative_review_count) AS negative_review_count,
  SUM(f.negative_review_eligible) AS negative_review_eligible,
  CASE
    WHEN SUM(f.negative_review_eligible) > 0
      THEN SUM(f.negative_review_count) / SUM(f.negative_review_eligible)
  END AS negative_review_rate
FROM {catalog}.{gold}.fact_seller_monthly AS f
INNER JOIN {catalog}.{gold}.dim_month AS m
  ON f.month_key = m.month_key
INNER JOIN {catalog}.{gold}.dim_seller AS s
  ON f.seller_key = s.seller_key
WHERE f.seller_key <> -1
  AND m.month_key <> -1
  AND s.seller_key <> -1
  AND ({p} IS NULL OR m.year_month >= {p})
  AND ({p} IS NULL OR m.year_month <= {p})
  AND ({p} IS NULL OR s.region_name = {p})
  AND ({p} IS NULL OR s.state_code = {p})
