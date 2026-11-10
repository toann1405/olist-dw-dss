-- requirement: R34
-- tables: dss.policy_scenario

SELECT
  as_of_month,
  policy_code,
  expected_bad_orders,
  gmv_affected_pct,
  n_sellers_flagged,
  meets_x,
  meets_n,
  theta_1,
  theta_2,
  theta_3,
  min_orders,
  x_limit,
  n_limit
FROM {catalog}.{dss}.policy_scenario
ORDER BY policy_code
