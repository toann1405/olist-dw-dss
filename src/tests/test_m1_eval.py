"""M1 calibration and factor contributions. No warehouse."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.dss.train import FEATURE_LABELS, train_and_score  # noqa: E402


def _months(start: tuple[int, int], count: int) -> list[tuple[int, str]]:
    year, month = start
    labels = []
    for _ in range(count):
        labels.append((year * 100 + month, f"{year:04d}-{month:02d}"))
        month += 1
        if month == 13:
            year += 1
            month = 1
    return labels


def _features(month_count: int) -> pd.DataFrame:
    rows = []
    sellers = (
        (1, "s1", "Sudeste", "beleza", 0.05, 4.6, 1),
        (2, "s2", "Nordeste", "casa", 0.50, 2.4, 4),
    )
    for seller_key, seller_id, region, category, late, review, bad_count in sellers:
        for month_key, year_month in _months((2018, 1), month_count):
            bump = 0.02 if month_key >= 201806 else 0.0
            rows.append(
                {
                    "seller_key": seller_key,
                    "seller_id": seller_id,
                    "month_key": month_key,
                    "year_month": year_month,
                    "n_orders_valid": 5,
                    "n_items_valid": 12,
                    "gmv": 100.0 * seller_key,
                    "late_ship_rate": late + bump,
                    "avg_review": review,
                    "bad_experience_count": bad_count,
                    "bad_experience_eligible": 5,
                    "region_name": region,
                    "has_closed_deal": 1,
                    "won_date": "2017-01-01",
                    "late_ship_rate_3m": late + bump,
                    "avg_distance_km": 80.0 * seller_key,
                    "category_group": category,
                    "seller_age_days": 300 + seller_key * 10,
                }
            )
    return pd.DataFrame(rows)


def test_baseline_returns_empty_diagnostics():
    _scores, metrics, calibration, contrib = train_and_score(_features(2), "2018-02")
    assert metrics["model_name"] == "baseline_rate"
    assert calibration.empty
    assert contrib.empty
    assert list(calibration.columns) == ["bin", "mean_pred", "observed_rate", "n"]
    assert list(contrib.columns) == ["seller_id", "feature", "value", "contribution"]


def test_calibration_counts_orders_and_contributions_match_logit():
    scores, metrics, calibration, contrib = train_and_score(_features(8), "2018-08")
    assert metrics["model_name"] == "logistic"
    assert metrics["test_months"] == ["2018-06", "2018-07"]
    assert 1 <= len(calibration) <= 10
    assert int(calibration["n"].sum()) == metrics["n_test_orders"]
    assert metrics["n_test_orders"] == 20
    assert set(contrib["seller_id"]) == set(scores["seller_id"].astype(str))
    assert FEATURE_LABELS["late_ship_rate_3m"] in set(contrib["feature"])
    assert "late_ship_rate_3m" not in set(contrib["feature"])

    intercept = float(metrics["intercept"])
    for seller_id, group in contrib.groupby("seller_id"):
        probability = float(scores.loc[scores["seller_id"] == seller_id, "p_bad"].iloc[0])
        assert 0.0 < probability < 1.0
        logit = float(np.log(probability / (1.0 - probability)))
        total = float(group["contribution"].sum()) + intercept
        assert abs(total - logit) < 1e-6
