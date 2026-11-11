"""Wilson interval and Pareto share tests. No warehouse."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

FRONT = Path(__file__).resolve().parents[1] / "frontend"
sys.path.insert(0, str(FRONT))

from lib.stats import pareto, wilson_ci  # noqa: E402


def test_wilson_known_center():
    low, high = wilson_ci(50, 100)
    assert low is not None and high is not None
    assert abs(((low + high) / 2) - 0.5) < 0.01
    assert low < 0.5 < high
    assert abs(low - 0.4038) < 0.01
    assert abs(high - 0.5962) < 0.01


def test_wilson_edges_and_empty():
    low, high = wilson_ci(0, 10)
    assert low == 0.0
    assert high is not None and high > 0
    low, high = wilson_ci(10, 10)
    assert high == 1.0
    assert wilson_ci(1, 0) == (None, None)
    assert wilson_ci(None, 10) == (None, None)


def test_pareto_shares_end_at_one():
    frame = pd.DataFrame({"seller_id": ["a", "b", "c"], "bad_orders": [1, 1, 2]})
    ranked = pareto(frame)
    assert abs(float(ranked["bad_share"].iloc[-1]) - 1.0) < 1e-9
    assert abs(float(ranked["seller_share"].iloc[-1]) - 1.0) < 1e-9
    assert list(ranked["bad_orders"]) == [2, 1, 1]
    assert abs(float(ranked["seller_share"].sum()) - (1 / 3 + 2 / 3 + 1)) < 1e-9
