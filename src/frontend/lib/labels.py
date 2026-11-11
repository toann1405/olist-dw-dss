"""Display names and number formats. Calculations keep the original column names."""

from __future__ import annotations

POLICY_LABELS = {
    "P0": "Không can thiệp",
    "P1": "Ngưỡng KPI cố định",
    "P2": "Điểm rủi ro dự báo",
}

POLICY_BLURB = {
    "P0": "Giữ nguyên, làm mốc so sánh.",
    "P1": "Xử lý seller giao trễ nhiều hoặc điểm review thấp.",
    "P2": "Xử lý seller có điểm rủi ro dự báo cao.",
}

COLUMN_LABELS = {
    "expected_bad_orders": "Đơn xấu dự kiến",
    "gmv_affected_pct": "GMV bị ảnh hưởng (%)",
    "n_sellers_flagged": "Số seller bị xử lý",
    "p_bad": "Điểm rủi ro",
    "n_orders_valid": "Số đơn hợp lệ",
    "e_k": "Hiệu quả can thiệp dự kiến",
    "seller_id": "Seller",
    "tier": "Hạng",
    "gmv": "GMV",
    "late_ship_rate": "Tỷ lệ bàn giao trễ",
    "avg_review": "Điểm review trung bình",
    "policy_code": "Phương án",
    "decided_at": "Thời điểm",
    "note": "Lý do",
    "as_of_month": "Tháng chấm",
    "meets_x": "Đạt trần GMV",
    "meets_n": "Đạt trần số seller",
    "theta_1": "Ngưỡng hạng 1",
    "theta_2": "Ngưỡng hạng 2",
    "theta_3": "Ngưỡng hạng 3",
    "min_orders": "Số đơn tối thiểu",
    "x_limit": "Trần GMV (%)",
    "n_limit": "Trần số seller",
    "scored_at": "Thời điểm job chạy",
    "q_bar": "Đơn kỳ vọng",
    "model_name": "Mô hình",
    "trained_through_month": "Học đến tháng",
}

FACTOR_LABELS = {
    "e_k": "Hiệu quả can thiệp",
    "r": "Tỷ lệ chuyển đơn",
    "s": "Hệ số mùa vụ",
}

# Rates stored on 0–1. GMV impact from M2 is already on a 0–100 scale.
RATIO_COLUMNS = {"p_bad", "late_ship_rate", "e_k"}
POINT_COLUMNS = {"gmv_affected_pct", "x_limit"}


def policy_name(code: str) -> str:
    label = POLICY_LABELS.get(str(code), str(code))
    return f"{label} ({code})"


def _missing(value) -> bool:
    if value is None:
        return True
    try:
        import pandas as pd

        return bool(pd.isna(value))
    except TypeError:
        return False


def _group(text: str) -> str:
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_count(value) -> str:
    if _missing(value):
        return "—"
    return _group(f"{int(round(float(value))):,}")


def fmt_number(value) -> str:
    """One decimal, thousands grouped, Vietnamese separators."""
    if _missing(value):
        return "—"
    return _group(f"{float(value):,.1f}")


def fmt_percent_points(value) -> str:
    """A percent already on a 0–100 scale."""
    if _missing(value):
        return "—"
    number = float(value)
    sign = "−" if number < 0 else ""
    return f"{sign}{_group(f'{abs(number):,.1f}')}%"


def fmt_ratio(value) -> str:
    """A ratio on 0–1, shown as a percent with one decimal."""
    if _missing(value):
        return "—"
    return fmt_percent_points(float(value) * 100)


def fmt_limit(value) -> str:
    if _missing(value):
        return "—"
    number = float(value)
    if number == int(number):
        return fmt_count(number)
    return fmt_number(number)
