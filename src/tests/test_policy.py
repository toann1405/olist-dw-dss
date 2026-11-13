"""Tests for budget_seek and efficiency in src.dss.policy. No warehouse."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.dss.params import TIER_GAP_2, TIER_GAP_3  # noqa: E402
from src.dss.policy import PolicyParams, budget_seek, efficiency, simulate  # noqa: E402


def test_budget_seek_binds_on_n():
    frame = pd.DataFrame(
        {
            "seller_id": [f"s{i}" for i in range(6)],
            "p_bad": [0.50, 0.40, 0.30, 0.25, 0.18, 0.10],
            "n_orders_valid": [10, 10, 10, 10, 10, 10],
            "gmv": [100.0] * 6,
            "late_ship_rate": [0.1] * 6,
            "avg_review": [4.0] * 6,
        }
    )
    params = PolicyParams(n_limit=3, x_limit=50.0, r=0.5, min_orders=5)
    result = budget_seek(frame, params)
    assert result.binding == "N"
    assert result.k == 3
    assert result.params.theta_1 == pytest.approx(0.30)
    assert result.params.theta_2 == pytest.approx(0.30 + TIER_GAP_2)
    assert result.params.theta_3 == pytest.approx(0.30 + TIER_GAP_3)
    assert result.scenario.n_sellers_flagged == 3
    assert result.scenario.meets_n is True
    assert result.scenario.meets_x is True


def test_budget_seek_binds_on_x():
    frame = pd.DataFrame(
        {
            "seller_id": ["s1", "s2", "s3", "s4"],
            "p_bad": [0.45, 0.35, 0.28, 0.15],
            "n_orders_valid": [10, 10, 10, 10],
            # Total GMV = 1000; r=0.5 -> each 100 GMV adds 5% affected GMV.
            "gmv": [120.0, 140.0, 200.0, 540.0],
            "late_ship_rate": [0.1] * 4,
            "avg_review": [4.0] * 4,
        }
    )
    # s1: 6.0%, s1+s2: 13.0% <= 15%, s1+s2+s3: 23.0% > 15% -> k=2, binding="X"
    params = PolicyParams(n_limit=4, x_limit=15.0, r=0.5, min_orders=5)
    result = budget_seek(frame, params)
    assert result.binding == "X"
    assert result.k == 2
    assert result.params.theta_1 == pytest.approx(0.35)
    assert result.params.theta_2 == pytest.approx(0.35 + TIER_GAP_2)
    assert result.params.theta_3 == pytest.approx(0.35 + TIER_GAP_3)
    assert result.scenario.n_sellers_flagged == 2
    assert result.scenario.gmv_affected_pct == pytest.approx(13.0)
    assert result.scenario.meets_x is True


def test_efficiency_returns_ratio_and_none_for_zero_gmv():
    frame = pd.DataFrame(
        {
            "seller_id": ["s1", "s2"],
            "p_bad": [0.40, 0.10],
            "n_orders_valid": [10, 10],
            "gmv": [200.0, 800.0],
            "late_ship_rate": [0.1, 0.1],
            "avg_review": [4.0, 4.0],
        }
    )
    params = PolicyParams(theta_1=0.20, e2=0.50, r=0.5, min_orders=5)
    p0 = simulate(frame, "P0", params)
    p2 = simulate(frame, "P2", params)
    # P0 expected bad = 4.0 + 1.0 = 5.0; P2 reduces s1 (tier 2, e2=0.5) by 2.0; gmv_affected_pct = 10.0%
    assert efficiency(p2, p0) == pytest.approx(0.2)
    assert efficiency(p0, p0) is None
