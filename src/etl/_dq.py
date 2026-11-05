# Databricks notebook source
"""Printed data-quality checks. Defines functions only. Warnings do not fail the job."""

# COMMAND ----------


def print_recon(
    target: str,
    rows_read: int,
    rows_loaded: int,
    rows_dropped_by_dedup: int,
    rows_rejected: int,
) -> None:
    expected = rows_loaded + rows_dropped_by_dedup + rows_rejected
    ok = rows_read == expected
    print(
        "DQ recon "
        f"{target}: read={rows_read} loaded={rows_loaded} "
        f"dropped={rows_dropped_by_dedup} rejected={rows_rejected} ok={ok}"
    )


def print_warn(check: str, detail: str) -> None:
    print(f"DQ warn {check}: {detail}")
