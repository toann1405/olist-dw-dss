"""KPI overview. Cards use the same numerator and denominator as the SQL files."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db, queries
from lib.glossary import explain
from lib.insights import build_insight_kpi
from lib.ui import (
    LATE,
    NAVY,
    apply_theme,
    filters,
    fmt_brl,
    fmt_int,
    fmt_pct,
    highlight_colors,
    insight_box,
    kpi_card,
    next_step,
    page_header,
    signed_pct,
    signed_points,
)
from src.dss.params import MIN_ORDERS


def _num(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        return None
    return float(value)


def _ratio(numerator, denominator):
    top = _num(numerator)
    bottom = _num(denominator)
    if top is None or bottom is None or bottom == 0:
        return None
    return top / bottom


def _row(frame: pd.DataFrame) -> pd.Series:
    return frame.iloc[0]


def _pack(monthly: pd.Series, orders: pd.Series) -> dict:
    gmv = _num(monthly["gmv"])
    valid_orders = _num(orders["valid_orders"])
    return {
        "gmv": gmv,
        "valid_orders": valid_orders,
        "aov": _ratio(orders["gmv_from_items"], orders["valid_orders"]),
        "late_rate": _ratio(monthly["late_ship_count"], monthly["late_ship_eligible"]),
        "late_n": _num(monthly["late_ship_eligible"]),
        "review_rate": _ratio(monthly["negative_review_count"], monthly["negative_review_eligible"]),
        "review_n": _num(monthly["negative_review_eligible"]),
        "cancel_rate": _ratio(orders["cancel_orders"], orders["placed_orders"]),
        "cancel_n": _num(orders["placed_orders"]),
    }


def _pack_category(row: pd.Series, review: dict) -> dict:
    return {
        "gmv": _num(row["gmv"]),
        "valid_orders": _num(row["valid_orders"]),
        "aov": _ratio(row["gmv"], row["valid_orders"]),
        "late_rate": _ratio(row["late_ship_count"], row["late_ship_eligible"]),
        "late_n": _num(row["late_ship_eligible"]),
        "review_rate": review["review_rate"],
        "review_n": review["review_n"],
        "cancel_rate": _ratio(row["cancel_orders"], row["placed_orders"]),
        "cancel_n": _num(row["placed_orders"]),
    }


def _load_base(year, region, state) -> dict:
    monthly = _row(db.query(*queries.kpi_seller_month(year, region, state)))
    orders = _row(db.query(*queries.kpi_orders(year, region, state)))
    return _pack(monthly, orders)


def _combo(frame: pd.DataFrame) -> None:
    data = frame.copy()
    data["gmv"] = pd.to_numeric(data["gmv"], errors="coerce")
    data["late_ship_count"] = pd.to_numeric(data["late_ship_count"], errors="coerce")
    data["late_ship_eligible"] = pd.to_numeric(data["late_ship_eligible"], errors="coerce")
    data["late_rate"] = data["late_ship_count"] / data["late_ship_eligible"].where(data["late_ship_eligible"] > 0)
    fig = go.Figure()
    fig.add_bar(
        x=data["year_month"],
        y=data["gmv"],
        name="GMV",
        marker_color=NAVY,
        customdata=list(zip(data["late_ship_eligible"].fillna(0), data["gmv"].map(fmt_brl))),
        hovertemplate="Tháng %{x}<br>GMV %{customdata[1]}<br>n bàn giao %{customdata[0]:,.0f}<extra></extra>",
    )
    fig.add_scatter(
        x=data["year_month"],
        y=data["late_rate"],
        name="Bàn giao trễ",
        mode="lines+markers",
        marker_color=LATE,
        line=dict(color=LATE, width=2),
        yaxis="y2",
        customdata=data["late_ship_eligible"].fillna(0),
        hovertemplate="Tháng %{x}<br>Bàn giao trễ %{y:.1%}<br>n %{customdata:,.0f}<extra></extra>",
    )
    fig.update_layout(
        yaxis=dict(title="GMV", tickprefix="R$ ", tickformat=",.0f"),
        yaxis2=dict(title="Bàn giao trễ", overlaying="y", side="right", tickformat=".0%", showgrid=False, range=[0, 0.25]),
        hovermode="x unified",
        barmode="overlay",
    )
    apply_theme(fig, height=420)
    st.plotly_chart(fig, width="stretch")


def _category_bars(frame: pd.DataFrame) -> None:
    data = frame.copy()
    data["gmv"] = pd.to_numeric(data["gmv"], errors="coerce")
    data["n_items"] = pd.to_numeric(data["n_items"], errors="coerce")
    data = data.sort_values("gmv", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=data["gmv"],
            y=data["category_group"],
            orientation="h",
            marker_color=highlight_colors(data["gmv"].tolist(), NAVY),
            customdata=list(zip(data["n_items"], data["gmv"].map(fmt_brl))),
            hovertemplate="%{y}<br>%{customdata[1]}<br>n item %{customdata[0]:,.0f}<extra></extra>",
        )
    )
    apply_theme(fig, height=max(280, 36 * len(data) + 40))
    fig.update_layout(margin=dict(l=150, r=16, t=24, b=16))
    fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f")
    st.plotly_chart(fig, width="stretch")


def _region_bars(frame: pd.DataFrame) -> None:
    data = frame.copy()
    data["late_ship_count"] = pd.to_numeric(data["late_ship_count"], errors="coerce")
    data["late_ship_eligible"] = pd.to_numeric(data["late_ship_eligible"], errors="coerce")
    data["late_rate"] = data["late_ship_count"] / data["late_ship_eligible"].where(data["late_ship_eligible"] > 0)
    data = data.dropna(subset=["late_rate"]).sort_values("late_rate")
    fig = go.Figure(
        go.Bar(
            x=data["late_rate"],
            y=data["region_name"],
            orientation="h",
            marker_color=highlight_colors(data["late_rate"].tolist(), LATE),
            customdata=data["late_ship_eligible"],
            hovertemplate="%{y}<br>%{x:.1%}<br>n %{customdata:,.0f}<extra></extra>",
        )
    )
    apply_theme(fig, height=max(240, 42 * len(data) + 40))
    fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")


def _risk_table() -> None:
    frame = db.query(*queries.risk_scores(5))
    if frame.empty:
        st.info("Chưa có seller với ít nhất 5 đơn hợp lệ trong tháng chấm. Chạy job DSS trên workspace trước.")
        return
    show = frame.head(10).copy()
    show["p_bad"] = pd.to_numeric(show["p_bad"], errors="coerce")
    show["Đơn"] = show["n_orders_valid"].map(fmt_int)
    show["GMV"] = show["gmv"].map(fmt_brl)
    show["Bàn giao trễ"] = show["late_ship_rate"].map(fmt_pct)
    st.dataframe(
        show[["seller_id", "p_bad", "Đơn", "GMV", "Bàn giao trễ", "as_of_month"]],
        column_config={
            "seller_id": "Seller",
            "p_bad": st.column_config.ProgressColumn("Điểm rủi ro", min_value=0, max_value=1, format="percent"),
            "as_of_month": "Tháng chấm",
        },
        width="stretch",
        hide_index=True,
    )


def render(settings=None) -> None:
    del settings
    page_header(
        "Sức khỏe marketplace đang thế nào?",
        "Sáu chỉ số giữ nguyên công thức. Câu phía trên theo bộ lọc đang chọn.",
        "Tổng quan KPI",
    )
    year, region, state, category = filters()
    try:
        with st.spinner("Đang hỏi SQL Warehouse..."):
            current = _load_base(year, region, state)
            previous = None
            if year is not None:
                previous = _load_base(year - 1, region, state)
            if category is not None:
                scoped = _row(db.query(*queries.kpi_for_category(year, region, state, category)))
                prior_review = current
                current = _pack_category(scoped, current)
                if year is not None:
                    prior_scoped = _row(db.query(*queries.kpi_for_category(year - 1, region, state, category)))
                    previous = _pack_category(prior_scoped, previous or prior_review)
            months = db.query(*queries.kpi_by_month(year, region, state))
            categories = db.query(*queries.kpi_top_categories(year, region, state))
            regions = db.query(*queries.kpi_late_by_region(year, state))
    except Exception as exc:
        db.show_warehouse_error(exc)
        next_step("kpi")
        return
    try:
        story = db.query(*queries.story_by_region(year, region, state, category))
        insight_box(build_insight_kpi(story, MIN_ORDERS))
    except Exception as exc:
        st.error(db.redact(exc))

    def _growth(now, before):
        if now is None or before in (None, 0):
            return None
        return (now - before) / abs(before)

    money_delta = points_late = points_review = points_cancel = orders_delta = aov_delta = None
    if previous is not None:
        money_delta = signed_pct(_growth(current["gmv"], previous["gmv"]))
        orders_delta = signed_pct(_growth(current["valid_orders"], previous["valid_orders"]))
        aov_delta = signed_pct(_growth(current["aov"], previous["aov"]))
        points_late = signed_points(current["late_rate"], previous["late_rate"])
        points_review = signed_points(current["review_rate"], previous["review_rate"])
        points_cancel = signed_points(current["cancel_rate"], previous["cancel_rate"])

    specs = [
        ("GMV", fmt_brl(current["gmv"]), money_delta, explain("gmv"), "normal"),
        ("Số đơn", fmt_int(current["valid_orders"]), orders_delta, explain("valid_orders"), "normal"),
        ("AOV", fmt_brl(current["aov"]), aov_delta, explain("aov"), "normal"),
        ("Bàn giao trễ", fmt_pct(current["late_rate"]), points_late, explain("late_ship"), "inverse"),
        ("Review xấu", fmt_pct(current["review_rate"]), points_review, explain("negative_review"), "inverse"),
        ("Cancel rate", fmt_pct(current["cancel_rate"]), points_cancel, explain("cancel_rate"), "inverse"),
    ]
    for start in (0, 3):
        for column, (label, value, delta, help_text, color) in zip(st.columns(3), specs[start : start + 3]):
            with column:
                kpi_card(label, value, delta=delta, help_text=help_text, delta_color=color)

    st.subheader("GMV và bàn giao trễ theo tháng mua")
    _combo(months)
    one, two, three = st.columns(3)
    with one:
        st.markdown("**Top 10 nhóm danh mục theo GMV**")
        _category_bars(categories)
    with two:
        st.markdown("**Bàn giao trễ theo vùng seller**")
        _region_bars(regions)
    with three:
        st.markdown("**Top 10 seller rủi ro**")
        st.caption("Tháng chấm mới nhất, chỉ seller có ít nhất 5 đơn hợp lệ.")
        try:
            _risk_table()
        except Exception as exc:
            st.error(db.redact(exc))
    next_step("kpi")
