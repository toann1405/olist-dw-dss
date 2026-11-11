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


def months() -> tuple[str, tuple]:
    sql = """
    SELECT year_month
    FROM {catalog}.{gold}.dim_month
    WHERE month_key <> -1
      AND year_month <> 'Unknown'
    ORDER BY year_month
    """
    return _bind(sql), ()


def _scope(year, region, state, funnel, month_from, month_to) -> tuple:
    return (
        year, year, region, region, state, state,
        funnel, funnel, month_from, month_from, month_to, month_to,
    )


_SCOPE_WHERE_MONTH = """
  AND ({p} IS NULL OR m.year = {p})
  AND ({p} IS NULL OR s.region_name = {p})
  AND ({p} IS NULL OR s.state_code = {p})
  AND ({p} IS NULL OR s.has_closed_deal = {p})
  AND ({p} IS NULL OR m.year_month >= {p})
  AND ({p} IS NULL OR m.year_month <= {p})
"""


def seller_month_series(year, region, state, funnel, month_from, month_to) -> tuple[str, tuple]:
    sql = f"""
    SELECT
      m.year_month,
      SUM(f.gmv) AS gmv,
      SUM(f.n_orders_valid) AS n_orders_valid,
      SUM(f.late_ship_count) AS late_ship_count,
      SUM(f.late_ship_eligible) AS late_ship_eligible,
      SUM(f.late_delivery_count) AS late_delivery_count,
      SUM(f.late_delivery_eligible) AS late_delivery_eligible,
      SUM(f.negative_review_count) AS negative_review_count,
      SUM(f.negative_review_eligible) AS negative_review_eligible,
      SUM(f.bad_experience_count) AS bad_experience_count,
      SUM(f.bad_experience_eligible) AS bad_experience_eligible,
      SUM(f.cancel_count) AS cancel_count,
      SUM(f.n_orders_placed) AS n_orders_placed,
      SUM(f.review_score_sum) AS review_score_sum,
      SUM(f.review_count) AS review_count,
      SUM(f.handling_days_sum) AS handling_days_sum,
      SUM(f.handling_days_count) AS handling_days_count,
      COUNT(DISTINCT CASE WHEN f.n_orders_valid >= 1 THEN f.seller_key END) AS active_sellers
    FROM {{catalog}}.{{gold}}.fact_seller_monthly AS f
    INNER JOIN {{catalog}}.{{gold}}.dim_month AS m
      ON f.month_key = m.month_key
    INNER JOIN {{catalog}}.{{gold}}.dim_seller AS s
      ON f.seller_key = s.seller_key
    WHERE f.seller_key <> -1
      AND m.month_key <> -1
      AND s.seller_key <> -1
      {_SCOPE_WHERE_MONTH}
    GROUP BY m.year_month
    ORDER BY m.year_month
    """
    return _bind(sql), _scope(year, region, state, funnel, month_from, month_to)


def seller_pareto(year, region, state, funnel, month_from, month_to, min_orders: int) -> tuple[str, tuple]:
    sql = f"""
    SELECT
      s.seller_id,
      SUM(f.bad_experience_count) AS bad_orders,
      SUM(f.bad_experience_eligible) AS eligible_orders,
      SUM(f.gmv) AS gmv,
      SUM(f.n_orders_valid) AS n_orders_valid
    FROM {{catalog}}.{{gold}}.fact_seller_monthly AS f
    INNER JOIN {{catalog}}.{{gold}}.dim_month AS m
      ON f.month_key = m.month_key
    INNER JOIN {{catalog}}.{{gold}}.dim_seller AS s
      ON f.seller_key = s.seller_key
    WHERE f.seller_key <> -1
      AND m.month_key <> -1
      AND s.seller_key <> -1
      {_SCOPE_WHERE_MONTH}
    GROUP BY s.seller_id
    HAVING SUM(f.n_orders_valid) >= {{p}}
    """
    params = _scope(year, region, state, funnel, month_from, month_to) + (int(min_orders),)
    return _bind(sql), params


def funnel_compare(year, region, state, month_from, month_to) -> tuple[str, tuple]:
    sql = """
    SELECT
      s.has_closed_deal,
      SUM(f.bad_experience_count) AS bad_orders,
      SUM(f.bad_experience_eligible) AS eligible_orders,
      COUNT(DISTINCT f.seller_key) AS sellers
    FROM {catalog}.{gold}.fact_seller_monthly AS f
    INNER JOIN {catalog}.{gold}.dim_month AS m
      ON f.month_key = m.month_key
    INNER JOIN {catalog}.{gold}.dim_seller AS s
      ON f.seller_key = s.seller_key
    WHERE f.seller_key <> -1
      AND m.month_key <> -1
      AND s.seller_key <> -1
      AND ({p} IS NULL OR m.year = {p})
      AND ({p} IS NULL OR s.region_name = {p})
      AND ({p} IS NULL OR s.state_code = {p})
      AND ({p} IS NULL OR m.year_month >= {p})
      AND ({p} IS NULL OR m.year_month <= {p})
    GROUP BY s.has_closed_deal
    """
    params = (year, year, region, region, state, state, month_from, month_from, month_to, month_to)
    return _bind(sql), params


def category_scatter(year, region, state) -> tuple[str, tuple]:
    sql = """
    SELECT
      COALESCE(p.category_group, 'Unknown') AS category_group,
      SUM(CASE
        WHEN st.order_status IS NULL OR st.order_status NOT IN ('canceled', 'unavailable')
          THEN i.price
      END) AS gmv,
      COUNT(DISTINCT CASE WHEN o.bad_experience_flag = 1 THEN o.order_id END) AS bad_orders,
      COUNT(DISTINCT CASE WHEN o.bad_experience_flag IS NOT NULL THEN o.order_id END) AS eligible_orders,
      COUNT(DISTINCT o.order_id) AS orders
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
    GROUP BY p.category_group
    """
    return _bind(sql), (year, year, region, region, state, state)


def market_quality(year, region, state) -> tuple[str, tuple]:
    sql = """
    WITH touched AS (
      SELECT DISTINCT
        o.order_id,
        o.n_sellers,
        o.shared_review_type,
        o.negative_review_flag,
        o.bad_experience_flag,
        o.late_flag
      FROM {catalog}.{gold}.fact_order AS o
      INNER JOIN {catalog}.{gold}.fact_order_item AS i
        ON o.order_id = i.order_id
      INNER JOIN {catalog}.{gold}.dim_seller AS s
        ON i.seller_key = s.seller_key
      INNER JOIN {catalog}.{gold}.dim_date AS d
        ON i.purchase_date_key = d.date_key
      WHERE i.seller_key <> -1
        AND s.seller_key <> -1
        AND d.date_key <> -1
        AND ({p} IS NULL OR d.year = {p})
        AND ({p} IS NULL OR s.region_name = {p})
        AND ({p} IS NULL OR s.state_code = {p})
    )
    SELECT
      COUNT(*) AS orders,
      SUM(CASE WHEN n_sellers > 1 THEN 1 ELSE 0 END) AS multi_seller_orders,
      SUM(CASE
        WHEN negative_review_flag IS NOT NULL
         AND (n_sellers > 1 OR shared_review_type = 'cross_seller')
          THEN 1 ELSE 0
      END) AS review_excluded_orders,
      SUM(CASE WHEN bad_experience_flag = 1 THEN 1 ELSE 0 END) AS bad_orders,
      SUM(CASE WHEN bad_experience_flag IS NOT NULL THEN 1 ELSE 0 END) AS bad_eligible,
      SUM(CASE WHEN late_flag = 1 THEN 1 ELSE 0 END) AS late_orders,
      SUM(CASE WHEN late_flag IS NOT NULL THEN 1 ELSE 0 END) AS late_eligible
    FROM touched
    """
    return _bind(sql), (year, year, region, region, state, state)


def story_by_region(
    year: int | None,
    region: str | None,
    state: str | None,
    category: str | None,
) -> tuple[str, tuple]:
    params = (year, year, region, region, state, state, category, category)
    return _bind(_STORY_BY_REGION), params
