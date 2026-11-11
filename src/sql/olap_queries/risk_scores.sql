-- requirement: R32
-- tables: dss.seller_risk_score

SELECT
  seller_key,
  seller_id,
  as_of_month,
  p_bad,
  q_bar,
  gmv,
  late_ship_rate,
  avg_review,
  n_orders_valid,
  model_name,
  trained_through_month
FROM {catalog}.{dss}.seller_risk_score
WHERE n_orders_valid >= {p}
ORDER BY p_bad DESC
