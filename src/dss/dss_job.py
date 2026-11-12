# Databricks notebook source
"""Score sellers from Gold and write the DSS snapshot tables.

Reads gold.* only, through dss.v_seller_features. Overwrites
dss.seller_risk_score, dss.policy_scenario, and the M1 eval tables
for the scoring month. Creates dss.decision_log if needed and does
not delete its rows.
"""

# COMMAND ----------

import sys
from pathlib import Path

# COMMAND ----------

def widget(name: str, default: str) -> str:
    dbutils.widgets.text(name, default)
    value = dbutils.widgets.get(name)
    text = "" if value is None else str(value).strip()
    return text or default


def find_repo_root(explicit: str) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    try:
        notebook_path = (
            dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        )
        parts = notebook_path.split("/")
        if "src" in parts:
            repo = "/".join(parts[: parts.index("src")])
            candidates.append(Path("/Workspace") / repo.lstrip("/"))
            candidates.append(Path(repo))
    except Exception:
        pass
    try:
        candidates.append(Path(__file__).resolve().parents[2])
    except NameError:
        pass
    candidates.append(Path.cwd())
    for candidate in candidates:
        if (candidate / "src" / "dss" / "policy.py").is_file():
            return candidate
    raise RuntimeError(
        "Cannot find the repo root. Set the repo_root widget to the folder that contains src/."
    )

# COMMAND ----------

catalog = widget("uc_catalog", "olist_catalog")
gold = widget("gold_schema", "gold")
dss = widget("dss_schema", "dss")
repo_root = find_repo_root(widget("repo_root", ""))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.dss.params import AS_OF_MONTH
from src.dss.policy import PolicyParams, compare_policies, scenario_record
from src.dss.train import train_and_score

# COMMAND ----------

view_sql = (repo_root / "src" / "sql" / "views" / "v_seller_features.sql").read_text(encoding="utf-8")
view_sql = view_sql.format(catalog=catalog, gold=gold)
spark.sql(f"CREATE OR REPLACE VIEW {catalog}.{dss}.v_seller_features AS\n{view_sql}")
print(f"view ready: {catalog}.{dss}.v_seller_features")

# COMMAND ----------

spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{dss}.seller_risk_score (
      seller_key BIGINT NOT NULL,
      seller_id STRING NOT NULL,
      as_of_month STRING NOT NULL,
      p_bad DOUBLE,
      q_bar DOUBLE NOT NULL,
      gmv DOUBLE NOT NULL,
      late_ship_rate DOUBLE,
      avg_review DOUBLE,
      n_orders_valid INT NOT NULL,
      model_name STRING NOT NULL,
      trained_through_month STRING,
      scored_at TIMESTAMP NOT NULL
    ) USING DELTA
    COMMENT 'One seller row for the latest scored month'
    """
)
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{dss}.policy_scenario (
      as_of_month STRING NOT NULL,
      policy_code STRING NOT NULL,
      theta_1 DOUBLE NOT NULL,
      theta_2 DOUBLE NOT NULL,
      theta_3 DOUBLE NOT NULL,
      e1 DOUBLE NOT NULL,
      e2 DOUBLE NOT NULL,
      e3 DOUBLE NOT NULL,
      e_p1 DOUBLE NOT NULL,
      late_ship_threshold DOUBLE NOT NULL,
      avg_review_threshold DOUBLE NOT NULL,
      r DOUBLE NOT NULL,
      s DOUBLE NOT NULL,
      min_orders INT NOT NULL,
      x_limit DOUBLE NOT NULL,
      n_limit INT NOT NULL,
      expected_bad_orders DOUBLE NOT NULL,
      gmv_affected_pct DOUBLE,
      n_sellers_flagged INT NOT NULL,
      meets_x BOOLEAN NOT NULL,
      meets_n BOOLEAN NOT NULL,
      scored_at TIMESTAMP NOT NULL
    ) USING DELTA
    COMMENT 'P0 P1 and P2 for the latest scored month'
    """
)
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{dss}.decision_log (
      decision_id STRING NOT NULL,
      decided_at TIMESTAMP NOT NULL,
      as_of_month STRING NOT NULL,
      policy_code STRING NOT NULL,
      theta_1 DOUBLE NOT NULL,
      theta_2 DOUBLE NOT NULL,
      theta_3 DOUBLE NOT NULL,
      e1 DOUBLE NOT NULL,
      e2 DOUBLE NOT NULL,
      e3 DOUBLE NOT NULL,
      e_p1 DOUBLE NOT NULL,
      late_ship_threshold DOUBLE NOT NULL,
      avg_review_threshold DOUBLE NOT NULL,
      r DOUBLE NOT NULL,
      s DOUBLE NOT NULL,
      min_orders INT NOT NULL,
      x_limit DOUBLE NOT NULL,
      n_limit INT NOT NULL,
      expected_bad_orders DOUBLE NOT NULL,
      gmv_affected_pct DOUBLE,
      n_sellers_flagged INT NOT NULL,
      note STRING
    ) USING DELTA
    COMMENT 'One appended row per confirmed decision. Streamlit writes this table.'
    """
)
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{dss}.seller_risk_contrib (
      as_of_month STRING NOT NULL,
      seller_id STRING NOT NULL,
      feature STRING NOT NULL,
      value DOUBLE,
      contribution DOUBLE
    ) USING DELTA
    COMMENT 'coef times centered feature. Written by the DSS job when logistic scores are fit.'
    """
)
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{dss}.model_eval (
      as_of_month STRING NOT NULL,
      metric STRING NOT NULL,
      value DOUBLE
    ) USING DELTA
    COMMENT 'Test-month metrics for the M1 fit. One row per metric for the scoring month.'
    """
)
spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS {catalog}.{dss}.model_calibration (
      as_of_month STRING NOT NULL,
      bin INT NOT NULL,
      mean_pred DOUBLE,
      observed_rate DOUBLE,
      n INT
    ) USING DELTA
    COMMENT 'Predicted versus observed rate by decile on the test month.'
    """
)

# COMMAND ----------

features = spark.table(f"{catalog}.{dss}.v_seller_features").toPandas()
if features.empty:
    raise RuntimeError("v_seller_features returned no rows. The monthly Gold fact is empty.")
scores, metrics, calibration, contrib = train_and_score(features, AS_OF_MONTH)
if scores.empty:
    raise RuntimeError("Scoring returned no sellers.")
params = PolicyParams()
scenarios = compare_policies(scores, params)
as_of_month = str(scores["as_of_month"].iloc[0])
scored_at = scores["scored_at"].iloc[0]
scenario_rows = [scenario_record(item, params, as_of_month, scored_at) for item in scenarios]

print(f"model_name={metrics['model_name']}")
print(f"reason={metrics['reason']}")
print(f"auc={metrics['auc']}")
print(f"brier={metrics['brier']}")
print(f"trained_through_month={metrics['trained_through_month']}")
print(f"base_rate={metrics.get('base_rate')}")
print(f"test_months={metrics.get('test_months')}")
print(f"as_of_month={as_of_month}")
print(f"sellers={len(scores)}")
for row in scenario_rows:
    print(
        f"{row['policy_code']} expected_bad_orders={row['expected_bad_orders']} "
        f"gmv_affected_pct={row['gmv_affected_pct']} n_sellers_flagged={row['n_sellers_flagged']}"
    )

# COMMAND ----------

import math

import pandas as pd
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

score_columns = [
    "seller_key",
    "seller_id",
    "as_of_month",
    "p_bad",
    "q_bar",
    "gmv",
    "late_ship_rate",
    "avg_review",
    "n_orders_valid",
    "model_name",
    "trained_through_month",
    "scored_at",
]
scenario_columns = [
    "as_of_month",
    "policy_code",
    "theta_1",
    "theta_2",
    "theta_3",
    "e1",
    "e2",
    "e3",
    "e_p1",
    "late_ship_threshold",
    "avg_review_threshold",
    "r",
    "s",
    "min_orders",
    "x_limit",
    "n_limit",
    "expected_bad_orders",
    "gmv_affected_pct",
    "n_sellers_flagged",
    "meets_x",
    "meets_n",
    "scored_at",
]
score_schema = StructType(
    [
        StructField("seller_key", LongType(), False),
        StructField("seller_id", StringType(), False),
        StructField("as_of_month", StringType(), False),
        StructField("p_bad", DoubleType(), True),
        StructField("q_bar", DoubleType(), False),
        StructField("gmv", DoubleType(), False),
        StructField("late_ship_rate", DoubleType(), True),
        StructField("avg_review", DoubleType(), True),
        StructField("n_orders_valid", IntegerType(), False),
        StructField("model_name", StringType(), False),
        StructField("trained_through_month", StringType(), True),
        StructField("scored_at", TimestampType(), False),
    ]
)
scenario_schema = StructType(
    [
        StructField("as_of_month", StringType(), False),
        StructField("policy_code", StringType(), False),
        StructField("theta_1", DoubleType(), False),
        StructField("theta_2", DoubleType(), False),
        StructField("theta_3", DoubleType(), False),
        StructField("e1", DoubleType(), False),
        StructField("e2", DoubleType(), False),
        StructField("e3", DoubleType(), False),
        StructField("e_p1", DoubleType(), False),
        StructField("late_ship_threshold", DoubleType(), False),
        StructField("avg_review_threshold", DoubleType(), False),
        StructField("r", DoubleType(), False),
        StructField("s", DoubleType(), False),
        StructField("min_orders", IntegerType(), False),
        StructField("x_limit", DoubleType(), False),
        StructField("n_limit", IntegerType(), False),
        StructField("expected_bad_orders", DoubleType(), False),
        StructField("gmv_affected_pct", DoubleType(), True),
        StructField("n_sellers_flagged", IntegerType(), False),
        StructField("meets_x", BooleanType(), False),
        StructField("meets_n", BooleanType(), False),
        StructField("scored_at", TimestampType(), False),
    ]
)


def _clean(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            value = value.tz_localize("UTC")
        return value.tz_convert("UTC").to_pydatetime()
    return value


def overwrite(table: str, frame, columns: list[str], schema) -> None:
    records = []
    for row in frame.loc[:, columns].itertuples(index=False, name=None):
        records.append(tuple(_clean(value) for value in row))
    spark.sql(f"DELETE FROM {table}")
    spark.createDataFrame(records, schema).write.format("delta").mode("append").insertInto(table)
    print(f"wrote {table}: {len(records)} rows")


eval_schema = StructType(
    [
        StructField("as_of_month", StringType(), False),
        StructField("metric", StringType(), False),
        StructField("value", DoubleType(), True),
    ]
)
calibration_schema = StructType(
    [
        StructField("as_of_month", StringType(), False),
        StructField("bin", IntegerType(), False),
        StructField("mean_pred", DoubleType(), True),
        StructField("observed_rate", DoubleType(), True),
        StructField("n", IntegerType(), True),
    ]
)
contrib_schema = StructType(
    [
        StructField("as_of_month", StringType(), False),
        StructField("seller_id", StringType(), False),
        StructField("feature", StringType(), False),
        StructField("value", DoubleType(), True),
        StructField("contribution", DoubleType(), True),
    ]
)
eval_columns = ["as_of_month", "metric", "value"]
calibration_columns = ["as_of_month", "bin", "mean_pred", "observed_rate", "n"]
contrib_columns = ["as_of_month", "seller_id", "feature", "value", "contribution"]


def _month_number(year_month: str) -> float:
    year, month = str(year_month).split("-")
    return float(int(year) * 100 + int(month))


eval_rows = [
    {"as_of_month": as_of_month, "metric": name, "value": metrics.get(name)}
    for name in ("auc", "brier", "n_train_orders", "n_test_orders", "base_rate")
]
for month in metrics.get("test_months") or []:
    eval_rows.append(
        {"as_of_month": as_of_month, "metric": "test_month", "value": _month_number(month)}
    )
eval_frame = pd.DataFrame(eval_rows, columns=eval_columns)

calibration_frame = calibration.copy()
calibration_frame.insert(0, "as_of_month", as_of_month)
contrib_frame = contrib.copy()
contrib_frame.insert(0, "as_of_month", as_of_month)

overwrite(f"{catalog}.{dss}.seller_risk_score", scores, score_columns, score_schema)
overwrite(
    f"{catalog}.{dss}.policy_scenario",
    pd.DataFrame(scenario_rows),
    scenario_columns,
    scenario_schema,
)
overwrite(f"{catalog}.{dss}.model_eval", eval_frame, eval_columns, eval_schema)
overwrite(
    f"{catalog}.{dss}.model_calibration",
    calibration_frame,
    calibration_columns,
    calibration_schema,
)
overwrite(
    f"{catalog}.{dss}.seller_risk_contrib",
    contrib_frame,
    contrib_columns,
    contrib_schema,
)
print("decision_log was not modified")
