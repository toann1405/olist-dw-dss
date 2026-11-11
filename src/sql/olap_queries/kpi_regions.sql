-- operator: kpi
-- question: Which seller regions can the KPI page offer?
-- requirement: R09
-- tables: gold.dim_seller
-- rates from numerator and denominator

SELECT DISTINCT s.region_name
FROM {catalog}.{gold}.dim_seller AS s
WHERE s.seller_key <> -1
  AND s.region_name IS NOT NULL
  AND s.region_name <> 'Unknown'
ORDER BY s.region_name
