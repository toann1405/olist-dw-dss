"""Action labels and percentile rank. No warehouse."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.dss.recommend import TIER_NAME, action_for_tier, percentile_above, reason_chips  # noqa: E402


def test_action_for_tier():
    assert TIER_NAME[0] == "Bình thường"
    assert TIER_NAME[1] == "Theo dõi"
    assert TIER_NAME[2] == "Cảnh báo"
    assert TIER_NAME[3] == "Tạm ngưng"
    assert action_for_tier(0) == "Bình thường"
    assert action_for_tier(2) == "Cảnh báo + hỗ trợ"
    assert action_for_tier(3) == "Tạm ngưng hiển thị"
    assert action_for_tier(9) == "Bình thường"


def test_reason_chips_only_when_worse_than_platform():
    assert reason_chips(0.2, 3.0, 0.1, 4.0) == [
        "Bàn giao trễ cao hơn sàn",
        "Điểm review thấp hơn sàn",
    ]
    assert reason_chips(0.05, 4.5, 0.1, 4.0) == []
    assert reason_chips(None, None, 0.1, 4.0) == []


def test_percentile_above():
    assert percentile_above([0.1, 0.2, 0.4], 0.4) == 2 / 3
    assert percentile_above([], 0.2) is None
