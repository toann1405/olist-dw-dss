"""Load SQL files and bind catalog names plus filter parameters."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from lib import db

SQL_DIR = Path(__file__).resolve().parents[2] / "sql" / "olap_queries"
GOLD_PREFIX = re.compile(r"(?<![\w`.])gold\.")


def load(filename: str) -> str:
    if Path(filename).name != filename or not filename.endswith(".sql"):
        raise ValueError("SQL file name is not allowed")
    cfg = db.settings()
    raw = (SQL_DIR / filename).read_text(encoding="utf-8")
    qualified = GOLD_PREFIX.sub(f"{cfg['catalog']}.{cfg['gold']}.", raw)
    return (
        qualified.replace("{catalog}", cfg["catalog"])
        .replace("{gold}", cfg["gold"])
        .replace("{dss}", cfg["dss"])
        .replace("{p}", db.marker())
    )


def years() -> tuple[str, tuple]:
    return load("kpi_years.sql"), ()


def regions() -> tuple[str, tuple]:
    return load("kpi_regions.sql"), ()


def _place(year: int | None, region: str | None, state: str | None) -> tuple:
    return (year, year, region, region, state, state)


def kpi_seller_month(year: int | None, region: str | None, state: str | None = None) -> tuple[str, tuple]:
    return load("kpi_seller_month.sql"), _place(year, region, state)


def kpi_orders(year: int | None, region: str | None, state: str | None = None) -> tuple[str, tuple]:
    return load("kpi_orders.sql"), _place(year, region, state)


def states(region: str | None) -> tuple[str, tuple]:
    return load("kpi_states.sql"), (region, region)


def kpi_by_month(year: int | None, region: str | None, state: str | None) -> tuple[str, tuple]:
    return load("kpi_by_month.sql"), _place(year, region, state)


def kpi_top_categories(year: int | None, region: str | None, state: str | None) -> tuple[str, tuple]:
    return load("kpi_top_categories.sql"), _place(year, region, state)


def kpi_late_by_region(year: int | None, state: str | None) -> tuple[str, tuple]:
    return load("kpi_late_by_region.sql"), (year, year, state, state)


def kpi_for_category(
    year: int | None, region: str | None, state: str | None, category: str
) -> tuple[str, tuple]:
    return load("kpi_for_category.sql"), (*_place(year, region, state), category)


def pivot_counts() -> tuple[str, tuple]:
    return load("pivot_counts.sql"), ()


def category_groups() -> pd.DataFrame:
    return db.query(*load_pair("olap_categories.sql"))


def load_pair(filename: str) -> tuple[str, tuple]:
    return load(filename), ()


def slice_category(category_group: str) -> tuple[str, tuple]:
    allowed = set(category_groups()["category_group"].dropna().astype(str))
    if category_group not in allowed:
        raise ValueError("category_group is not in the slicer list")
    return load("03_slice_category_late_sellers.sql"), (category_group,)


def rollup() -> tuple[str, tuple]:
    return load("01_rollup_seller_late_handoff.sql"), ()


def drilldown() -> tuple[str, tuple]:
    return load("02_drilldown_negative_review.sql"), ()


def dice() -> tuple[str, tuple]:
    return load("04_dice_north_bulky.sql"), ()


def pivot() -> tuple[str, tuple]:
    return load("05_pivot_category_quarter_late.sql"), ()


def risk_scores(min_orders: int) -> tuple[str, tuple]:
    return load("risk_scores.sql"), (int(min_orders),)


def scores() -> tuple[str, tuple]:
    return load("risk_scores_all.sql"), ()


def seller_profile(seller_id: str) -> tuple[str, tuple]:
    return load("seller_profile.sql"), (str(seller_id),)


def policy_snapshot() -> tuple[str, tuple]:
    return load("policy_scenario.sql"), ()


_RECENT_DECISIONS = """
SELECT
  decided_at,
  policy_code,
  gmv_affected_pct,
  n_sellers_flagged,
  note
FROM (
  SELECT
    decided_at,
    policy_code,
    gmv_affected_pct,
    n_sellers_flagged,
    note,
    ROW_NUMBER() OVER (ORDER BY decided_at DESC) AS rn
  FROM {catalog}.{dss}.decision_log
) AS ranked
WHERE rn <= {p}
ORDER BY decided_at DESC
"""


def recent_decisions(limit: int) -> tuple[str, tuple]:
    return _bind(_RECENT_DECISIONS), (int(limit),)


def next_decision_id() -> tuple[str, tuple]:
    return load("decision_next_id.sql"), ()


def insert_decision(values: tuple) -> tuple[str, tuple]:
    if len(values) != 22:
        raise ValueError("decision_log insert expects 22 values")
    return load("insert_decision.sql"), tuple(values)


def _bind(sql_text: str) -> str:
    """Substitute catalog names and the parameter marker. Values stay in the tuple."""
    cfg = db.settings()
    return (
        sql_text.replace("{catalog}", cfg["catalog"])
        .replace("{gold}", cfg["gold"])
        .replace("{dss}", cfg["dss"])
        .replace("{p}", db.marker())
    )


_ACTIVE_SELLERS = """
SELECT COUNT(DISTINCT seller_key) AS active_sellers
FROM {catalog}.{gold}.fact_seller_monthly
WHERE seller_key <> -1
  AND n_orders_valid >= 1
"""

_STORY_BY_REGION = """
WITH items AS (
  SELECT
    i.order_id,
    i.price,
    o.bad_experience_flag,
    st.order_status,
    s.region_name
  FROM {catalog}.{gold}.fact_order_item AS i
  INNER JOIN {catalog}.{gold}.fact_order AS o
    ON i.order_id = o.order_id
  INNER JOIN {catalog}.{gold}.dim_order_status AS st
    ON o.order_status_key = st.order_status_key
  INNER JOIN {catalog}.{gold}.dim_seller AS s
    ON i.seller_key = s.seller_key
  INNER JOIN {catalog}.{gold}.dim_date AS d
    ON i.purchase_date_key = d.date_key
  LEFT JOIN {catalog}.{gold}.dim_product AS p
    ON i.product_key = p.product_key
  WHERE i.seller_key <> -1
    AND s.seller_key <> -1
    AND d.date_key <> -1
    AND ({p} IS NULL OR d.year = {p})
    AND ({p} IS NULL OR s.region_name = {p})
    AND ({p} IS NULL OR s.state_code = {p})
    AND ({p} IS NULL OR p.category_group = {p})
)
SELECT
  CASE
    WHEN GROUPING(region_name) = 1 THEN '__total__'
    ELSE COALESCE(region_name, '(không map được vùng)')
  END AS region_name,
  GROUPING(region_name) AS is_total,
  SUM(
    CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN price
    END
  ) AS gmv,
  COUNT(DISTINCT CASE WHEN bad_experience_flag = 1 THEN order_id END) AS bad_orders,
  COUNT(DISTINCT CASE WHEN bad_experience_flag IS NOT NULL THEN order_id END) AS eligible_orders
FROM items
GROUP BY GROUPING SETS ((region_name), ())
"""


def active_sellers() -> tuple[str, tuple]:
    return _bind(_ACTIVE_SELLERS), ()


def story_by_region(
    year: int | None,
    region: str | None,
    state: str | None,
    category: str | None,
) -> tuple[str, tuple]:
    params = (year, year, region, region, state, state, category, category)
    return _bind(_STORY_BY_REGION), params
