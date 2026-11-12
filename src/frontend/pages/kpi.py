"""KPI overview. Cards use the same numerator and denominator as the SQL files."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db, queries
from lib.glossary import explain
from lib.insights import build_insight_kpi
from lib.stats import SPARSE_MONTHS
from pages import kpi_panels
from lib.ui import (
    LATE,
    NAVY,
    NEUTRAL,
    add_legend_swatch,
    filters,
    fmt_brl,
    fmt_int,
    fmt_pct,
    highlight_colors,
    kpi_card,
    next_step,
    page_header,
    scope_subtitle,
    signed_pct,
    signed_points,
    style_fig,
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


def _load_base(month_from, month_to, region, state) -> dict:
    monthly = _row(db.query(*queries.kpi_seller_month(month_from, month_to, region, state)))
    orders = _row(db.query(*queries.kpi_orders(month_from, month_to, region, state)))
    return _pack(monthly, orders)


def _previous_window(start: str, end: str) -> tuple[str, str]:
    """The calendar window of the same length that ends the month before start."""

    def index(token: str) -> int:
        year, month = token.split("-", 1)
        return int(year) * 12 + int(month) - 1

    def label(value: int) -> str:
        year, month = divmod(value, 12)
        return f"{year:04d}-{month + 1:02d}"

    span = index(end) - index(start) + 1
    previous_end = index(start) - 1
    return label(previous_end - span + 1), label(previous_end)


def _months_between(start: str, end: str) -> list[str]:
    """Inclusive calendar months from start through end. Tokens are YYYY-MM."""

    def index(token: str) -> int:
        year, month = token.split("-", 1)
        return int(year) * 12 + int(month) - 1

    def label(value: int) -> str:
        year, month = divmod(value, 12)
        return f"{year:04d}-{month + 1:02d}"

    start_i = index(start)
    end_i = index(end)
    if end_i < start_i:
        return []
    return [label(value) for value in range(start_i, end_i + 1)]


def _delta_ready(previous: dict | None, prev_from: str | None, prev_to: str | None) -> bool:
    """Show a delta only when the previous window is large enough and has no thin month."""
    if previous is None or not prev_from or not prev_to:
        return False
    orders = _num(previous.get("valid_orders"))
    if orders is None or orders < MIN_ORDERS:
        return False
    return not any(month in SPARSE_MONTHS for month in _months_between(prev_from, prev_to))


def _card_help(term: str, unit: str, prev_from, prev_to, shown: bool) -> str:
    text = explain(term)
    if prev_from and prev_to:
        text += f" Kỳ so sánh: {prev_from} → {prev_to}."
    text += f" Đơn vị mức thay đổi: {unit}. Xanh là tốt lên."
    if not shown:
        text += (
            " Không hiện mức thay đổi vì kỳ trước không có đủ đơn"
            f" (dưới {MIN_ORDERS}) hoặc có tháng dữ liệu thưa."
        )
    return text


def _has_activity(pack: dict) -> bool:
    for key in ("gmv", "valid_orders", "cancel_n", "late_n", "review_n"):
        value = pack.get(key)
        if value not in (None, 0):
            return True
    return False


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
        name="GMV (R$)",
        marker_color=NAVY,
        customdata=list(zip(data["late_ship_eligible"].fillna(0), data["gmv"].map(fmt_brl))),
        hovertemplate="Tháng %{x}<br>GMV %{customdata[1]}<br>n bàn giao %{customdata[0]:,.0f}<extra></extra>",
    )
    fig.add_scatter(
        x=data["year_month"],
        y=data["late_rate"],
        name="Bàn giao trễ (%)",
        mode="lines+markers",
        marker_color=LATE,
        line=dict(color=LATE, width=2),
        yaxis="y2",
        customdata=data["late_ship_eligible"].fillna(0),
        hovertemplate="Tháng %{x}<br>Bàn giao trễ %{y:.1%}<br>n %{customdata:,.0f}<extra></extra>",
    )
    fig.update_layout(
        height=420,
        yaxis=dict(title="GMV (R$)", tickprefix="R$ ", tickformat=",.0f"),
        yaxis2=dict(
            title="Bàn giao trễ (%)",
            overlaying="y",
            side="right",
            tickformat=".0%",
            showgrid=False,
            range=[0, 0.25],
        ),
        hovermode="x unified",
        barmode="overlay",
    )
    fig.update_xaxes(title="Tháng")
    st.plotly_chart(
        style_fig(fig, "GMV và tỷ lệ bàn giao trễ theo tháng đi cùng nhau thế nào?", scope_subtitle()),
        width="stretch",
    )


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
            name="GMV (R$)",
            showlegend=False,
            marker_color=highlight_colors(data["gmv"].tolist(), NAVY),
            customdata=list(zip(data["n_items"], data["gmv"].map(fmt_brl))),
            hovertemplate="%{y}<br>%{customdata[1]}<br>n item %{customdata[0]:,.0f}<extra></extra>",
        )
    )
    add_legend_swatch(fig, "Cao nhất", NAVY)
    add_legend_swatch(fig, "Các nhóm còn lại", NEUTRAL)
    fig.update_layout(height=max(280, 36 * len(data) + 80), margin_l=150, margin_r=16, margin_b=16)
    fig.update_xaxes(title="GMV (R$)", tickprefix="R$ ", tickformat=",.0f")
    fig.update_yaxes(title="Nhóm danh mục", automargin=True)
    st.plotly_chart(
        style_fig(fig, "Nhóm danh mục nào mang lại nhiều GMV nhất?", scope_subtitle()),
        width="stretch",
    )


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
            name="Bàn giao trễ (%)",
            showlegend=False,
            marker_color=highlight_colors(data["late_rate"].tolist(), LATE),
            customdata=data["late_ship_eligible"],
            hovertemplate="%{y}<br>%{x:.1%}<br>n %{customdata:,.0f}<extra></extra>",
        )
    )
    add_legend_swatch(fig, "Cao nhất", LATE)
    add_legend_swatch(fig, "Các nhóm còn lại", NEUTRAL)
    fig.update_layout(height=max(240, 42 * len(data) + 80), margin_l=140, margin_b=16)
    fig.update_xaxes(title="Bàn giao trễ (%)", tickformat=".0%")
    fig.update_yaxes(title="Vùng seller", automargin=True)
    st.plotly_chart(
        style_fig(
            fig,
            "Vùng seller nào bàn giao trễ cao nhất?",
            scope_subtitle(include_region=False, extra="mọi vùng"),
        ),
        width="stretch",
    )


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


def _month_phrase(token) -> str:
    parts = str(token).split("-")
    if len(parts) >= 2 and len(parts[1]) == 2:
        return f"Tháng {parts[1]}/{parts[0]}"
    return str(token)


def _kpi_conclusion(series: pd.DataFrame | None, story: pd.DataFrame | None) -> str:
    """Latest dense month versus the month before it, plus the worst region."""
    from lib.insights import _groups, _worst_group
    from lib.stats import SPARSE_MONTHS

    if series is None or series.empty or "bad_experience_count" not in series.columns:
        if story is None:
            return "Chưa đủ dữ liệu để kết luận."
        return build_insight_kpi(story, MIN_ORDERS)
    data = series.copy()
    data["bad_orders"] = pd.to_numeric(data["bad_experience_count"], errors="coerce")
    data["eligible"] = pd.to_numeric(data["bad_experience_eligible"], errors="coerce")
    data = data.dropna(subset=["year_month"]).sort_values("year_month")
    dense = data[~data["year_month"].astype(str).isin(SPARSE_MONTHS)]
    use = dense if not dense.empty else data
    if use.empty:
        return "Chưa đủ dữ liệu để kết luận."
    last = use.iloc[-1]
    rate = _ratio(last["bad_orders"], last["eligible"])
    if rate is None:
        return "Chưa đủ dữ liệu để kết luận."
    direction = ""
    if len(use) >= 2:
        previous = use.iloc[-2]
        previous_rate = _ratio(previous["bad_orders"], previous["eligible"])
        points = signed_points(rate, previous_rate)
        if points:
            direction = f", {points} so với tháng trước"
    region = ""
    if story is not None:
        _total, groups = _groups(story, MIN_ORDERS)
        if not groups.empty:
            worst = _worst_group(groups)
            region = f"; vùng {worst['region_name']} cao nhất"
    return f"{_month_phrase(last['year_month'])}: {fmt_pct(rate)} đơn xấu{direction}{region}."


def render(settings=None) -> None:
    del settings
    chosen = filters()
    month_from = chosen.get("month_from")
    month_to = chosen.get("month_to")
    region = chosen.get("region")
    state = chosen.get("state")
    category = chosen.get("category")
    if month_from and month_to and month_from > month_to:
        st.warning("Từ tháng đang sau Đến tháng. Chọn lại khoảng thời gian ở sidebar.")
        return
    funnel_label = chosen.get("funnel") or "Tất cả"
    funnel = {"Có closed deal": 1, "Không có closed deal": 0}.get(funnel_label)
    start, end = month_from, month_to
    try:
        with st.spinner("Đang tải dữ liệu…"):
            current = _load_base(start, end, region, state)
            previous = None
            prev_from = prev_to = None
            if start and end:
                prev_from, prev_to = _previous_window(start, end)
                prior = _load_base(prev_from, prev_to, region, state)
                if _has_activity(prior):
                    previous = prior
            if category is not None:
                scoped = _row(db.query(*queries.kpi_for_category(start, end, region, state, category)))
                current = _pack_category(scoped, current)
                if previous is not None:
                    prior_scoped = _row(
                        db.query(*queries.kpi_for_category(prev_from, prev_to, region, state, category))
                    )
                    scoped_orders = _num(prior_scoped.get("placed_orders"))
                    scoped_gmv = _num(prior_scoped.get("gmv"))
                    if scoped_orders in (None, 0) and scoped_gmv in (None, 0):
                        previous = None
                    else:
                        previous = _pack_category(prior_scoped, previous)
            categories = db.query(*queries.kpi_top_categories(start, end, region, state))
            regions = db.query(*queries.kpi_late_by_region(start, end, state))
            story = db.query(*queries.story_by_region(start, end, region, state, category))
            series = db.query(*queries.seller_month_series(region, state, funnel, start, end))
    except Exception as exc:
        page_header("Sức khỏe marketplace đang thế nào?", "Chưa tải được dữ liệu để kết luận.", "actual")
        db.show_warehouse_error(exc)
        next_step("kpi")
        return
    page_header(
        "Sức khỏe marketplace đang thế nào?",
        _kpi_conclusion(series, story),
        "actual",
    )
    st.caption(
        f"Tháng {start or 'đầu kỳ'} → {end or 'cuối kỳ'} · vùng {region or 'tất cả'} · "
        f"bang {state or 'tất cả'}"
        + (f" · {funnel_label}" if funnel is not None else "")
    )

    def _growth(now, before):
        if now is None or before in (None, 0):
            return None
        return (now - before) / abs(before)

    show_delta = _delta_ready(previous, prev_from, prev_to)
    money_delta = points_late = points_review = points_cancel = orders_delta = aov_delta = None
    if show_delta:
        money_delta = signed_pct(_growth(current["gmv"], previous["gmv"]))
        orders_delta = signed_pct(_growth(current["valid_orders"], previous["valid_orders"]))
        aov_delta = signed_pct(_growth(current["aov"], previous["aov"]))
        points_late = signed_points(current["late_rate"], previous["late_rate"])
        points_review = signed_points(current["review_rate"], previous["review_rate"])
        points_cancel = signed_points(current["cancel_rate"], previous["cancel_rate"])

    specs = [
        ("GMV", fmt_brl(current["gmv"]), money_delta, _card_help("gmv", "%", prev_from, prev_to, show_delta), "normal"),
        ("Số đơn", fmt_int(current["valid_orders"]), orders_delta, _card_help("valid_orders", "%", prev_from, prev_to, show_delta), "normal"),
        ("AOV", fmt_brl(current["aov"]), aov_delta, _card_help("aov", "%", prev_from, prev_to, show_delta), "normal"),
        ("Bàn giao trễ", fmt_pct(current["late_rate"]), points_late, _card_help("late_ship", "điểm %", prev_from, prev_to, show_delta), "inverse"),
        ("Review xấu (theo seller)", fmt_pct(current["review_rate"]), points_review, _card_help("negative_review", "điểm %", prev_from, prev_to, show_delta), "inverse"),
        ("Cancel rate", fmt_pct(current["cancel_rate"]), points_cancel, _card_help("cancel_rate", "điểm %", prev_from, prev_to, show_delta), "inverse"),
    ]
    st.markdown("### Tổng quan kỳ")
    for offset in (0, 3):
        for column, (label, value, delta, help_text, color) in zip(st.columns(3), specs[offset : offset + 3]):
            with column:
                kpi_card(label, value, delta=delta, help_text=help_text, delta_color=color)

    quality = scatter = sellers = funnel_frame = snapshot = None
    try:
        with st.spinner("Đang tải dữ liệu…"):
            quality = db.query(*queries.market_quality(start, end, region, state))
            scatter = db.query(*queries.category_scatter(start, end, region, state))
            sellers = db.query(*queries.seller_pareto(region, state, funnel, start, end, 1))
            funnel_frame = db.query(*queries.funnel_compare(region, state, start, end))
            snapshot = db.query(*queries.policy_snapshot())
    except Exception as exc:
        st.error(db.redact(exc))
    if quality is not None and not quality.empty:
        row = quality.iloc[0]
        rate = None if not row["bad_eligible"] else float(row["bad_orders"]) / float(row["bad_eligible"])
        previous_rate = None
        if previous is not None:
            previous_rate = None
        kpi_panels.hero(
            pd.DataFrame([{
                "is_total": 1,
                "bad_orders": row["bad_orders"],
                "eligible_orders": row["bad_eligible"],
            }]),
            previous_rate,
        )
    if snapshot is not None:
        kpi_panels.constraint_strip(snapshot)
    st.divider()
    st.markdown("### Xu hướng theo tháng")
    st.caption(
        f"Theo tháng · {start or 'đầu kỳ'} → {end or 'cuối kỳ'} · "
        f"vùng {region or 'tất cả'} · bang {state or 'tất cả'}"
    )
    if series is not None:
        kpi_panels.grouped_cards(current, series)
        platform_bad = None
        platform_late = current["late_rate"]
        if quality is not None and not quality.empty and quality.iloc[0]["bad_eligible"]:
            platform_bad = float(quality.iloc[0]["bad_orders"]) / float(quality.iloc[0]["bad_eligible"])
        kpi_panels.render_tabs(
            series, regions, scatter if scatter is not None else categories,
            sellers, funnel_frame, quality, platform_bad, platform_late, _risk_table,
        )
    next_step("kpi")
