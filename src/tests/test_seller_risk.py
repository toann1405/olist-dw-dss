"""Seller risk KPIs come from M2 simulate, not a second formula."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "src" / "frontend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(FRONT))

from pages.seller_risk import _attach, _kpi_numbers  # noqa: E402
from src.dss.policy import PolicyParams, simulate  # noqa: E402


def _sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "seller_id": ["a", "b", "c"],
            "p_bad": [0.25, 0.40, 0.10],
            "n_orders_valid": [10, 10, 10],
            "gmv": [100.0, 200.0, 300.0],
            "late_ship_rate": [0.1, 0.1, 0.1],
            "avg_review": [4.0, 4.0, 4.0],
        }
    )


def test_kpis_match_simulate_on_three_sellers():
    frame = _sample()
    scored, scenario = _attach(frame, min_orders=5)
    stats = _kpi_numbers(scored, scored, scenario)
    expected = simulate(frame, "P2", PolicyParams(min_orders=5))
    assert stats["n_flagged"] == 2
    assert stats["tiers"][1] == 1
    assert stats["tiers"][2] == 1
    assert stats["gmv_affected_pct"] == expected.gmv_affected_pct
    assert int(scored["flagged"].sum()) == expected.n_sellers_flagged
    assert list(pd.to_numeric(scored["baseline_bad"])) == [2.5, 4.0, 1.0]
