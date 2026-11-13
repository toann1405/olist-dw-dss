"""One- or two-sentence conclusions built only from a frame already loaded."""

from __future__ import annotations

import pandas as pd

NOT_ENOUGH = "Chưa đủ dữ liệu để kết luận."
TOTAL = "__total__"


def _missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def _num(value):
    if _missing(value):
        return None
    return float(value)


from lib.ui import (
    fmt_int as _int,
    fmt_number as _decimal,
    fmt_pct as _pct,
    fmt_percent_points as _already_pct,
)


def _rate(numerator, denominator):
    top = _num(numerator)
    bottom = _num(denominator)
    if top is None or bottom is None or bottom <= 0:
        return None
    return top / bottom


def _eligible(frame: pd.DataFrame, min_orders: int) -> pd.DataFrame:
    work = frame.copy()
    work["eligible_orders"] = pd.to_numeric(work["eligible_orders"], errors="coerce")
    work["bad_orders"] = pd.to_numeric(work["bad_orders"], errors="coerce")
    work = work[work["eligible_orders"] >= int(min_orders)]
    work = work.dropna(subset=["bad_orders", "eligible_orders"])
    return work


def _groups(frame: pd.DataFrame, min_orders: int) -> tuple[pd.Series | None, pd.DataFrame]:
    if frame is None or frame.empty or "region_name" not in frame.columns:
        return None, frame.iloc[0:0] if frame is not None else pd.DataFrame()
    work = frame.copy()
    if "is_total" in work.columns:
        total_rows = work[pd.to_numeric(work["is_total"], errors="coerce").fillna(0).astype(int) == 1]
        groups = work[pd.to_numeric(work["is_total"], errors="coerce").fillna(0).astype(int) == 0]
    else:
        total_rows = work[work["region_name"].astype(str) == TOTAL]
        groups = work[work["region_name"].astype(str) != TOTAL]
    total = None if total_rows.empty else total_rows.iloc[0]
    return total, _eligible(groups, min_orders)


def _worst_group(groups: pd.DataFrame) -> pd.Series:
    ranked = groups.copy()
    ranked["rate"] = ranked.apply(lambda row: _rate(row["bad_orders"], row["eligible_orders"]), axis=1)
    ranked = ranked.dropna(subset=["rate"])
    ranked = ranked.sort_values(["rate", "eligible_orders", "region_name"], ascending=[False, False, True])
    return ranked.iloc[0]


def build_insight_kpi(frame: pd.DataFrame, min_orders: int) -> str:
    """Marketplace bad-experience rate, then the region with the highest rate."""
    total, groups = _groups(frame, min_orders)
    if total is None or groups.empty:
        return NOT_ENOUGH
    overall_n = _num(total["eligible_orders"])
    overall = _rate(total["bad_orders"], total["eligible_orders"])
    if overall is None or overall_n is None or overall_n < int(min_orders):
        return NOT_ENOUGH
    worst = _worst_group(groups)
    if len(groups) == 1:
        return (
            f"Tỷ lệ đơn trải nghiệm xấu tại vùng {worst['region_name']} là "
            f"{_pct(worst['rate'])} (n={_int(worst['eligible_orders'])})."
        )
    return (
        f"Tỷ lệ đơn trải nghiệm xấu {_pct(overall)}, cao nhất ở {worst['region_name']} "
        f"({_pct(worst['rate'])}, n={_int(worst['eligible_orders'])})."
    )


def build_insight_olap(frame: pd.DataFrame, min_orders: int) -> str:
    """Where bad experience is highest, and that group's share of GMV."""
    total, groups = _groups(frame, min_orders)
    if groups.empty:
        return NOT_ENOUGH
    worst = _worst_group(groups)
    sentence = (
        f"Trải nghiệm xấu cao nhất ở {worst['region_name']} "
        f"({_pct(worst['rate'])}, n={_int(worst['eligible_orders'])})."
    )
    if total is None or "gmv" not in frame.columns:
        return sentence
    total_gmv = _num(total["gmv"])
    group_gmv = _num(worst["gmv"]) if "gmv" in worst.index else None
    share = _rate(group_gmv, total_gmv)
    if share is None:
        return sentence
    return sentence + f" Nhóm này chiếm {_pct(share)} GMV trong bộ lọc."


def build_insight_risk(frame: pd.DataFrame, min_orders: int) -> str:
    """Seller with the highest M1 score among those meeting min_orders."""
    if frame is None or frame.empty:
        return NOT_ENOUGH
    work = frame.copy()
    work["n_orders_valid"] = pd.to_numeric(work["n_orders_valid"], errors="coerce")
    work["p_bad"] = pd.to_numeric(work["p_bad"], errors="coerce")
    work = work[work["n_orders_valid"] >= int(min_orders)].dropna(subset=["p_bad", "seller_id"])
    if work.empty:
        return NOT_ENOUGH
    top = work.sort_values(["p_bad", "n_orders_valid"], ascending=[False, False]).iloc[0]
    return (
        f"Seller {top['seller_id']} có điểm rủi ro cao nhất ({_pct(top['p_bad'])}), "
        f"với {_int(top['n_orders_valid'])} đơn hợp lệ trong tháng chấm."
    )


def recommend_policy(frame: pd.DataFrame, x_limit: float, n_limit: float) -> dict:
    """Pick the feasible non-baseline policy with the fewest expected bad orders.

    A tie keeps every code that shares that count. The radio default is the
    first of those codes in alphabetical order. The sentence is built only
    from the frame. X and N are the locked ceilings, not a second formula.
    """
    from lib.labels import fmt_count, fmt_limit, fmt_number, fmt_percent_points, policy_name

    empty = {"code": None, "tied": (), "sentence": NOT_ENOUGH}
    if frame is None or frame.empty:
        return empty
    work = frame.copy()
    work["expected_bad_orders"] = pd.to_numeric(work["expected_bad_orders"], errors="coerce")
    work["gmv_affected_pct"] = pd.to_numeric(work["gmv_affected_pct"], errors="coerce")
    work["n_sellers_flagged"] = pd.to_numeric(work["n_sellers_flagged"], errors="coerce")
    work["meets_x"] = work["meets_x"].map(lambda value: bool(value) if not _missing(value) else False)
    work["meets_n"] = work["meets_n"].map(lambda value: bool(value) if not _missing(value) else False)
    work["policy_code"] = work["policy_code"].astype(str)
    feasible = work[
        (work["policy_code"] != "P0") & work["meets_x"] & work["meets_n"]
    ].dropna(subset=["expected_bad_orders"])
    if feasible.empty:
        return {
            "code": None,
            "tied": (),
            "sentence": (
                f"Không có phương án nào đạt cả hai ràng buộc: "
                f"GMV bị ảnh hưởng ≤ {fmt_limit(x_limit)}% và số seller ≤ {fmt_limit(n_limit)}."
            ),
        }
    best_value = float(feasible["expected_bad_orders"].min())
    tied = feasible[feasible["expected_bad_orders"] == best_value].sort_values("policy_code")
    chosen = tied.iloc[0]
    codes = tuple(tied["policy_code"].tolist())
    names = " và ".join(policy_name(code) for code in codes)
    base_rows = work[work["policy_code"] == "P0"].dropna(subset=["expected_bad_orders"])
    base = None if base_rows.empty else float(base_rows.iloc[0]["expected_bad_orders"])
    saved = None if base is None else base - float(chosen["expected_bad_orders"])
    if saved is None:
        change = f"còn {fmt_number(chosen['expected_bad_orders'])} đơn xấu dự kiến"
    elif saved >= 0:
        change = f"giảm ~{fmt_number(saved)} đơn xấu"
    else:
        change = f"tăng ~{fmt_number(abs(saved))} đơn xấu"
    if base not in (None, 0) and saved is not None:
        change += f" ({fmt_percent_points(saved / base * 100)} so với {policy_name('P0')})"
    same = "cùng " if len(codes) > 1 else ""
    sentence = (
        f"{names} {same}{change}, "
        f"GMV ảnh hưởng {fmt_percent_points(chosen['gmv_affected_pct'])} "
        f"(≤{fmt_limit(x_limit)}%), "
        f"{fmt_count(chosen['n_sellers_flagged'])} seller (≤{fmt_limit(n_limit)}) "
        f"→ đạt cả hai ràng buộc."
    )
    return {"code": str(chosen["policy_code"]), "tied": codes, "sentence": sentence}


def build_insight_policy(frame: pd.DataFrame) -> str:
    """Feasible non-P0 policy with the lowest expected bad-order count."""
    if frame is None or frame.empty:
        return NOT_ENOUGH
    work = frame.copy()
    work["expected_bad_orders"] = pd.to_numeric(work["expected_bad_orders"], errors="coerce")
    work["meets_x"] = work["meets_x"].map(lambda value: bool(value) if not _missing(value) else False)
    work["meets_n"] = work["meets_n"].map(lambda value: bool(value) if not _missing(value) else False)
    feasible = work[
        (work["policy_code"].astype(str) != "P0") & work["meets_x"] & work["meets_n"]
    ].dropna(subset=["expected_bad_orders"])
    if feasible.empty:
        return "Chưa có phương án nào vừa trần GMV vừa trần số seller."
    best = feasible.sort_values(["expected_bad_orders", "policy_code"], ascending=[True, True]).iloc[0]
    gmv = _num(best["gmv_affected_pct"])
    sellers = _num(best["n_sellers_flagged"])
    sentence = (
        f"Phương án {best['policy_code']} cho số đơn xấu dự kiến thấp nhất "
        f"({_decimal(best['expected_bad_orders'])})"
    )
    if gmv is None or sellers is None:
        return sentence + " và còn trong cả hai trần."
    return (
        sentence
        + f", GMV bị ảnh hưởng {_already_pct(gmv)}, {_int(sellers)} seller bị xử lý, "
        + "và còn trong cả hai trần."
    )
