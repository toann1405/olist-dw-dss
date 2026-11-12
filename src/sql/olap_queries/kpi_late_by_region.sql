-- requirement: R09
-- tables: gold.fact_seller_monthly, gold.dim_month, gold.dim_seller
-- rates from numerator and denominator

SELECT
  COALESCE(s.region_name, '(không map được vùng)') AS region_name,
  SUM(f.late_ship_count) AS late_ship_count,
  SUM(f.late_ship_eligible) AS late_ship_eligible
FROM {catalog}.{gold}.fact_seller_monthly AS f
INNER JOIN {catalog}.{gold}.dim_month AS m
  ON f.month_key = m.month_key
INNER JOIN {catalog}.{gold}.dim_seller AS s
  ON f.seller_key = s.seller_key
WHERE f.seller_key <> -1
  AND m.month_key <> -1
  AND s.seller_key <> -1
  AND (s.region_name IS NULL OR s.region_name <> 'Unknown')
  AND ({p} IS NULL OR m.year_month >= {p})
  AND ({p} IS NULL OR m.year_month <= {p})
  AND ({p} IS NULL OR s.state_code = {p})
GROUP BY s.region_name
ORDER BY region_name
