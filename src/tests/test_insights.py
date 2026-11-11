"""Sample frames for the storytelling sentences. No warehouse."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "src" / "frontend"
sys.path.insert(0, str(FRONT))

from lib.glossary import GLOSSARY, HOME_TERMS, explain  # noqa: E402
from lib.insights import (  # noqa: E402
    NOT_ENOUGH,
    build_insight_kpi,
    build_insight_olap,
    build_insight_policy,
    build_insight_risk,
)


def _story() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"region_name": "__total__", "is_total": 1, "bad_orders": 20, "eligible_orders": 100, "gmv": 1000},
            {"region_name": "Norte", "is_total": 0, "bad_orders": 1, "eligible_orders": 4, "gmv": 50},
            {"region_name": "Sudeste", "is_total": 0, "bad_orders": 9, "eligible_orders": 30, "gmv": 600},
            {"region_name": "Sul", "is_total": 0, "bad_orders": 4, "eligible_orders": 40, "gmv": 350},
        ]
    )


def test_glossary_covers_home_terms():
    for term in HOME_TERMS:
        text = explain(term)
        assert GLOSSARY[term]["definition"] in text
        assert "Tử:" in text
        assert "Mẫu:" in text


def test_kpi_insight_skips_small_groups():
    text = build_insight_kpi(_story(), min_orders=5)
    assert "20,0%" in text
    assert "Sudeste" in text
    assert "30,0%" in text
    assert "n=30" in text
    assert "Norte" not in text


def test_kpi_insight_when_no_group_is_large_enough():
    assert build_insight_kpi(_story(), min_orders=50) == NOT_ENOUGH


def test_kpi_insight_empty():
    assert build_insight_kpi(pd.DataFrame(), min_orders=5) == NOT_ENOUGH


def test_olap_insight_adds_gmv_share():
    text = build_insight_olap(_story(), min_orders=5)
    assert "Sudeste" in text
    assert "60,0%" in text


def test_risk_insight_uses_min_orders():
    frame = pd.DataFrame(
        [
            {"seller_id": "small", "p_bad": 0.9, "n_orders_valid": 2},
            {"seller_id": "large", "p_bad": 0.4, "n_orders_valid": 8},
        ]
    )
    text = build_insight_risk(frame, min_orders=5)
    assert "large" in text
    assert "40,0%" in text
    assert "small" not in text
    assert build_insight_risk(frame, min_orders=20) == NOT_ENOUGH


def test_policy_insight_picks_feasible_non_baseline():
    frame = pd.DataFrame(
        [
            {"policy_code": "P0", "expected_bad_orders": 10, "meets_x": True, "meets_n": True, "gmv_affected_pct": 0, "n_sellers_flagged": 0},
            {"policy_code": "P1", "expected_bad_orders": 8, "meets_x": False, "meets_n": True, "gmv_affected_pct": 0.2, "n_sellers_flagged": 10},
            {"policy_code": "P2", "expected_bad_orders": 6.5, "meets_x": True, "meets_n": True, "gmv_affected_pct": 4.0, "n_sellers_flagged": 12},
        ]
    )
    text = build_insight_policy(frame)
    assert text.startswith("Phương án P2")
    assert "6,5" in text
    assert "4,0%" in text
    assert "12" in text


def test_policy_insight_when_nothing_fits():
    frame = pd.DataFrame(
        [
            {"policy_code": "P1", "expected_bad_orders": 8, "meets_x": False, "meets_n": True, "gmv_affected_pct": 0.2, "n_sellers_flagged": 3},
        ]
    )
    assert build_insight_policy(frame) == "Chưa có phương án nào vừa trần GMV vừa trần số seller."
    assert build_insight_policy(pd.DataFrame()) == NOT_ENOUGH
