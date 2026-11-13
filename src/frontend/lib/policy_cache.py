"""Cache M2 results for one score table and one parameter tuple.

The cached functions call the unchanged policy module. They do not recompute
a formula of their own.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib.insights import recommend_policy
from src.dss.policy import (
    PolicyParams,
    budget_curve,
    budget_seek,
    compare_policies,
    goal_seek,
    tornado,
    tornado_shifts,
)

_SCORE_COLUMNS = (
    "seller_id",
    "seller_key",
    "p_bad",
    "n_orders_valid",
    "gmv",
    "late_ship_rate",
    "avg_review",
    "q_bar",
    "as_of_month",
)


def _plain(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


def score_token(frame: pd.DataFrame) -> tuple:
    columns = [name for name in _SCORE_COLUMNS if name in frame.columns]
    slim = frame.loc[:, columns]
    rows = tuple(tuple(_plain(value) for value in row) for row in slim.itertuples(index=False, name=None))
    return rows, tuple(columns)


def param_token(params: PolicyParams) -> tuple:
    return (
        round(float(params.theta_1), 6),
        round(float(params.theta_2), 6),
        round(float(params.theta_3), 6),
        round(float(params.e1), 6),
        round(float(params.e2), 6),
        round(float(params.e3), 6),
        round(float(params.e_p1), 6),
        round(float(params.late_ship_threshold), 6),
        round(float(params.avg_review_threshold), 6),
        round(float(params.r), 6),
        round(float(params.s), 6),
        int(params.min_orders),
        float(params.x_limit),
        int(params.n_limit),
    )


def _frame(token: tuple) -> pd.DataFrame:
    rows, columns = token
    return pd.DataFrame(list(rows), columns=list(columns))


def _params(token: tuple) -> PolicyParams:
    return PolicyParams(*token)


@st.cache_data(show_spinner=False)
def cached_compare(score_rows: tuple, param_values: tuple):
    return compare_policies(_frame(score_rows), _params(param_values))


@st.cache_data(show_spinner=False)
def cached_goal(score_rows: tuple, param_values: tuple):
    return goal_seek(_frame(score_rows), _params(param_values))


@st.cache_data(show_spinner=False)
def cached_budget(score_rows: tuple, param_values: tuple):
    return budget_seek(_frame(score_rows), _params(param_values))


@st.cache_data(show_spinner=False)
def cached_budget_curve(score_rows: tuple, param_values: tuple):
    return budget_curve(_frame(score_rows), _params(param_values))


@st.cache_data(show_spinner=False)
def cached_tornado(score_rows: tuple, param_values: tuple):
    params = _params(param_values)
    return tornado(_frame(score_rows), params)


def _policy_summary_frame(results) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "policy_code": item.policy_code,
                "expected_bad_orders": item.expected_bad_orders,
                "gmv_affected_pct": item.gmv_affected_pct,
                "n_sellers_flagged": item.n_sellers_flagged,
                "meets_x": item.meets_x,
                "meets_n": item.meets_n,
            }
            for item in results
        ]
    )


@st.cache_data(show_spinner=False)
def cached_tornado_advice(score_rows: tuple, param_values: tuple) -> tuple[str | None, list[tuple[str, str, str | None]]]:
    frame = _frame(score_rows)
    params = _params(param_values)
    base_code = recommend_policy(
        _policy_summary_frame(compare_policies(frame, params)),
        params.x_limit,
        params.n_limit,
    ).get("code")
    changes: list[tuple[str, str, str | None]] = []
    for factor, shock, _mult, shifted in tornado_shifts(params):
        if shock == "base":
            continue
        code = recommend_policy(
            _policy_summary_frame(compare_policies(frame, shifted)),
            shifted.x_limit,
            shifted.n_limit,
        ).get("code")
        if code != base_code:
            changes.append((factor, shock, code))
    return base_code, changes
