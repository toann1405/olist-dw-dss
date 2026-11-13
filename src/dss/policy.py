"""Policy simulation M2: P0, P1, P2, goal seeking, and a sensitivity table.

expected_bad_orders = sum(p_i * Q_i * (1 - e_k))
Q_i = n_orders_valid * s
GMV affected for a flagged seller is gmv * (1 - r).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

from src.dss.params import (
    AVG_REVIEW_THRESHOLD,
    BISECTION_TOL,
    E1,
    E2,
    E3,
    E_P1,
    LATE_SHIP_THRESHOLD,
    MIN_ORDERS,
    N,
    R,
    S,
    THETA_1,
    THETA_2,
    THETA_3,
    THETA_HI,
    TIER_GAP_2,
    TIER_GAP_3,
    X,
)


@dataclass(frozen=True)
class PolicyParams:
    theta_1: float = THETA_1
    theta_2: float = THETA_2
    theta_3: float = THETA_3
    e1: float = E1
    e2: float = E2
    e3: float = E3
    e_p1: float = E_P1
    late_ship_threshold: float = LATE_SHIP_THRESHOLD
    avg_review_threshold: float = AVG_REVIEW_THRESHOLD
    r: float = R
    s: float = S
    min_orders: int = MIN_ORDERS
    x_limit: float = X
    n_limit: int = N


@dataclass(frozen=True)
class Scenario:
    policy_code: str
    expected_bad_orders: float
    gmv_affected_pct: float | None
    n_sellers_flagged: int
    meets_x: bool
    meets_n: bool
    sellers: pd.DataFrame


@dataclass(frozen=True)
class BudgetSeekResult:
    params: PolicyParams
    scenario: Scenario
    k: int
    binding: str


def _clip01(value: float) -> float:
    return float(min(1.0, max(0.0, value)))


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    """Copy the scored sellers and coerce the columns M2 reads."""
    out = frame.copy()
    out["p_bad"] = pd.to_numeric(out["p_bad"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    out["n_orders_valid"] = pd.to_numeric(out["n_orders_valid"], errors="coerce").fillna(0).astype(int)
    out["q_bar"] = out["n_orders_valid"].astype(float)
    out["gmv"] = pd.to_numeric(out["gmv"], errors="coerce").fillna(0.0)
    out["late_ship_rate"] = pd.to_numeric(out["late_ship_rate"], errors="coerce")
    out["avg_review"] = pd.to_numeric(out["avg_review"], errors="coerce")
    if "seller_id" not in out.columns:
        out["seller_id"] = out["seller_key"].astype(str)
    return out


def _cap(out: pd.DataFrame, rank_column: str, n_limit: int) -> pd.DataFrame:
    flagged_index = out.index[out["flagged"]]
    if n_limit < 0 or len(flagged_index) <= n_limit:
        return out
    ranked = out.loc[flagged_index].sort_values(
        [rank_column, "seller_id"],
        ascending=[False, True],
        na_position="last",
    )
    drop_index = ranked.index[n_limit:]
    out.loc[drop_index, "flagged"] = False
    out.loc[drop_index, "tier"] = 0
    return out


def _effects(out: pd.DataFrame, policy_code: str, params: PolicyParams) -> pd.Series:
    if policy_code == "P1":
        effect = np.where(out["flagged"], _clip01(params.e_p1), 0.0)
        return pd.Series(effect, index=out.index)
    by_tier = {
        1: _clip01(params.e1),
        2: _clip01(params.e2),
        3: _clip01(params.e3),
    }
    return out["tier"].map(lambda tier: by_tier.get(int(tier), 0.0)).astype(float)


def simulate(frame: pd.DataFrame, policy_code: str, params: PolicyParams) -> Scenario:
    """Score one policy. Sellers above N are dropped, worst sellers kept."""
    out = prepare(frame)
    eligible = out["n_orders_valid"] >= int(params.min_orders)
    if policy_code == "P0":
        out["tier"] = 0
        out["flagged"] = False
    elif policy_code == "P1":
        late = out["late_ship_rate"] >= params.late_ship_threshold
        review = out["avg_review"] <= params.avg_review_threshold
        out["flagged"] = eligible & (late.fillna(False) | review.fillna(False))
        out["tier"] = out["flagged"].astype(int)
        out = _cap(out, "late_ship_rate", int(params.n_limit))
    elif policy_code == "P2":
        low, mid, high = sorted((params.theta_1, params.theta_2, params.theta_3))
        probability = out["p_bad"]
        tier = np.where(
            probability >= high,
            3,
            np.where(probability >= mid, 2, np.where(probability >= low, 1, 0)),
        )
        out["tier"] = np.where(eligible, tier, 0).astype(int)
        out["flagged"] = out["tier"] > 0
        out = _cap(out, "p_bad", int(params.n_limit))
    else:
        raise ValueError(f"Unknown policy {policy_code}")

    transfer = _clip01(params.r)
    season = max(float(params.s), 0.0)
    out["e_k"] = _effects(out, policy_code, params)
    out["q_i"] = out["q_bar"] * season
    out["expected_bad_i"] = out["p_bad"] * out["q_i"] * (1.0 - out["e_k"])
    out["gmv_affected_i"] = np.where(out["flagged"], out["gmv"] * (1.0 - transfer), 0.0)

    total_gmv = float(out["gmv"].sum())
    affected = float(out["gmv_affected_i"].sum())
    pct = None if total_gmv <= 0 else 100.0 * affected / total_gmv
    n_flagged = int(out["flagged"].sum())
    return Scenario(
        policy_code=policy_code,
        expected_bad_orders=float(out["expected_bad_i"].sum()),
        gmv_affected_pct=pct,
        n_sellers_flagged=n_flagged,
        meets_x=pct is not None and pct <= float(params.x_limit) + 1e-9,
        meets_n=n_flagged <= int(params.n_limit),
        sellers=out,
    )


def compare_policies(frame: pd.DataFrame, params: PolicyParams) -> list[Scenario]:
    return [simulate(frame, code, params) for code in ("P0", "P1", "P2")]


def _with_theta(params: PolicyParams, theta_1: float) -> PolicyParams:
    theta = float(min(THETA_HI, max(0.0, theta_1)))
    return replace(
        params,
        theta_1=theta,
        theta_2=min(1.0, theta + TIER_GAP_2),
        theta_3=min(1.0, theta + TIER_GAP_3),
    )


def goal_seek(frame: pd.DataFrame, params: PolicyParams) -> tuple[PolicyParams, Scenario]:
    """Smallest theta_1 whose P2 GMV share is still within X.

    theta_2 and theta_3 keep the default gaps 0.15 and 0.30.
    """
    lo = 0.0
    hi = THETA_HI
    if simulate(frame, "P2", _with_theta(params, lo)).meets_x:
        chosen = _with_theta(params, lo)
        return chosen, simulate(frame, "P2", chosen)
    if not simulate(frame, "P2", _with_theta(params, hi)).meets_x:
        chosen = _with_theta(params, hi)
        return chosen, simulate(frame, "P2", chosen)
    while hi - lo > BISECTION_TOL:
        mid = (lo + hi) / 2.0
        if simulate(frame, "P2", _with_theta(params, mid)).meets_x:
            hi = mid
        else:
            lo = mid
    chosen = _with_theta(params, hi)
    return chosen, simulate(frame, "P2", chosen)


def _with_theta_exact(params: PolicyParams, theta_1: float) -> PolicyParams:
    theta = float(min(1.0, max(0.0, theta_1)))
    return replace(
        params,
        theta_1=theta,
        theta_2=min(1.0, theta + TIER_GAP_2),
        theta_3=min(1.0, theta + TIER_GAP_3),
    )


def budget_seek(frame: pd.DataFrame, params: PolicyParams) -> BudgetSeekResult:
    """Largest k <= n_limit of eligible sellers by p_bad with GMV impact <= x_limit."""
    out = prepare(frame)
    eligible = out[out["n_orders_valid"] >= int(params.min_orders)].copy()
    ranked = eligible.sort_values(
        ["p_bad", "seller_id"],
        ascending=[False, True],
        na_position="last",
    ).reset_index(drop=True)

    total_gmv = float(out["gmv"].sum())
    max_k = min(len(ranked), max(0, int(params.n_limit)))
    if max_k == 0 or total_gmv <= 0:
        chosen = _with_theta_exact(params, 1.0)
        sought = simulate(out, "P2", chosen)
        return BudgetSeekResult(
            params=chosen,
            scenario=sought,
            k=0,
            binding="X" if total_gmv <= 0 else "N",
        )

    transfer = _clip01(params.r)
    cum_gmv = 0.0
    best_k = 0
    for idx in range(max_k):
        cum_gmv += float(ranked.loc[idx, "gmv"]) * (1.0 - transfer)
        pct = 100.0 * cum_gmv / total_gmv
        if pct <= float(params.x_limit) + 1e-9:
            best_k = idx + 1
        else:
            break

    binding = "X" if best_k < max_k else "N"
    if binding == "X" and 0 < best_k < len(ranked):
        boundary_p = float(ranked.loc[best_k - 1, "p_bad"])
        if float(ranked.loc[best_k, "p_bad"]) == boundary_p:
            while best_k > 0 and float(ranked.loc[best_k - 1, "p_bad"]) == boundary_p:
                best_k -= 1

    theta_1 = 1.0 if best_k == 0 else float(ranked.loc[best_k - 1, "p_bad"])
    chosen = _with_theta_exact(params, theta_1)
    sought = simulate(out, "P2", chosen)
    return BudgetSeekResult(params=chosen, scenario=sought, k=best_k, binding=binding)


def budget_curve(frame: pd.DataFrame, params: PolicyParams) -> pd.DataFrame:
    """Expected bad orders and GMV impact when flagging top k=1..n_limit eligible sellers."""
    out = prepare(frame)
    eligible = out[out["n_orders_valid"] >= int(params.min_orders)].copy()
    ranked = eligible.sort_values(
        ["p_bad", "seller_id"],
        ascending=[False, True],
        na_position="last",
    ).reset_index(drop=True)
    max_k = min(len(ranked), max(0, int(params.n_limit)))
    rows = []
    for k in range(1, max_k + 1):
        theta_1 = float(ranked.loc[k - 1, "p_bad"])
        step_params = replace(_with_theta_exact(params, theta_1), n_limit=k)
        res = simulate(out, "P2", step_params)
        rows.append(
            {
                "k": k,
                "theta_1": step_params.theta_1,
                "expected_bad_orders": res.expected_bad_orders,
                "gmv_affected_pct": res.gmv_affected_pct,
                "meets_x": res.meets_x,
            }
        )
    return pd.DataFrame(rows)


def efficiency(scenario: Scenario, baseline: Scenario | float) -> float | None:
    """Bad orders reduced per percentage point of affected GMV; None if GMV impact is zero."""
    if scenario is None or baseline is None:
        return None
    gmv_pct = scenario.gmv_affected_pct
    if gmv_pct is None or pd.isna(gmv_pct) or float(gmv_pct) == 0.0:
        return None
    base_bad = float(baseline.expected_bad_orders) if hasattr(baseline, "expected_bad_orders") else float(baseline)
    reduced = base_bad - float(scenario.expected_bad_orders)
    return reduced / float(gmv_pct)


def _scale_effects(params: PolicyParams, factor: float) -> PolicyParams:
    return replace(
        params,
        e1=_clip01(params.e1 * factor),
        e2=_clip01(params.e2 * factor),
        e3=_clip01(params.e3 * factor),
        e_p1=_clip01(params.e_p1 * factor),
    )


def tornado(frame: pd.DataFrame, params: PolicyParams) -> pd.DataFrame:
    """P2 results when e_k, r, or s moves by 20 percent. One row per shock."""
    rows = []
    shocks = (("e_k", "effect"), ("r", "transfer"), ("s", "season"))
    for name, kind in shocks:
        for factor, label in ((0.8, "low"), (1.0, "base"), (1.2, "high")):
            if kind == "effect":
                shifted = _scale_effects(params, factor)
            elif kind == "transfer":
                shifted = replace(params, r=_clip01(params.r * factor))
            else:
                shifted = replace(params, s=max(params.s * factor, 0.0))
            result = simulate(frame, "P2", shifted)
            rows.append(
                {
                    "factor": name,
                    "shock": label,
                    "multiplier": factor,
                    "expected_bad_orders": result.expected_bad_orders,
                    "gmv_affected_pct": result.gmv_affected_pct,
                    "n_sellers_flagged": result.n_sellers_flagged,
                }
            )
    return pd.DataFrame(rows)


def scenario_record(result: Scenario, params: PolicyParams, as_of_month: str, scored_at) -> dict:
    """One policy_scenario row, including the parameters that produced it."""
    return {
        "as_of_month": as_of_month,
        "policy_code": result.policy_code,
        "theta_1": params.theta_1,
        "theta_2": params.theta_2,
        "theta_3": params.theta_3,
        "e1": params.e1,
        "e2": params.e2,
        "e3": params.e3,
        "e_p1": params.e_p1,
        "late_ship_threshold": params.late_ship_threshold,
        "avg_review_threshold": params.avg_review_threshold,
        "r": params.r,
        "s": params.s,
        "min_orders": int(params.min_orders),
        "x_limit": params.x_limit,
        "n_limit": int(params.n_limit),
        "expected_bad_orders": result.expected_bad_orders,
        "gmv_affected_pct": result.gmv_affected_pct,
        "n_sellers_flagged": result.n_sellers_flagged,
        "meets_x": result.meets_x,
        "meets_n": result.meets_n,
        "scored_at": scored_at,
    }
