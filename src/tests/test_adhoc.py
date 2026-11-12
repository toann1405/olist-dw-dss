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


def test_same_params_hit_the_warehouse_once(monkeypatch):
    calls = {"n": 0}

    def fake(sql, params=()):
        calls["n"] += 1
        return __import__("pandas").DataFrame({"dim_1": ["Sudeste"], "value": [1.0], "n": [10]})

    adhoc.run_query.clear()
    monkeypatch.setattr(adhoc.db, "query", fake)
    key = adhoc.params_key({"measure": "GMV", "dims": ["Vùng"], "filters": {}})
    adhoc.run_query(key)
    adhoc.run_query(key)
    assert calls["n"] == 1


def test_late_ship_by_region_matches_the_rollup_tab():
    sql, params = adhoc.build_query("Tỷ lệ bàn giao trễ", ["Vùng"], {})
    frame = db.query_uncached(sql, params)
    norte = frame[frame["dim_1"].astype(str) == "Norte"].iloc[0]
    assert round(float(norte["value"]) * 100, 1) == 19.2


def test_all_filters_omit_optional_predicates():
    filters = {"month_from": None, "month_to": None, "region": None, "category": None}
    sql, params = adhoc.build_query("GMV", ["Vùng"], filters)
    assert "IS NULL OR" not in sql
    assert params == ()
    assert "WHERE" in sql
    assert "seller_key <> -1" in sql
    item_sql, item_params = adhoc.build_query("Tỷ lệ bàn giao trễ", ["Vùng"], filters)
    assert "IS NULL OR" not in item_sql
    assert item_params == ()


def test_region_sul_is_bound_and_readable():
    sql, params = adhoc.build_query(
        "GMV",
        ["Vùng"],
        {"region": "Sul", "month_from": None, "month_to": None, "category": None},
    )
    assert "Sul" not in sql
    assert "IS NULL OR" not in sql
    assert params == ("Sul",)
    assert "s.region_name = ?" in sql
    shown = " ".join(adhoc.readable_sql(sql, params).split())
    assert "s.region_name = 'Sul'" in shown
    assert shown.startswith("SELECT")
    assert " WHERE " in shown


def test_typed_filter_stays_out_of_executed_sql_when_shown():
    sql, params = adhoc.build_query("GMV", ["Vùng"], {"region": _TOKEN})
    assert _TOKEN not in sql
    assert _TOKEN in params
    shown = adhoc.readable_sql(sql, params)
    assert _TOKEN not in sql
    assert "''" in shown


def test_sul_gmv_matches_the_unfiltered_slice():
    all_sql, all_params = adhoc.build_query("GMV", ["Vùng"], {})
    all_frame = db.query_uncached(all_sql, all_params)
    sul_sql, sul_params = adhoc.build_query("GMV", ["Vùng"], {"region": "Sul"})
    sul_frame = db.query_uncached(sul_sql, sul_params)
    expected = float(all_frame.loc[all_frame["dim_1"].astype(str) == "Sul", "value"].iloc[0])
    assert len(sul_frame) == 1
    assert abs(float(sul_frame["value"].iloc[0]) - expected) < 0.05
