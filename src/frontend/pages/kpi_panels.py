"""Analytic panels for the KPI page. Rates are recomputed from counts."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.glossary import explain
from lib.insights import recommend_policy
from lib.labels import fmt_count, fmt_limit, fmt_number, fmt_percent_points, policy_name
from lib.stats import SPARSE_MONTHS, pareto, wilson_ci
from lib.ui import (
    LATE,
    MIN_N_DISPLAY,
    NAVY,
    add_platform_reference,
    apply_theme,
    fmt_brl,
    fmt_int,
    fmt_pct,
    kpi_card,
    point_opacity,
)
from src.dss.params import MIN_ORDERS, N, X


def _num(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        return None
    return float(value)


def _rate(top, bottom):
    numerator, denominator = _num(top), _num(bottom)
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _spark(frame: pd.DataFrame, value_column: str) -> None:
    if frame is None or frame.empty or value_column not in frame.columns:
        return
    figure = go.Figure(go.Scatter(x=frame["year_month"], y=frame[value_column], mode="lines", line=dict(color=NAVY, width=2)))
    apply_theme(figure, height=90)
    figure.update_layout(margin=dict(l=0, r=0, t=4, b=0), showlegend=False)
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    st.plotly_chart(figure, width="stretch")


def _with_rates(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    pairs = {
        "late_ship_rate": ("late_ship_count", "late_ship_eligible"),
        "late_delivery_rate": ("late_delivery_count", "late_delivery_eligible"),
        "review_rate": ("negative_review_count", "negative_review_eligible"),
        "bad_rate": ("bad_experience_count", "bad_experience_eligible"),
        "cancel_rate": ("cancel_count", "n_orders_placed"),
        "avg_review": ("review_score_sum", "review_count"),
        "avg_handling_days": ("handling_days_sum", "handling_days_count"),
    }
    for name, (top, bottom) in pairs.items():
        if top in data.columns and bottom in data.columns:
            data[name] = [
                _rate(row[top], row[bottom]) for row in data.to_dict("records")
            ]
    return data


def constraint_strip(snapshot: pd.DataFrame) -> None:
    st.markdown("**Trạng thái so với ràng buộc**")
    if snapshot is None or snapshot.empty:
        st.info("Chưa có kết quả chính sách cho kỳ này.")
        return
    advice = recommend_policy(snapshot, X, N)
    chosen = advice["code"]
    row = None
    if chosen is not None and "policy_code" in snapshot.columns:
        match = snapshot[snapshot["policy_code"].astype(str) == chosen]
        if not match.empty:
            row = match.iloc[0]
    if row is None:
        st.info(advice["sentence"])
    else:
        st.write(
            f"{policy_name(chosen)}: GMV bị gắn cờ {fmt_percent_points(row['gmv_affected_pct'])} "
            f"/ trần {fmt_limit(X)}%, {fmt_count(row['n_sellers_flagged'])} seller / trần {fmt_limit(N)}."
        )
    pages = st.session_state.get("nav_pages", {})
    if pages.get("policy") is not None:
        st.page_link(pages["policy"], label="Mở trang chính sách")


def hero(story: pd.DataFrame, previous_rate) -> None:
    total = story[pd.to_numeric(story["is_total"], errors="coerce").fillna(0).astype(int) == 1]
    if total.empty:
        st.info("Chưa đủ dữ liệu để kết luận.")
        return
    row = total.iloc[0]
    rate = _rate(row["bad_orders"], row["eligible_orders"])
    delta = None
    if previous_rate is not None and rate is not None:
        delta = fmt_pct(rate - previous_rate).replace("%", " điểm")
    low, high = wilson_ci(row["bad_orders"], row["eligible_orders"])
    band = ""
    if low is not None:
        band = f"Khoảng Wilson {fmt_pct(low)}–{fmt_pct(high)}. "
    st.markdown("**Tỷ lệ đơn trải nghiệm xấu**")
    kpi_card(
        "Đơn trải nghiệm xấu",
        fmt_pct(rate),
        delta=delta,
        help_text=explain("bad_experience") + " " + band + f"n = {fmt_int(row['eligible_orders'])}.",
        delta_color="inverse",
    )


def grouped_cards(current: dict, series: pd.DataFrame) -> None:
    data = _with_rates(series) if series is not None else pd.DataFrame()
    latest = None
    if not data.empty:
        kept = data[~data["year_month"].isin(SPARSE_MONTHS)]
        latest = (kept if not kept.empty else data).iloc[-1]

    def tail(column):
        if data.empty or column not in data.columns:
            return data
        return data[["year_month", column]].dropna()

    st.markdown("**Quy mô**")
    columns = st.columns(4)
    blocks = [
        ("GMV", fmt_brl(current["gmv"]), explain("gmv"), "gmv"),
        ("Số đơn", fmt_int(current["valid_orders"]), explain("valid_orders"), "n_orders_valid"),
        ("AOV", fmt_brl(current["aov"]), explain("aov"), None),
        ("Seller hoạt động tháng cuối đủ dữ liệu", fmt_int(None if latest is None else latest.get("active_sellers")), explain("active_sellers"), "active_sellers"),
    ]
    for column, (label, value, help_text, spark) in zip(columns, blocks):
        with column:
            kpi_card(label, value, help_text=help_text)
            if spark:
                _spark(tail(spark), spark)
    handling = None if latest is None else latest.get("avg_handling_days")
    review = None if latest is None else latest.get("avg_review")
    delivery = None if latest is None else latest.get("late_delivery_rate")
    st.markdown("**Chất lượng**")
    columns = st.columns(4)
    quality = [
        ("Giao trễ tới khách", fmt_pct(delivery), explain("late_delivery"), "late_delivery_rate"),
        ("Bàn giao trễ", fmt_pct(current["late_rate"]), explain("late_ship"), "late_ship_rate"),
        ("Review xấu (theo seller)", fmt_pct(current["review_rate"]), explain("negative_review"), "review_rate"),
        ("Cancel rate", fmt_pct(current["cancel_rate"]), explain("cancel_rate"), "cancel_rate"),
    ]
    for column, (label, value, help_text, spark) in zip(columns, quality):
        with column:
            kpi_card(label, value, help_text=help_text)
            _spark(tail(spark), spark)
    st.markdown("**Vận hành**")
    columns = st.columns(2)
    with columns[0]:
        kpi_card("Điểm review trung bình", fmt_number(review), help_text=explain("negative_review"))
        _spark(tail("avg_review"), "avg_review")
    with columns[1]:
        kpi_card("Số ngày xử lý trung bình", fmt_number(handling), help_text="handling_days_sum / handling_days_count.")
        _spark(tail("avg_handling_days"), "avg_handling_days")


def trend_tab(series: pd.DataFrame, platform_bad) -> None:
    data = _with_rates(series)
    if data.empty:
        st.info("Chưa đủ dữ liệu để kết luận.")
        return
    choice = st.selectbox(
        "Đường tỷ lệ",
        ("bad_rate", "late_delivery_rate", "late_ship_rate", "review_rate", "cancel_rate"),
        format_func=lambda name: {
            "bad_rate": "Đơn trải nghiệm xấu",
            "late_delivery_rate": "Giao trễ tới khách",
            "late_ship_rate": "Bàn giao trễ",
            "review_rate": "Review xấu (theo seller)",
            "cancel_rate": "Cancel rate",
        }[name],
    )
    count_column = {
        "bad_rate": "bad_experience_eligible",
        "late_delivery_rate": "late_delivery_eligible",
        "late_ship_rate": "late_ship_eligible",
        "review_rate": "negative_review_eligible",
        "cancel_rate": "n_orders_placed",
    }[choice]
    success_column = {
        "bad_rate": "bad_experience_count",
        "late_delivery_rate": "late_delivery_count",
        "late_ship_rate": "late_ship_count",
        "review_rate": "negative_review_count",
        "cancel_rate": "cancel_count",
    }[choice]
    data["sparse"] = data["year_month"].isin(SPARSE_MONTHS)
    figure = go.Figure()
    figure.add_bar(
        x=data["year_month"],
        y=data["gmv"],
        name="GMV",
        marker_color=["#c5cdd6" if flag else NAVY for flag in data["sparse"]],
        opacity=0.85,
    )
    errors_plus = []
    errors_minus = []
    for row in data.itertuples(index=False):
        rate = getattr(row, choice)
        low, high = wilson_ci(getattr(row, success_column), getattr(row, count_column))
        if rate is None or low is None or pd.isna(rate):
            errors_plus.append(0)
            errors_minus.append(0)
        else:
            errors_plus.append(max(0.0, high - rate))
            errors_minus.append(max(0.0, rate - low))
    figure.add_scatter(
        x=data["year_month"],
        y=data[choice],
        name="Tỷ lệ",
        mode="lines+markers",
        marker=dict(color=LATE, opacity=point_opacity(data[count_column])),
        yaxis="y2",
        error_y=dict(type="data", array=errors_plus, arrayminus=errors_minus, thickness=1),
        customdata=data[count_column],
        hovertemplate="%{x}<br>%{y:.1%}<br>n %{customdata:,.0f}<extra></extra>",
    )
    figure.update_layout(
        yaxis=dict(title="GMV"),
        yaxis2=dict(title="Tỷ lệ", overlaying="y", side="right", tickformat=".0%"),
        hovermode="x unified",
    )
    add_platform_reference(figure, platform_bad if choice == "bad_rate" else None)
    apply_theme(figure, height=420)
    st.plotly_chart(figure, width="stretch")
    st.caption(f"Tháng tô nhạt là tháng dữ liệu thưa. Điểm mờ có n < {MIN_N_DISPLAY}.")
    peak = data[data[count_column] >= MIN_N_DISPLAY].dropna(subset=[choice]).sort_values(choice, ascending=False).head(1)
    if not peak.empty:
        row = peak.iloc[0]
        st.info(
            f"Tỷ lệ cao nhất trong bộ lọc là {row['year_month']}: {fmt_pct(row[choice])} "
            f"(n={fmt_int(row[count_column])})."
        )


def where_tab(regions: pd.DataFrame, categories: pd.DataFrame, platform_late) -> None:
    level = st.selectbox("Mức địa lý", ("Vùng", "Bang"))
    if level == "Vùng" and regions is not None and not regions.empty:
        data = regions.copy()
        data["rate"] = [
            _rate(row.late_ship_count, row.late_ship_eligible) for row in data.itertuples(index=False)
        ]
        figure = go.Figure(go.Bar(
            x=data["rate"],
            y=data["region_name"],
            orientation="h",
            marker=dict(color=LATE, opacity=point_opacity(data["late_ship_eligible"])),
            error_x=dict(type="data", array=[
                0 if wilson_ci(k, n)[1] is None or rate is None else max(0, wilson_ci(k, n)[1] - rate)
                for k, n, rate in zip(data["late_ship_count"], data["late_ship_eligible"], data["rate"])
            ]),
        ))
        add_platform_reference(figure, platform_late)
        apply_theme(figure, height=320)
        st.plotly_chart(figure, width="stretch")
    if categories is not None and not categories.empty and "bad_orders" in categories.columns:
        data = categories.copy()
        data["rate"] = [_rate(a, b) for a, b in zip(data["bad_orders"], data["eligible_orders"])]
        figure = go.Figure(go.Scatter(
            x=data["gmv"],
            y=data["rate"],
            mode="markers",
            text=data["category_group"],
            marker=dict(size=(data["orders"].fillna(0) / data["orders"].max() * 40).clip(lower=8), color=NAVY, opacity=point_opacity(data["eligible_orders"])),
        ))
        add_platform_reference(figure, _rate(data["bad_orders"].sum(), data["eligible_orders"].sum()))
        apply_theme(figure, height=420)
        figure.update_yaxes(tickformat=".0%")
        st.plotly_chart(figure, width="stretch")
        st.caption("Trục ngang là GMV, trục dọc là tỷ lệ đơn trải nghiệm xấu, kích thước là số đơn.")


def seller_tab(sellers: pd.DataFrame, funnel: pd.DataFrame, risk) -> None:
    if sellers is not None and not sellers.empty:
        ranked = pareto(sellers)
        mark = ranked[ranked["sellers"] <= 40].tail(1)
        figure = go.Figure(go.Scatter(x=ranked["seller_share"], y=ranked["bad_share"], mode="lines", line=dict(color=NAVY)))
        if not mark.empty:
            figure.add_scatter(
                x=mark["seller_share"],
                y=mark["bad_share"],
                mode="markers",
                name="40 seller",
                marker=dict(color=LATE, size=12),
            )
        apply_theme(figure, height=320)
        figure.update_xaxes(tickformat=".0%", title="Seller, tệ nhất trước")
        figure.update_yaxes(tickformat=".0%", title="Đơn xấu cộng dồn")
        st.plotly_chart(figure, width="stretch")
        if not mark.empty:
            st.info(
                f"{fmt_count(mark.iloc[0]['sellers'])} seller tệ nhất chiếm {fmt_pct(mark.iloc[0]['bad_share'])} "
                "đơn trải nghiệm xấu theo measure seller."
            )
        kept = sellers[pd.to_numeric(sellers["n_orders_valid"], errors="coerce") >= MIN_ORDERS].copy()
        kept["rate"] = [_rate(a, b) for a, b in zip(kept["bad_orders"], kept["eligible_orders"])]
        figure = go.Figure(go.Scatter(
            x=kept["n_orders_valid"],
            y=kept["rate"],
            mode="markers",
            marker=dict(size=8, color=NAVY, opacity=point_opacity(kept["eligible_orders"])),
        ))
        apply_theme(figure, height=320)
        figure.update_yaxes(tickformat=".0%")
        st.plotly_chart(figure, width="stretch")
    if funnel is not None and not funnel.empty:
        for row in funnel.itertuples(index=False):
            label = "Có closed deal" if int(row.has_closed_deal) == 1 else "Không có closed deal"
            st.write(
                f"{label}: {fmt_pct(_rate(row.bad_orders, row.eligible_orders))} "
                f"(n={fmt_int(row.eligible_orders)}, {fmt_int(row.sellers)} seller)."
            )
    risk()
    pages = st.session_state.get("nav_pages", {})
    if pages.get("risk") is not None:
        st.page_link(pages["risk"], label="Mở trang Seller risk")


def trust_tab(series: pd.DataFrame, quality: pd.DataFrame) -> None:
    if series is not None and not series.empty:
        data = series.copy()
        data["sparse"] = data["year_month"].isin(SPARSE_MONTHS)
        figure = go.Figure(go.Bar(
            x=data["year_month"],
            y=data["n_orders_valid"],
            marker_color=["#c5cdd6" if flag else NAVY for flag in data["sparse"]],
        ))
        apply_theme(figure, height=280)
        st.plotly_chart(figure, width="stretch")
        sparse = data.loc[data["sparse"], "year_month"].astype(str).tolist()
        st.write("Tháng thưa trong bộ lọc: " + (", ".join(sparse) if sparse else "không có."))
    if quality is not None and not quality.empty:
        row = quality.iloc[0]
        orders = _num(row["orders"])
        multi = _num(row["multi_seller_orders"])
        share = _rate(multi, orders)
        st.write(
            f"Đơn nhiều seller: {fmt_pct(share)} (n={fmt_int(multi)} / {fmt_int(orders)}). "
            f"Đơn có review nhưng bị loại khỏi measure seller: {fmt_int(row['review_excluded_orders'])}."
        )


def render_tabs(series, regions, categories, sellers, funnel, quality, platform_bad, platform_late, risk) -> None:
    tabs = st.tabs(["Xu hướng", "Xảy ra ở đâu", "Seller", "Độ tin cậy dữ liệu"])
    with tabs[0]:
        trend_tab(series, platform_bad)
    with tabs[1]:
        where_tab(regions, categories, platform_late)
    with tabs[2]:
        seller_tab(sellers, funnel, risk)
    with tabs[3]:
        trust_tab(series, quality)
