"""M1 logistic regression on seller-months from dss.v_seller_features.

The label is the next calendar month's bad-experience orders. Each eligible
order becomes one training row so the fit matches a binomial likelihood.
The time split keeps the last two year_month values as the test set.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

from src.dss.params import RANDOM_STATE

NUMERIC_FEATURES = (
    "late_ship_rate_3m",
    "avg_review",
    "n_orders_valid",
    "avg_distance_km",
    "seller_age_days",
)
CATEGORY_FEATURES = ("category_group", "region_name")
MIN_ITEMS = 10
MIN_ACTIVE_MONTHS = 6
TEST_MONTHS = 2


def next_month_key(month_key: int) -> int:
    year, month = divmod(int(month_key), 100)
    if month == 12:
        return (year + 1) * 100 + 1
    return year * 100 + month + 1


def _labeled(features: pd.DataFrame) -> pd.DataFrame:
    frame = features.copy()
    frame["seller_key"] = pd.to_numeric(frame["seller_key"], errors="coerce")
    frame["month_key"] = pd.to_numeric(frame["month_key"], errors="coerce")
    frame = frame.dropna(subset=["month_key", "seller_key"]).copy()
    frame["seller_key"] = frame["seller_key"].astype(int)
    frame["month_key"] = frame["month_key"].astype(int)
    frame["next_month_key"] = frame["month_key"].map(next_month_key)
    label = frame[
        ["seller_key", "month_key", "bad_experience_count", "bad_experience_eligible"]
    ].rename(
        columns={
            "month_key": "next_month_key",
            "bad_experience_count": "label_bad",
            "bad_experience_eligible": "label_eligible",
        }
    )
    merged = frame.merge(label, on=["seller_key", "next_month_key"], how="inner")
    merged["label_bad"] = pd.to_numeric(merged["label_bad"], errors="coerce").fillna(0)
    merged["label_eligible"] = pd.to_numeric(merged["label_eligible"], errors="coerce").fillna(0)
    return merged[merged["label_eligible"] > 0].copy()


def _train_population(features: pd.DataFrame) -> set:
    active = features.copy()
    active["seller_key"] = pd.to_numeric(active["seller_key"], errors="coerce")
    active = active.dropna(subset=["seller_key"])
    active["seller_key"] = active["seller_key"].astype(int)
    active["n_items_valid"] = pd.to_numeric(active["n_items_valid"], errors="coerce").fillna(0)
    counts = (
        active[active["n_items_valid"] >= MIN_ITEMS]
        .groupby("seller_key")["month_key"]
        .nunique()
    )
    return set(counts[counts >= MIN_ACTIVE_MONTHS].index)


def _design_matrix(
    frame: pd.DataFrame,
    medians: pd.Series | None,
    columns: list[str] | None,
) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    numeric = frame.loc[:, list(NUMERIC_FEATURES)].apply(pd.to_numeric, errors="coerce")
    if medians is None:
        medians = numeric.median(numeric_only=True)
    numeric = numeric.fillna(medians).fillna(0.0)
    categories = frame.loc[:, list(CATEGORY_FEATURES)].fillna("Unknown").astype(str)
    dummies = pd.get_dummies(categories, dtype=float)
    matrix = pd.concat([numeric.reset_index(drop=True), dummies.reset_index(drop=True)], axis=1)
    if columns is None:
        columns = list(matrix.columns)
    matrix = matrix.reindex(columns=columns, fill_value=0.0)
    return matrix, medians, columns


def _expand(matrix: pd.DataFrame, bad: np.ndarray, eligible: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    eligible = np.maximum(eligible.astype(int), 0)
    bad = np.minimum(np.maximum(bad.astype(int), 0), eligible)
    repeats = eligible
    total = int(repeats.sum())
    if total <= 0:
        return np.empty((0, matrix.shape[1])), np.empty(0, dtype=int)
    index = np.repeat(np.arange(len(matrix)), repeats)
    starts = np.cumsum(repeats) - repeats
    position = np.arange(total) - np.repeat(starts, repeats)
    outcome = (position < np.repeat(bad.astype(int), repeats)).astype(int)
    return matrix.to_numpy(dtype=float)[index], outcome


def _baseline_scores(latest: pd.DataFrame, reason: str, scored_at: datetime) -> tuple[pd.DataFrame, dict]:
    eligible = pd.to_numeric(latest["bad_experience_eligible"], errors="coerce").fillna(0)
    bad = pd.to_numeric(latest["bad_experience_count"], errors="coerce").fillna(0)
    rate = np.where(eligible > 0, bad / eligible, np.nan)
    scores = _score_frame(latest, rate, "baseline_rate", None, scored_at)
    metrics = {
        "model_name": "baseline_rate",
        "reason": reason,
        "auc": None,
        "brier": None,
        "n_train_orders": 0,
        "n_test_orders": 0,
        "trained_through_month": None,
        "as_of_month": scores["as_of_month"].iloc[0] if len(scores) else None,
    }
    return scores, metrics


def _score_frame(
    latest: pd.DataFrame,
    probability: np.ndarray,
    model_name: str,
    trained_through_month: str | None,
    scored_at: datetime,
) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "seller_key": latest["seller_key"].to_numpy(),
            "seller_id": latest["seller_id"].astype(str).to_numpy(),
            "as_of_month": latest["year_month"].astype(str).to_numpy(),
            "p_bad": probability,
            "q_bar": pd.to_numeric(latest["n_orders_valid"], errors="coerce").fillna(0).to_numpy(),
            "gmv": pd.to_numeric(latest["gmv"], errors="coerce").fillna(0).to_numpy(dtype=float),
            "late_ship_rate": pd.to_numeric(latest["late_ship_rate"], errors="coerce").to_numpy(),
            "avg_review": pd.to_numeric(latest["avg_review"], errors="coerce").to_numpy(),
            "n_orders_valid": pd.to_numeric(latest["n_orders_valid"], errors="coerce").fillna(0).astype(int).to_numpy(),
            "model_name": model_name,
            "trained_through_month": trained_through_month,
            "scored_at": scored_at,
        }
    )
    return out


def train_and_score(features: pd.DataFrame, as_of_month: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Fit on history up to as_of_month and score every seller in that month."""
    from src.dss.params import AS_OF_MONTH

    scored_at = datetime.now(timezone.utc).replace(tzinfo=None)
    chosen = str(as_of_month or AS_OF_MONTH)
    if not features.empty and "year_month" in features.columns:
        features = features[features["year_month"].astype(str) <= chosen].copy()
    if features.empty:
        metrics = {
            "model_name": "baseline_rate",
            "reason": "no feature rows",
            "auc": None,
            "brier": None,
            "n_train_orders": 0,
            "n_test_orders": 0,
            "trained_through_month": None,
            "as_of_month": None,
        }
        return pd.DataFrame(), metrics

    latest = features[features["year_month"].astype(str) == chosen].copy()
    if latest.empty:
        metrics = {
            "model_name": "baseline_rate",
            "reason": f"no sellers in {chosen}",
            "auc": None,
            "brier": None,
            "n_train_orders": 0,
            "n_test_orders": 0,
            "trained_through_month": None,
            "as_of_month": chosen,
        }
        return pd.DataFrame(), metrics
    labeled = _labeled(features)
    population = _train_population(features)
    labeled = labeled[labeled["seller_key"].isin(population)].copy()
    months = sorted(labeled["year_month"].astype(str).unique())
    if len(months) <= TEST_MONTHS:
        return _baseline_scores(latest, "fewer than three labeled months", scored_at)

    test_months = set(months[-TEST_MONTHS:])
    train_months = months[:-TEST_MONTHS]
    train_rows = labeled[labeled["year_month"].astype(str).isin(train_months)].copy()
    test_rows = labeled[labeled["year_month"].astype(str).isin(test_months)].copy()
    if train_rows.empty or test_rows.empty:
        return _baseline_scores(latest, "empty train or test split", scored_at)

    train_x, medians, columns = _design_matrix(train_rows, None, None)
    test_x, _, _ = _design_matrix(test_rows, medians, columns)
    train_matrix, train_y = _expand(
        train_x,
        train_rows["label_bad"].to_numpy(),
        train_rows["label_eligible"].to_numpy(),
    )
    test_matrix, test_y = _expand(
        test_x,
        test_rows["label_bad"].to_numpy(),
        test_rows["label_eligible"].to_numpy(),
    )
    if train_y.size == 0 or len(np.unique(train_y)) < 2:
        return _baseline_scores(latest, "training labels have one class", scored_at)

    model = LogisticRegression(random_state=RANDOM_STATE, max_iter=500, solver="lbfgs")
    model.fit(train_matrix, train_y)
    n_iter = np.atleast_1d(model.n_iter_)
    if int(n_iter.max()) >= 500:
        return _baseline_scores(latest, "logistic regression did not converge", scored_at)

    probability = model.predict_proba(test_matrix)[:, 1] if test_y.size else np.array([])
    auc = None
    brier = None
    if test_y.size and len(np.unique(test_y)) > 1:
        auc = float(roc_auc_score(test_y, probability))
        brier = float(brier_score_loss(test_y, probability))
    elif test_y.size:
        brier = float(brier_score_loss(test_y, probability))

    score_x, _, _ = _design_matrix(latest, medians, columns)
    scored = _score_frame(
        latest,
        model.predict_proba(score_x.to_numpy(dtype=float))[:, 1],
        "logistic",
        train_months[-1],
        scored_at,
    )
    metrics = {
        "model_name": "logistic",
        "reason": None,
        "auc": auc,
        "brier": brier,
        "n_train_orders": int(train_y.size),
        "n_test_orders": int(test_y.size),
        "trained_through_month": train_months[-1],
        "as_of_month": scored["as_of_month"].iloc[0] if len(scored) else None,
    }
    return scored, metrics
