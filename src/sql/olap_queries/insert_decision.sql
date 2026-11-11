-- requirement: R37
-- tables: dss.decision_log

INSERT INTO {catalog}.{dss}.decision_log (
  decision_id, decided_at, as_of_month, policy_code,
  theta_1, theta_2, theta_3, e1, e2, e3, e_p1,
  late_ship_threshold, avg_review_threshold, r, s, min_orders,
  x_limit, n_limit, expected_bad_orders, gmv_affected_pct,
  n_sellers_flagged, note
) VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
