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


def print_grain_retention(
    target: str,
    grain_before: int,
    grain_source: int,
    grain_after: int,
    orphans: int,
) -> None:
    """Grain counts only. Do not store these on etl_audit.rows_loaded."""
    increased = grain_after - grain_before
    print(
        f"DQ grain {target}: before={grain_before} source={grain_source} "
        f"after={grain_after} increased={increased} orphans_not_in_source={orphans}"
    )
