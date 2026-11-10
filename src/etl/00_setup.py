# Databricks notebook source
"""Create the four schemas and gold.etl_audit.

The Volume already exists. This notebook only checks it.
Gold dimension and fact DDL lives in the notebook that first MERGEs that table.
Bronze and Silver tables are created by those notebooks.
"""

# COMMAND ----------

def widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name)
    text = "" if value is None else str(value).strip()
    return text or default

# COMMAND ----------

catalog = widget("uc_catalog", "olist_catalog")
bronze = widget("bronze_schema", "bronze")
silver = widget("silver_schema", "silver")
gold = widget("gold_schema", "gold")
dss = widget("dss_schema", "dss")
volume_root = widget("volume_root", "/Volumes/olist_catalog/bronze/raw").rstrip("/")

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS ${uc_catalog}.${bronze_schema};
# MAGIC CREATE SCHEMA IF NOT EXISTS ${uc_catalog}.${silver_schema};
# MAGIC CREATE SCHEMA IF NOT EXISTS ${uc_catalog}.${gold_schema};
# MAGIC CREATE SCHEMA IF NOT EXISTS ${uc_catalog}.${dss_schema};

# COMMAND ----------

entries = dbutils.fs.ls(volume_root)
names = {entry.name.strip("/") for entry in entries}
missing = [name for name in ("olist", "funnel", "ref") if name not in names]
if missing:
    raise RuntimeError(
        f"Volume path {volume_root} is missing {missing}. "
        "This notebook does not create, replace, or delete the Volume."
    )
print(f"volume ok: {volume_root} ({', '.join(sorted(names))})")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Append-only load log. Ten columns from SPEC section 6. No MERGE.
# MAGIC CREATE TABLE IF NOT EXISTS ${uc_catalog}.${gold_schema}.etl_audit (
# MAGIC   audit_id BIGINT NOT NULL,
# MAGIC   run_id STRING NOT NULL,
# MAGIC   layer STRING NOT NULL,
# MAGIC   target_table STRING NOT NULL,
# MAGIC   source_name STRING NOT NULL,
# MAGIC   rows_read BIGINT NOT NULL,
# MAGIC   rows_loaded BIGINT NOT NULL,
# MAGIC   rows_rejected BIGINT NOT NULL,
# MAGIC   rows_unknown_fk BIGINT,
# MAGIC   loaded_at TIMESTAMP NOT NULL
# MAGIC ) USING DELTA
# MAGIC COMMENT 'One appended row per target table per run_id';

# COMMAND ----------

schemas = [row[0] for row in spark.sql(f"SHOW SCHEMAS IN `{catalog}`").collect()]
for name in (bronze, silver, gold, dss):
    if name not in schemas:
        raise RuntimeError(f"Missing schema {catalog}.{name}")
audit_cols = spark.table(f"`{catalog}`.`{gold}`.`etl_audit`").columns
print(f"schemas ok: {bronze}, {silver}, {gold}, {dss}")
print(f"etl_audit columns ({len(audit_cols)}): {audit_cols}")
if len(audit_cols) != 10:
    raise RuntimeError("gold.etl_audit must have 10 columns")
dss_tables = spark.sql(f"SHOW TABLES IN `{catalog}`.`{dss}`").collect()
allowed_dss = {"v_seller_features", "seller_risk_score", "policy_scenario", "decision_log"}
found_dss = set()
for row in dss_tables:
    name = row.tableName if hasattr(row, "tableName") else row[1]
    found_dss.add(name)
unexpected = found_dss - allowed_dss
if unexpected:
    raise RuntimeError(f"Unexpected objects in {catalog}.{dss}: {sorted(unexpected)}")
print(f"dss objects: {sorted(found_dss) or 'none'}")
