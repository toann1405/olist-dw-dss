-- Append-only load log. Ten columns from SPEC section 6. No MERGE.

CREATE TABLE IF NOT EXISTS `{catalog}`.`{gold}`.`etl_audit` (
  audit_id BIGINT NOT NULL,
  run_id STRING NOT NULL,
  layer STRING NOT NULL,
  target_table STRING NOT NULL,
  source_name STRING NOT NULL,
  rows_read BIGINT NOT NULL,
  rows_loaded BIGINT NOT NULL,
  rows_rejected BIGINT NOT NULL,
  rows_unknown_fk BIGINT,
  loaded_at TIMESTAMP NOT NULL
) USING DELTA
COMMENT 'One appended row per target table per run_id';
