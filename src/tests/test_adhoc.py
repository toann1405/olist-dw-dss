"""Ad hoc SQL is assembled from fixed fragments. Filter text stays in the parameter tuple."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

FRONT = Path(__file__).resolve().parents[1] / "frontend"
sys.path.insert(0, str(FRONT))

from lib import adhoc, db  # noqa: E402

_TOKEN = "user'); DROP TABLE gold.fact_order; --"


def test_user_text_stays_out_of_the_sql():
    sql, params = adhoc.build_query(
        "GMV",
        ["Vùng"],
        {"region": _TOKEN, "month_from": _TOKEN, "month_to": _TOKEN, "category": None},
    )
    assert _TOKEN not in sql
    assert _TOKEN in params
    assert "GROUP BY" in sql and "ORDER BY" in sql and "LIMIT 500" in sql
    assert sql.count("?") == len(params)


def test_invalid_pair_is_rejected():
    with pytest.raises(ValueError):
        adhoc.build_query("GMV", ["Nhóm danh mục"], {})
    with pytest.raises(ValueError):
        adhoc.build_query("GMV", ["Vùng", "Vùng"], {})
    with pytest.raises(ValueError):
        adhoc.build_query("không có chỉ số này", ["Vùng"], {})
    with pytest.raises(ValueError):
        adhoc.build_query("GMV", ["Vùng"], {"category": "electronics_it_telephony"})


def test_gmv_by_region_sums_to_the_full_marketplace():
    sql, params = adhoc.build_query("GMV", ["Vùng"], {})
    frame = db.query_uncached(sql, params)
    total = float(frame["value"].sum())
    assert abs(total - 13494400.74) < 0.05


def test_late_ship_by_region_matches_the_rollup_tab():
    sql, params = adhoc.build_query("Tỷ lệ bàn giao trễ", ["Vùng"], {})
    frame = db.query_uncached(sql, params)
    norte = frame[frame["dim_1"].astype(str) == "Norte"].iloc[0]
    assert round(float(norte["value"]) * 100, 1) == 19.2
