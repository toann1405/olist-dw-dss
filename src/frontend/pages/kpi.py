"""KPI overview. Rates are recomputed from counts, not from rate columns."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, queries


def _float(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        return None
    return float(value)


def _metric(label: str, value, caption: str) -> None:
    number = _float(value)
    shown = "null" if number is None else f"{number:,.4f}"
    st.metric(label, shown)
    st.caption(caption)


def render(settings=None) -> None:
    del settings
    st.header("Tổng quan KPI")
    st.caption("Warehouse Free Edition có thể mất vài phút cho câu đầu.")
    db.refresh_button("kpi")
    try:
        year_frame = db.query(*queries.years())
        region_frame = db.query(*queries.regions())
        years = ["Tất cả"] + [int(value) for value in year_frame["year"].dropna().tolist()]
        regions = ["Tất cả"] + region_frame["region_name"].dropna().astype(str).tolist()
        year_choice = st.selectbox("Năm mua", years)
        region_choice = st.selectbox("Vùng seller", regions)
        year = None if year_choice == "Tất cả" else int(year_choice)
        region = None if region_choice == "Tất cả" else str(region_choice)
        with st.spinner("Đang hỏi SQL Warehouse..."):
            monthly = db.query(*queries.kpi_seller_month(year, region)).iloc[0]
            orders = db.query(*queries.kpi_orders(year, region)).iloc[0]
    except Exception as exc:
        db.show_warehouse_error(exc)
        return

    left, right = st.columns(2)
    with left:
        _metric(
            "GMV",
            monthly["gmv"],
            "SUM(price), không gồm freight, loại canceled và unavailable.",
        )
        _metric(
            "Tỷ lệ bàn giao trễ",
            monthly["late_ship_rate"],
            f"Item trễ / item có cờ khác null: {monthly['late_ship_count']} / {monthly['late_ship_eligible']}",
        )
        _metric(
            "Tỷ lệ review xấu",
            monthly["negative_review_rate"],
            "Measure seller, loại đơn nhiều seller và cross_seller. "
            f"{monthly['negative_review_count']} / {monthly['negative_review_eligible']}",
        )
    with right:
        _metric(
            "AOV",
            orders["aov"],
            "GMV trong bộ lọc / số đơn phân biệt. "
            f"{orders['gmv_from_items']} / {orders['valid_orders']}",
        )
        _metric(
            "Cancel rate",
            orders["cancel_rate"],
            "Đơn canceled hoặc unavailable / mọi đơn phân biệt. "
            f"{orders['cancel_orders']} / {orders['placed_orders']}",
        )
