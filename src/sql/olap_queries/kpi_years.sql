-- operator: kpi
-- question: Which purchase years can the KPI page offer?
-- requirement: R09
-- tables: gold.dim_month
-- rates from numerator and denominator

SELECT DISTINCT m.year
FROM {catalog}.{gold}.dim_month AS m
WHERE m.month_key <> -1
  AND m.year IS NOT NULL
ORDER BY m.year
