"""Small statistical helpers. They do not query the warehouse."""

from __future__ import annotations

import math

import pandas as pd

# SPEC §3: months below 1,000 orders. The list is the published profile, not a new count.
SPARSE_MONTHS = ("2016-09", "2016-10", "2016-12", "2017-01", "2018-09", "2018-10")
DENSE_FROM = "2017-02"
DENSE_TO = "2018-08"


def wilson_ci(k, n, z: float = 1.96) -> tuple[float | None, float | None]:
    """Wilson score interval for a binomial proportion. Returns (low, high) on 0–1."""
    if n is None or k is None:
        return (None, None)
    try:
        if pd.isna(n) or pd.isna(k):
            return (None, None)
    except TypeError:
        pass
    sample = float(n)
    successes = float(k)
    if sample <= 0 or successes < 0 or successes > sample:
        return (None, None)
    proportion = successes / sample
    z2 = z * z
    denominator = 1.0 + z2 / sample
    center = (proportion + z2 / (2.0 * sample)) / denominator
    margin = z * math.sqrt((proportion * (1.0 - proportion) / sample) + z2 / (4.0 * sample * sample))
    margin = margin / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def pareto(frame: pd.DataFrame, value_column: str = "bad_orders") -> pd.DataFrame:
    """Cumulative seller share and cumulative bad-order share, worst sellers first.

    The last cumulative bad share is 1 when the total is positive.
    """
    if frame is None or frame.empty or value_column not in frame.columns:
        return pd.DataFrame(columns=["seller_share", "bad_share", "sellers", value_column])
    work = frame.copy()
    work[value_column] = pd.to_numeric(work[value_column], errors="coerce").fillna(0.0)
    work = work.sort_values(value_column, ascending=False).reset_index(drop=True)
    total = float(work[value_column].sum())
    count = len(work)
    work["sellers"] = range(1, count + 1)
    work["seller_share"] = work["sellers"] / count
    if total <= 0:
        work["bad_share"] = 0.0
    else:
        work["bad_share"] = work[value_column].cumsum() / total
    return work


def rolling_mean(values: pd.Series, window: int = 3) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.rolling(window, min_periods=window).mean()
