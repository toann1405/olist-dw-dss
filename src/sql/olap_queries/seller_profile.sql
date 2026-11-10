-- requirement: R32
-- tables: dss.seller_risk_score, gold.dim_seller

SELECT
  r.seller_id,
  r.as_of_month,
  r.p_bad,
  r.q_bar,
  r.gmv,
  r.late_ship_rate,
  r.avg_review,
  r.n_orders_valid,
  r.model_name,
  r.trained_through_month,
  s.city_name,
  s.state_code,
  s.region_name
FROM {catalog}.{dss}.seller_risk_score AS r
LEFT JOIN {catalog}.{gold}.dim_seller AS s
  ON r.seller_key = s.seller_key
WHERE r.seller_id = {p}
