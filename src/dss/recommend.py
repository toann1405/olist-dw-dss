"""Simple action labels from a seller row and the platform rates.

Tier numbers come from M2. This module does not recompute thresholds or p_i.
"""

from __future__ import annotations

TIER_ACTION = {
    0: "Bình thường",
    1: "Theo dõi",
    2: "Cảnh báo + hỗ trợ",
    3: "Tạm ngưng hiển thị",
}


def action_for_tier(tier: int) -> str:
    return TIER_ACTION.get(int(tier), TIER_ACTION[0])


def reason_chips(late_ship_rate, avg_review, platform_late, platform_review) -> list[str]:
    """Name the gaps versus the platform. Missing values add no chip."""
    chips = []
    if late_ship_rate is not None and platform_late is not None and float(late_ship_rate) > float(platform_late):
        chips.append("Bàn giao trễ cao hơn sàn")
    if avg_review is not None and platform_review is not None and float(avg_review) < float(platform_review):
        chips.append("Điểm review thấp hơn sàn")
    return chips


def percentile_above(values, value) -> float | None:
    """Share of values strictly below this one. None when the set is empty."""
    if value is None or values is None:
        return None
    clean = [float(item) for item in values if item is not None]
    if not clean:
        return None
    below = sum(1 for item in clean if item < float(value))
    return below / len(clean)
