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


def risk_board() -> tuple[str, tuple]:
    sql = """
    SELECT
      r.seller_key,
      r.seller_id,
      r.as_of_month,
      r.p_bad,
      r.q_bar,
      r.gmv,
      r.late_ship_rate,
      r.avg_review,
      r.n_orders_valid,
      r.model_name,
      r.trained_through_month,
      r.scored_at,
      s.city_name,
      s.state_code,
      s.region_name,
      s.business_segment,
      s.lead_type,
      s.won_date,
      DATEDIFF(TO_DATE(CONCAT(r.as_of_month, '-01')), s.won_date) AS seller_age_days
    FROM {catalog}.{dss}.seller_risk_score AS r
    LEFT JOIN {catalog}.{gold}.dim_seller AS s
      ON r.seller_key = s.seller_key
    """
    return _bind(sql), ()


def seller_history(seller_id: str) -> tuple[str, tuple]:
    sql = """
    SELECT
      m.year_month,
      SUM(f.late_ship_count) AS late_ship_count,
      SUM(f.late_ship_eligible) AS late_ship_eligible,
      SUM(f.negative_review_count) AS negative_review_count,
      SUM(f.negative_review_eligible) AS negative_review_eligible,
      SUM(f.n_orders_valid) AS n_orders_valid,
      SUM(f.cancel_count) AS cancel_count,
      SUM(f.n_orders_placed) AS n_orders_placed,
      SUM(f.handling_days_sum) AS handling_days_sum,
      SUM(f.handling_days_count) AS handling_days_count,
      SUM(f.gmv) AS gmv
    FROM {catalog}.{gold}.fact_seller_monthly AS f
    INNER JOIN {catalog}.{gold}.dim_month AS m
      ON f.month_key = m.month_key
    INNER JOIN {catalog}.{gold}.dim_seller AS s
      ON f.seller_key = s.seller_key
    WHERE s.seller_id = {p}
      AND f.seller_key <> -1
      AND m.month_key <> -1
    GROUP BY m.year_month
    ORDER BY m.year_month
    """
    return _bind(sql), (str(seller_id),)


def platform_month(year_month: str) -> tuple[str, tuple]:
    sql = """
    SELECT
      SUM(f.gmv) AS gmv,
      SUM(f.late_ship_count) AS late_ship_count,
      SUM(f.late_ship_eligible) AS late_ship_eligible,
      SUM(f.negative_review_count) AS negative_review_count,
      SUM(f.negative_review_eligible) AS negative_review_eligible,
      SUM(f.cancel_count) AS cancel_count,
      SUM(f.n_orders_placed) AS n_orders_placed,
      SUM(f.handling_days_sum) AS handling_days_sum,
      SUM(f.handling_days_count) AS handling_days_count,
      SUM(f.n_orders_valid) AS n_orders_valid
    FROM {catalog}.{gold}.fact_seller_monthly AS f
    INNER JOIN {catalog}.{gold}.dim_month AS m
      ON f.month_key = m.month_key
    WHERE m.year_month = {p}
      AND f.seller_key <> -1
      AND m.month_key <> -1
    """
    return _bind(sql), (str(year_month),)


def seller_categories(seller_id: str, year_month: str) -> tuple[str, tuple]:
    sql = """
    SELECT
      COALESCE(p.category_group, 'Unknown') AS category_group,
      SUM(CASE
        WHEN st.order_status IS NULL OR st.order_status NOT IN ('canceled', 'unavailable')
          THEN i.price
      END) AS gmv
    FROM {catalog}.{gold}.fact_order_item AS i
    INNER JOIN {catalog}.{gold}.fact_order AS o
      ON i.order_id = o.order_id
    INNER JOIN {catalog}.{gold}.dim_order_status AS st
      ON o.order_status_key = st.order_status_key
    INNER JOIN {catalog}.{gold}.dim_seller AS s
      ON i.seller_key = s.seller_key
    INNER JOIN {catalog}.{gold}.dim_product AS p
      ON i.product_key = p.product_key
    INNER JOIN {catalog}.{gold}.dim_date AS d
      ON i.purchase_date_key = d.date_key
    WHERE s.seller_id = {p}
      AND format_string('%04d-%02d', d.year, d.month) = {p}
      AND i.seller_key <> -1
    GROUP BY p.category_group
    ORDER BY gmv DESC
    """
    return _bind(sql), (str(seller_id), str(year_month))


def model_eval(as_of_month: str) -> tuple[str, tuple]:
    sql = """
    SELECT metric, value
    FROM {catalog}.{dss}.model_eval
    WHERE as_of_month = {p}
    """
    return _bind(sql), (str(as_of_month),)


def model_calibration(as_of_month: str) -> tuple[str, tuple]:
    sql = """
    SELECT bin, mean_pred, observed_rate, n
    FROM {catalog}.{dss}.model_calibration
    WHERE as_of_month = {p}
    ORDER BY bin
    """
    return _bind(sql), (str(as_of_month),)


def risk_contrib(seller_id: str, as_of_month: str) -> tuple[str, tuple]:
    sql = """
    SELECT feature, value, contribution
    FROM {catalog}.{dss}.seller_risk_contrib
    WHERE seller_id = {p}
      AND as_of_month = {p}
    """
    return _bind(sql), (str(seller_id), str(as_of_month))


def home_profile() -> tuple[str, tuple]:
    """Scale of the mart, plus the latest Gold and DSS job timestamps."""
    sql = """
    SELECT
      (SELECT MIN(d.full_date)
       FROM {catalog}.{gold}.fact_order AS o
       INNER JOIN {catalog}.{gold}.dim_date AS d
         ON o.purchase_date_key = d.date_key
       WHERE d.date_key <> -1) AS min_purchase,
      (SELECT MAX(d.full_date)
       FROM {catalog}.{gold}.fact_order AS o
       INNER JOIN {catalog}.{gold}.dim_date AS d
         ON o.purchase_date_key = d.date_key
       WHERE d.date_key <> -1) AS max_purchase,
      (SELECT COUNT(*) FROM {catalog}.{gold}.fact_order) AS n_orders,
      (SELECT COUNT(*)
       FROM {catalog}.{gold}.dim_seller
       WHERE seller_key <> -1) AS n_sellers,
      (SELECT COUNT(*)
       FROM {catalog}.{gold}.dim_customer
       WHERE customer_key <> -1) AS n_customers,
      (SELECT COUNT(DISTINCT category_pt)
       FROM {catalog}.{gold}.dim_product
       WHERE product_key <> -1
         AND category_pt <> 'Unknown') AS n_categories,
      (SELECT COUNT(DISTINCT state_code)
       FROM {catalog}.{gold}.dim_seller
       WHERE seller_key <> -1
         AND state_code IS NOT NULL
         AND state_code <> 'Unknown') AS n_states,
      (SELECT COUNT(*)
       FROM {catalog}.{gold}.fact_order
       WHERE n_sellers > 1) AS multi_seller_orders,
      (SELECT MAX(loaded_at) FROM {catalog}.{gold}.etl_audit) AS gold_loaded_at,
      (SELECT MAX(scored_at) FROM {catalog}.{dss}.seller_risk_score) AS dss_scored_at
    """
    return _bind(sql), ()


def home_months() -> tuple[str, tuple]:
    """Distinct orders by purchase month. Home flags thin months in Python."""
    sql = """
    SELECT
      m.year_month,
      COUNT(DISTINCT o.order_id) AS n_orders
    FROM {catalog}.{gold}.fact_order AS o
    INNER JOIN {catalog}.{gold}.dim_date AS d
      ON o.purchase_date_key = d.date_key
    INNER JOIN {catalog}.{gold}.dim_month AS m
      ON d.month_key = m.month_key
    WHERE d.date_key <> -1
      AND m.month_key <> -1
    GROUP BY m.year_month
    ORDER BY m.year_month
    """
    return _bind(sql), ()


def home_tables() -> tuple[str, tuple]:
    sql = """
    SELECT table_schema, table_name
    FROM {catalog}.information_schema.tables
    WHERE table_schema IN ('{gold}', '{dss}')
    ORDER BY table_schema, table_name
    """
    return _bind(sql), ()


# Seller geography sums the same fact_seller_monthly numerators and denominators
# as kpi_late_by_region (late ship) and seller_month_series (the other rates, GMV).
# Customer geography rebuilds those counts from the order and item flags, grouped
# by customer_state_code. Each order is counted once. Sidebar filters stay on the
# seller: purchase year, seller region, seller state.
_WHERE_SELLER_STATE = """
SELECT
  s.state_code AS state_code,
  MAX(s.region_name) AS region_name,
  SUM(f.gmv) AS gmv,
  SUM(f.n_items_valid) AS n_items_valid,
  SUM(f.bad_experience_count) AS bad_experience_count,
  SUM(f.bad_experience_eligible) AS bad_experience_eligible,
  SUM(f.late_delivery_count) AS late_delivery_count,
  SUM(f.late_delivery_eligible) AS late_delivery_eligible,
  SUM(f.late_ship_count) AS late_ship_count,
  SUM(f.late_ship_eligible) AS late_ship_eligible,
  SUM(f.negative_review_count) AS negative_review_count,
  SUM(f.negative_review_eligible) AS negative_review_eligible
FROM {catalog}.{gold}.fact_seller_monthly AS f
INNER JOIN {catalog}.{gold}.dim_month AS m
  ON f.month_key = m.month_key
INNER JOIN {catalog}.{gold}.dim_seller AS s
  ON f.seller_key = s.seller_key
WHERE f.seller_key <> -1
  AND m.month_key <> -1
  AND s.seller_key <> -1
  AND (s.region_name IS NULL OR s.region_name <> 'Unknown')
  AND ({p} IS NULL OR m.year = {p})
  AND ({p} IS NULL OR s.region_name = {p})
  AND ({p} IS NULL OR s.state_code = {p})
GROUP BY s.state_code
"""

_WHERE_CUSTOMER_STATE = """
WITH items AS (
  SELECT
    i.order_id,
    i.price,
    i.seller_ship_late_flag,
    o.customer_state_code,
    o.late_flag,
    o.n_sellers,
    o.review_score,
    o.shared_review_type,
    o.negative_review_flag,
    st.order_status
  FROM {catalog}.{gold}.fact_order_item AS i
  INNER JOIN {catalog}.{gold}.fact_order AS o
    ON i.order_id = o.order_id
  INNER JOIN {catalog}.{gold}.dim_order_status AS st
    ON o.order_status_key = st.order_status_key
  INNER JOIN {catalog}.{gold}.dim_seller AS s
    ON i.seller_key = s.seller_key
  INNER JOIN {catalog}.{gold}.dim_date AS d
    ON i.purchase_date_key = d.date_key
  WHERE i.seller_key <> -1
    AND s.seller_key <> -1
    AND d.date_key <> -1
    AND (s.region_name IS NULL OR s.region_name <> 'Unknown')
    AND ({p} IS NULL OR d.year = {p})
    AND ({p} IS NULL OR s.region_name = {p})
    AND ({p} IS NULL OR s.state_code = {p})
),
by_order AS (
  SELECT
    order_id,
    MAX(customer_state_code) AS state_code,
    MAX(late_flag) AS late_flag,
    MAX(n_sellers) AS n_sellers,
    MAX(review_score) AS review_score,
    MAX(shared_review_type) AS shared_review_type,
    MAX(negative_review_flag) AS negative_review_flag,
    SUM(CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN price
    END) AS gmv,
    SUM(CASE
      WHEN order_status IS NULL OR order_status NOT IN ('canceled', 'unavailable')
        THEN 1 ELSE 0
    END) AS n_items_valid,
    SUM(CASE WHEN seller_ship_late_flag = 1 THEN 1 ELSE 0 END) AS late_ship_count,
    SUM(CASE WHEN seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) AS late_ship_eligible
  FROM items
  GROUP BY order_id
),
states AS (
  SELECT
    state_code,
    SUM(COALESCE(gmv, 0)) AS gmv,
    SUM(n_items_valid) AS n_items_valid,
    SUM(late_ship_count) AS late_ship_count,
    SUM(late_ship_eligible) AS late_ship_eligible,
    SUM(CASE WHEN late_flag = 1 THEN 1 ELSE 0 END) AS late_delivery_count,
    SUM(CASE WHEN late_flag IS NOT NULL THEN 1 ELSE 0 END) AS late_delivery_eligible,
    SUM(CASE
      WHEN n_sellers = 1
       AND shared_review_type IN ('none', 'same_seller')
       AND review_score IS NOT NULL
       AND negative_review_flag = 1
      THEN 1 ELSE 0
    END) AS negative_review_count,
    SUM(CASE
      WHEN n_sellers = 1
       AND shared_review_type IN ('none', 'same_seller')
       AND review_score IS NOT NULL
      THEN 1 ELSE 0
    END) AS negative_review_eligible,
    SUM(CASE
      WHEN (
        n_sellers = 1
        AND shared_review_type IN ('none', 'same_seller')
        AND review_score IS NOT NULL
        AND negative_review_flag = 1
      ) OR late_flag = 1
      THEN 1 ELSE 0
    END) AS bad_experience_count,
    SUM(CASE
      WHEN (
        n_sellers = 1
        AND shared_review_type IN ('none', 'same_seller')
        AND review_score IS NOT NULL
      ) OR late_flag IS NOT NULL
      THEN 1 ELSE 0
    END) AS bad_experience_eligible
  FROM by_order
  WHERE state_code IS NOT NULL
    AND state_code <> 'Unknown'
  GROUP BY state_code
)
SELECT
  states.state_code,
  geo.region_name,
  states.gmv,
  states.n_items_valid,
  states.bad_experience_count,
  states.bad_experience_eligible,
  states.late_delivery_count,
  states.late_delivery_eligible,
  states.late_ship_count,
  states.late_ship_eligible,
  states.negative_review_count,
  states.negative_review_eligible
FROM states
LEFT JOIN (
  SELECT s.state_code, MAX(s.region_name) AS region_name
  FROM {catalog}.{gold}.dim_seller AS s
  WHERE s.seller_key <> -1
    AND s.state_code IS NOT NULL
    AND s.state_code <> 'Unknown'
    AND (s.region_name IS NULL OR s.region_name <> 'Unknown')
  GROUP BY s.state_code
) AS geo
  ON states.state_code = geo.state_code
"""


def kpi_where_by_state(year, region, state, geography: str) -> tuple[str, tuple]:
    """One row per state. geography is seller or customer. Values stay in the tuple."""
    if geography == "seller":
        sql = _WHERE_SELLER_STATE
    elif geography == "customer":
        sql = _WHERE_CUSTOMER_STATE
    else:
        raise ValueError("geography must be seller or customer")
    return _bind(sql), (year, year, region, region, state, state)
