"""Five OLAP operators. Each operator keeps the SQL file that defines it."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, queries


def _review_by_level(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    work = frame.copy()
    work["negative_orders"] = pd.to_numeric(work["negative_orders"], errors="coerce").fillna(0)
    work["reviewed_orders"] = pd.to_numeric(work["reviewed_orders"], errors="coerce").fillna(0)
    grouped = work.groupby(columns, as_index=False, dropna=False)[
        ["negative_orders", "reviewed_orders"]
    ].sum()
    denominator = grouped["reviewed_orders"]
    grouped["negative_review_rate"] = grouped["negative_orders"] / denominator.where(denominator > 0)
    return grouped


def _axis(frame: pd.DataFrame, level: str) -> pd.DataFrame:
    out = frame.copy()
    if level == "region":
        out["axis"] = out["region_name"].fillna("(không map được vùng)")
    elif level == "state":
        region = out["region_name"].fillna("(không map được vùng)")
        state = out["state_code"].fillna("(trống)")
        out["axis"] = region + " / " + state
    else:
        city = out["city_name"].fillna("(trống)")
        state = out["state_code"].fillna("(trống)")
        out["axis"] = state + " / " + city
    return out


def _show_rollup(frame: pd.DataFrame) -> None:
    level = st.selectbox("Mức roll-up", ("region", "state", "city"))
    part = frame[frame["rollup_level"] == level].copy()
    labeled = _axis(part, level)
    chart = labeled
    if level == "city":
        chart = labeled.sort_values("eligible_items", ascending=False).head(20)
    st.bar_chart(chart.set_index("axis")[["late_ship_rate"]])
    if level == "city":
        st.caption("Chart lấy 20 thành phố có nhiều item đủ mẫu nhất. Bảng bên dưới là đủ mức thành phố.")
    st.dataframe(part, width="stretch")


def _show_drill(frame: pd.DataFrame) -> None:
    level = st.selectbox("Mức drill-down", ("Năm", "Quý", "Tháng", "Ngày"))
    columns = {
        "Năm": ["year"],
        "Quý": ["year", "quarter"],
        "Tháng": ["year", "quarter", "month"],
        "Ngày": ["year", "quarter", "month", "day_of_month", "full_date"],
    }[level]
    grouped = _review_by_level(frame, columns)
    if level == "Năm":
        grouped["axis"] = grouped["year"].astype(str)
    elif level == "Quý":
        grouped["axis"] = grouped["year"].astype(str) + " Q" + grouped["quarter"].astype(str)
    elif level == "Tháng":
        grouped["axis"] = (
            grouped["year"].astype(str)
            + "-"
            + grouped["month"].astype(int).astype(str).str.zfill(2)
        )
    else:
        grouped["axis"] = grouped["full_date"].astype(str)
    st.line_chart(grouped.set_index("axis")[["negative_review_rate"]])
    st.caption("KPI sàn: giữ cross_seller. Tỷ lệ = tổng đơn review xấu / tổng đơn có điểm, không lấy trung bình các tỷ lệ con.")
    st.dataframe(grouped, width="stretch")


def _show_slice() -> None:
    groups = queries.category_groups()
    names = groups["category_group"].dropna().astype(str).tolist()
    if not names:
        st.info("Không có category_group với product_key khác -1.")
        return
    chosen = st.selectbox("category_group", names)
    frame = db.query(*queries.slice_category(chosen))
    ranked = frame.sort_values(
        by=["late_delivery_rate", "eligible_orders"],
        ascending=[False, False],
        na_position="last",
    )
    st.bar_chart(ranked.head(20).set_index("seller_id")[["late_delivery_rate"]])
    st.caption("Top 20 seller theo late_delivery_rate. Cờ giao trễ đếm DISTINCT order_id, không SUM trên item.")
    st.dataframe(ranked, width="stretch")


def _show_dice() -> None:
    frame = db.query(*queries.dice())
    st.caption("Khách Norte và Nordeste, Q1–Q2/2018, size_band = bulky, theo bang seller.")
    st.dataframe(frame, width="stretch")


def _show_pivot() -> None:
    frame = db.query(*queries.pivot())
    st.caption("category_group × quý. Mọi năm gộp vào cùng một quý, đúng file 05.")
    st.dataframe(frame, width="stretch")


def render(settings=None) -> None:
    del settings
    st.header("OLAP Explorer")
    st.caption("Warehouse Free Edition có thể mất vài phút cho câu đầu.")
    db.refresh_button("olap")
    operator = st.selectbox(
        "Phép",
        ("Roll-up", "Drill-down", "Slice", "Dice", "Pivot"),
    )
    try:
        with st.spinner("Đang hỏi SQL Warehouse..."):
            if operator == "Roll-up":
                _show_rollup(db.query(*queries.rollup()))
            elif operator == "Drill-down":
                _show_drill(db.query(*queries.drilldown()))
            elif operator == "Slice":
                _show_slice()
            elif operator == "Dice":
                _show_dice()
            else:
                _show_pivot()
    except Exception as exc:
        db.show_warehouse_error(exc)
