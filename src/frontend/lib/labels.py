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


from lib.ui import (
    fmt_int as fmt_count,
    fmt_limit,
    fmt_number,
    fmt_pct as fmt_ratio,
    fmt_percent_points,
)


def policy_name(code: str) -> str:
    label = POLICY_LABELS.get(str(code), str(code))
    return f"{label} ({code})"
