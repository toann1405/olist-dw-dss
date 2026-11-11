-- requirement: R09
-- tables: gold.dim_seller
-- rates from numerator and denominator

SELECT DISTINCT s.state_code
FROM {catalog}.{gold}.dim_seller AS s
WHERE s.seller_key <> -1
  AND s.state_code IS NOT NULL
  AND s.state_code <> 'Unknown'
  AND ({p} IS NULL OR s.region_name = {p})
ORDER BY s.state_code
