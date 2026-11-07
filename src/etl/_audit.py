# Databricks notebook source
"""Append one gold.etl_audit row. Defines functions only. No tables, no CSV reads."""

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import LongType, StringType, StructField, StructType, TimestampType


def append_audit(
    catalog: str,
    gold_schema: str,
    run_id: str,
    layer: str,
    target_table: str,
    source_name: str,
    rows_read: int,
    rows_loaded: int,
    rows_rejected: int,
    rows_unknown_fk: int | None,
) -> None:
    """Insert one log row. audit_id = max + 1. Does not MERGE history."""
    table = f"{catalog}.{gold_schema}.etl_audit"
    current = spark.sql(f"SELECT COALESCE(MAX(audit_id), 0) AS max_id FROM {table}").first()
    audit_id = int(current["max_id"]) + 1
    schema = StructType(
        [
            StructField("audit_id", LongType(), False),
            StructField("run_id", StringType(), False),
            StructField("layer", StringType(), False),
            StructField("target_table", StringType(), False),
            StructField("source_name", StringType(), False),
            StructField("rows_read", LongType(), False),
            StructField("rows_loaded", LongType(), False),
            StructField("rows_rejected", LongType(), False),
            StructField("rows_unknown_fk", LongType(), True),
            StructField("loaded_at", TimestampType(), True),
        ]
    )
    row = spark.createDataFrame(
        [
            (
                audit_id,
                run_id,
                layer,
                target_table,
                source_name,
                int(rows_read),
                int(rows_loaded),
                int(rows_rejected),
                None if rows_unknown_fk is None else int(rows_unknown_fk),
                None,
            )
        ],
        schema,
    ).withColumn("loaded_at", F.current_timestamp())
    row.write.format("delta").mode("append").saveAsTable(table)
