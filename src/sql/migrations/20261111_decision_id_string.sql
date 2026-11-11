-- decision_id BIGINT -> STRING so Streamlit can store a UUID.
-- Run once on the warehouse. CREATE TABLE IF NOT EXISTS does not alter an existing table.
-- Numeric ids already stored are kept as their decimal text.
-- Replace {catalog} before running. Do not run this twice.
-- 11/11/2026: the live table had 0 rows, so this session dropped it and
-- created it again with decision_id STRING. The statements below are the
-- path for a table that already has rows.

CREATE TABLE {catalog}.dss.decision_log_uuid
USING DELTA
AS
SELECT
  CAST(decision_id AS STRING) AS decision_id,
  decided_at,
  as_of_month,
  policy_code,
  theta_1,
  theta_2,
  theta_3,
  e1,
  e2,
  e3,
  e_p1,
  late_ship_threshold,
  avg_review_threshold,
  r,
  s,
  min_orders,
  x_limit,
  n_limit,
  expected_bad_orders,
  gmv_affected_pct,
  n_sellers_flagged,
  note
FROM {catalog}.dss.decision_log;

DROP TABLE {catalog}.dss.decision_log;
ALTER TABLE {catalog}.dss.decision_log_uuid RENAME TO {catalog}.dss.decision_log;
