"""Analytic panels for the KPI page. Rates are recomputed from counts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db, queries
from lib.glossary import explain
from lib.insights import recommend_policy
from lib.labels import fmt_count, fmt_limit, fmt_number, fmt_percent_points, policy_name
from lib.stats import SPARSE_MONTHS, pareto, wilson_ci
from lib.ui import (
    LATE,
    MIN_N_DISPLAY,
    NAVY,
    REVIEW,
    add_legend_swatch,
    add_platform_reference,
    add_vertical_platform_reference,
    badge_actual,
    chart_note,
    count_axis_ticks,
    filters,
    fmt_brl,
    fmt_int,
    fmt_pct,
    button_dropdown,
    kpi_card,
    point_opacity,
    scope_subtitle,
    style_fig,
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


def _spark_text(column: str, value) -> str:
    if column in ("gmv", "aov"):
        return fmt_brl(value)
    if column in ("n_orders_valid", "active_sellers"):
        return fmt_int(value)
    if column in ("late_delivery_rate", "late_ship_rate", "review_rate", "cancel_rate"):
        return fmt_pct(value)
    return fmt_number(value)


def _spark(frame: pd.DataFrame, value_column: str) -> None:
    """One line. The page caption carries the period, so this chart has no subtitle."""
    if frame is None or frame.empty or value_column not in frame.columns:
        return
    work = frame.dropna(subset=["year_month", value_column]).sort_values("year_month")
    if work.empty:
        return
    work = work.copy()
    work["year_month"] = work["year_month"].astype(str)
    first = work["year_month"].iloc[0]
    last = work["year_month"].iloc[-1]
    last_value = work[value_column].iloc[-1]
    ticks = [first] if first == last else [first, last]
    figure = go.Figure(
        go.Scatter(
            x=work["year_month"],
            y=work[value_column],
            mode="lines",
            line=dict(color=NAVY, width=2),
            hovertemplate="%{x}<br>%{y}<extra></extra>",
            showlegend=False,
        )
    )
    figure.add_scatter(
        x=[last],
        y=[last_value],
        mode="markers+text",
        text=[_spark_text(value_column, last_value)],
        textposition="top center",
        marker=dict(color=NAVY, size=8),
        hoverinfo="skip",
        showlegend=False,
    )
    figure.update_layout(height=240)
    figure.update_yaxes(visible=False, showgrid=False)
    styled = style_fig(figure, "Theo tháng", legend=False)
    styled.update_xaxes(
        type="category",
        tickmode="array",
        tickvals=ticks,
        ticktext=ticks,
        showgrid=False,
    )
    st.plotly_chart(styled, width="stretch")


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
        "aov": ("gmv", "n_orders_valid"),
    }
    for name, (top, bottom) in pairs.items():
        if top in data.columns and bottom in data.columns:
            data[name] = [
                _rate(row[top], row[bottom]) for row in data.to_dict("records")
            ]
    return data


def constraint_strip(snapshot: pd.DataFrame) -> None:
    st.markdown("**Trạng thái so với ràng buộc**")
    st.caption("Tính trên toàn bộ phạm vi, không theo bộ lọc")
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

    def _pair(column, label, value, help_text, spark):
        with column:
            with st.container(border=True):
                kpi_card(label, value, help_text=help_text, border=False)
                _spark(tail(spark), spark)

    st.markdown("**Quy mô**")
    columns = st.columns(4)
    blocks = [
        ("GMV", fmt_brl(current["gmv"]), explain("gmv"), "gmv"),
        ("Số đơn", fmt_int(current["valid_orders"]), explain("valid_orders"), "n_orders_valid"),
        ("AOV", fmt_brl(current["aov"]), explain("aov"), "aov"),
        ("Seller hoạt động tháng cuối đủ dữ liệu", fmt_int(None if latest is None else latest.get("active_sellers")), explain("active_sellers"), "active_sellers"),
    ]
    for column, block in zip(columns, blocks):
        _pair(column, *block)
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
    for column, block in zip(columns, quality):
        _pair(column, *block)
    st.markdown("**Vận hành**")
    columns = st.columns(2)
    operations = [
        ("Điểm review trung bình", fmt_number(review), explain("negative_review"), "avg_review"),
        ("Số ngày xử lý trung bình", fmt_number(handling), "handling_days_sum / handling_days_count.", "avg_handling_days"),
    ]
    for column, block in zip(columns, operations):
        _pair(column, *block)


def trend_tab(series: pd.DataFrame, platform_bad) -> None:
    data = _with_rates(series)
    if data.empty:
        st.info("Chưa đủ dữ liệu để kết luận.")
        return
    labels = {
        "bad_rate": "Đơn trải nghiệm xấu",
        "late_delivery_rate": "Giao trễ tới khách",
        "late_ship_rate": "Bàn giao trễ",
        "review_rate": "Review xấu (theo seller)",
        "cancel_rate": "Cancel rate",
    }
    choice = button_dropdown(
        "Đường tỷ lệ",
        ("bad_rate", "late_delivery_rate", "late_ship_rate", "review_rate", "cancel_rate"),
        "trend_rate",
        format_func=lambda name: labels[name],
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
    rate_name = f"{labels[choice]} (%)"
    figure = go.Figure()
    solid = data[~data["sparse"]]
    thin = data[data["sparse"]]
    if not solid.empty:
        figure.add_bar(x=solid["year_month"], y=solid["gmv"], name="GMV (R$)", marker_color=NAVY, opacity=0.85)
    if not thin.empty:
        figure.add_bar(
            x=thin["year_month"],
            y=thin["gmv"],
            name="Tháng dữ liệu thưa",
            marker_color="#c5cdd6",
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
        name=rate_name,
        mode="lines+markers",
        marker=dict(color=LATE, opacity=point_opacity(data[count_column])),
        yaxis="y2",
        error_y=dict(type="data", array=errors_plus, arrayminus=errors_minus, thickness=1),
        customdata=data[count_column],
        hovertemplate="%{x}<br>%{y:.1%}<br>n %{customdata:,.0f}<extra></extra>",
    )
    figure.update_layout(
        height=440,
        yaxis=dict(title="GMV (R$)"),
        yaxis2=dict(title=rate_name, overlaying="y", side="right", tickformat=".0%"),
        hovermode="x unified",
        barmode="overlay",
    )
    figure.update_xaxes(title="Tháng")
    add_platform_reference(figure, platform_bad if choice == "bad_rate" else None, yref="y2")
    st.plotly_chart(
        style_fig(
            figure,
            f"GMV và {labels[choice].lower()} theo tháng thay đổi ra sao?",
            scope_subtitle(include_months=True, include_funnel=True),
        ),
        width="stretch",
    )
    st.caption(f"Tháng tô nhạt là tháng dữ liệu thưa. Điểm mờ: dưới {fmt_int(MIN_N_DISPLAY)} mẫu.")
    peak = data[data[count_column] >= MIN_N_DISPLAY].dropna(subset=[choice]).sort_values(choice, ascending=False).head(1)
    if not peak.empty:
        row = peak.iloc[0]
        st.info(
            f"Tỷ lệ cao nhất trong bộ lọc là {row['year_month']}: {fmt_pct(row[choice])} "
            f"(n={fmt_int(row[count_column])})."
        )

    _bad_events_stack(data)


def _bad_events_stack(data: pd.DataFrame) -> None:
    if data is None or data.empty:
        st.info("Chưa có sự kiện xấu trong kỳ chọn.")
        return
    work = data.sort_values("year_month").copy()
    components = (
        ("Bàn giao trễ", "late_ship_count", LATE),
        ("Review tiêu cực", "negative_review_count", REVIEW),
        ("Hủy đơn", "cancel_count", NAVY),
    )
    for _, column, _ in components:
        if column in work.columns:
            work[column] = pd.to_numeric(work[column], errors="coerce").fillna(0.0)
        else:
            work[column] = 0.0
    work["event_total"] = work["late_ship_count"] + work["negative_review_count"] + work["cancel_count"]
    totals = [(label, float(work[column].sum())) for label, column, _ in components]
    grand_total = sum(val for _, val in totals)
    if grand_total <= 0:
        st.info("Chưa có sự kiện xấu trong kỳ chọn.")
        return

    top_label, top_value = max(totals, key=lambda item: item[1])
    st.write(f"Trong kỳ chọn, {top_label} chiếm {fmt_pct(top_value / grand_total)} sự kiện xấu.")

    mode = st.segmented_control(
        "Chế độ hiển thị",
        ["Số lượng", "Tỷ trọng %"],
        default="Số lượng",
        key="trend_bad_events_mode",
    )
    is_pct = mode == "Tỷ trọng %"

    sparse_flags = work["year_month"].isin(SPARSE_MONTHS).tolist()
    opacities = [0.35 if is_sparse else 0.9 for is_sparse in sparse_flags]
    month_totals = work["event_total"].tolist()

    figure = go.Figure()
    for label, column, color in components:
        counts = work[column].tolist()
        shares = [
            0.0 if m_total <= 0 else cnt / m_total
            for cnt, m_total in zip(counts, month_totals)
        ]
        figure.add_bar(
            x=work["year_month"],
            y=counts,
            name=label,
            marker=dict(color=color, opacity=opacities),
            customdata=list(zip(counts, shares)),
            hovertemplate=f"Tháng %{{x}}<br>{label}: %{{customdata[0]:,.0f}} sự kiện (%{{customdata[1]:.1%}})<extra></extra>",
        )
    if any(sparse_flags):
        add_legend_swatch(figure, "Tháng dữ liệu thưa", "#8a93a0", opacity=0.35)

    layout_kwargs = dict(height=380, barmode="stack", hovermode="x unified")
    if is_pct:
        layout_kwargs["barnorm"] = "fraction"
    figure.update_layout(**layout_kwargs)
    figure.update_xaxes(title="Tháng", type="category")
    if is_pct:
        figure.update_yaxes(title="Tỷ trọng (%)")
    else:
        figure.update_yaxes(title="Số sự kiện", **count_axis_ticks(month_totals))
    st.plotly_chart(
        style_fig(figure, "Tháng xấu là do khâu nào?", scope_subtitle()),
        width="stretch",
    )
    chart_note(
        "Một đơn có thể vừa trễ vừa bị review xấu nên tổng cột là số sự kiện, "
        "có thể lớn hơn số đơn xấu ở thẻ KPI."
    )


_WHERE_METRICS = (
    ("Tỷ lệ đơn trải nghiệm xấu", "bad_experience_count", "bad_experience_eligible", True),
    ("Giao trễ tới khách", "late_delivery_count", "late_delivery_eligible", True),
    ("Bàn giao trễ", "late_ship_count", "late_ship_eligible", True),
    ("Review xấu", "negative_review_count", "negative_review_eligible", True),
    ("GMV", "gmv", "n_items_valid", False),
)
_SUM_COLUMNS = (
    "gmv",
    "n_items_valid",
    "bad_experience_count",
    "bad_experience_eligible",
    "late_delivery_count",
    "late_delivery_eligible",
    "late_ship_count",
    "late_ship_eligible",
    "negative_review_count",
    "negative_review_eligible",
)
_PAIR_HEIGHT = 360
_ORANGE_SCALE = [[0, "#fde8d8"], [0.55, "#f0a06a"], [1, "#d9622b"]]
_NAVY_SCALE = [[0, "#d6e2f0"], [1, "#1f3a5f"]]


def _text(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()


@st.cache_data
def _brazil_states() -> tuple[dict, dict[str, str]]:
    path = Path(__file__).resolve().parents[1] / "assets" / "brazil_states.geojson"
    payload = json.loads(path.read_text(encoding="utf-8"))
    names: dict[str, str] = {}
    for feature in payload.get("features", []):
        props = feature.get("properties") or {}
        code = _text(props.get("sigla")).upper()
        if code:
            names[code] = _text(props.get("name")) or code
    return payload, names


def _clean_geo(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["state_code", "region_name", *_SUM_COLUMNS]
    if frame is None or frame.empty:
        return pd.DataFrame(columns=columns)
    out = frame.copy()
    for column in _SUM_COLUMNS:
        if column not in out.columns:
            out[column] = 0
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0)
    out["state_code"] = out["state_code"].map(lambda value: _text(value).upper())
    out["region_name"] = out["region_name"].map(lambda value: _text(value) or "(không map được vùng)")
    return out


def _with_metric(frame: pd.DataFrame, numerator: str, denominator: str, is_rate: bool) -> pd.DataFrame:
    out = frame.copy()
    out["numerator"] = pd.to_numeric(out[numerator], errors="coerce").fillna(0)
    out["n"] = pd.to_numeric(out[denominator], errors="coerce").fillna(0)
    if is_rate:
        out["value"] = [_rate(top, bottom) for top, bottom in zip(out["numerator"], out["n"])]
    else:
        out["value"] = out["numerator"]
    return out


def _selected_state(event) -> str | None:
    if event is None:
        return None
    selection = event["selection"] if isinstance(event, dict) else getattr(event, "selection", None)
    if selection is None:
        return None
    points = selection["points"] if isinstance(selection, dict) else getattr(selection, "points", None)
    if not points:
        return None
    point = points[0]
    if not isinstance(point, dict):
        return None
    custom = point.get("customdata")
    if isinstance(custom, str) and custom:
        return _text(custom).upper()
    if custom is not None:
        try:
            return _text(custom[0]).upper() or None
        except (TypeError, IndexError, KeyError):
            pass
    location = point.get("location")
    return _text(location).upper() or None


def _state_rows(cleaned: pd.DataFrame, names: dict[str, str]) -> pd.DataFrame:
    known = cleaned[cleaned["state_code"].isin(names)].copy()
    if known.empty:
        collapsed = pd.DataFrame(columns=["state_code", "region_name", *_SUM_COLUMNS])
    else:
        collapsed = known.groupby("state_code", as_index=False).agg(
            {**{column: "sum" for column in _SUM_COLUMNS}, "region_name": "first"}
        )
    collapsed = collapsed.set_index("state_code")
    rows = []
    for code, name in names.items():
        if code in collapsed.index:
            row = collapsed.loc[code]
            region = _text(row["region_name"]) or "(không map được vùng)"
            values = {column: float(row[column]) for column in _SUM_COLUMNS}
        else:
            region = "(không map được vùng)"
            values = {column: 0.0 for column in _SUM_COLUMNS}
        rows.append({"state_code": code, "state_name": name, "region_name": region, **values})
    return pd.DataFrame(rows)


def _hover_rows(frame: pd.DataFrame, label: str, is_rate: bool) -> list[list[str]]:
    rows = []
    for row in frame.itertuples(index=False):
        metric = f"{label}: {fmt_pct(row.value) if is_rate else fmt_brl(row.value)}"
        rows.append([
            row.state_code,
            row.state_name,
            row.region_name,
            metric,
            fmt_int(row.n),
            fmt_brl(row.gmv_show),
            "Mẫu nhỏ" if float(row.n) < MIN_N_DISPLAY else "",
        ])
    return rows


def _choropleth(frame: pd.DataFrame, label: str, is_rate: bool, level: str) -> None:
    geojson, _names = _brazil_states()
    small = frame["n"].fillna(0) < MIN_N_DISPLAY
    missing = frame["value"].isna()
    colored = frame.loc[~small & ~missing].copy()
    gray = frame.loc[small | missing].copy()
    figure = go.Figure()
    hover = (
        "<b>%{customdata[1]}</b> (%{customdata[0]})<br>"
        "Vùng: %{customdata[2]}<br>%{customdata[3]}<br>"
        "n %{customdata[4]}<br>GMV %{customdata[5]}<br>%{customdata[6]}<extra></extra>"
    )
    if not colored.empty:
        peak = float(pd.to_numeric(colored["value"], errors="coerce").max())
        figure.add_trace(go.Choropleth(
            geojson=geojson,
            locations=colored["state_code"],
            z=colored["value"],
            featureidkey="properties.sigla",
            colorscale=_ORANGE_SCALE if is_rate else _NAVY_SCALE,
            zmin=0,
            zmax=peak if peak > 0 else 1,
            marker_line_color="#ffffff",
            marker_line_width=0.6,
            colorbar=dict(
                title=f"{label} (%)" if is_rate else f"{label} (R$)",
                tickformat=".0%" if is_rate else ",.0f",
                len=0.9,
            ),
            customdata=_hover_rows(colored, label, is_rate),
            hovertemplate=hover,
            name="",
            showscale=True,
        ))
    if not gray.empty:
        figure.add_trace(go.Choropleth(
            geojson=geojson,
            locations=gray["state_code"],
            z=[0] * len(gray),
            featureidkey="properties.sigla",
            colorscale=[[0, "#d9d9d9"], [1, "#d9d9d9"]],
            showscale=False,
            marker_line_color="#ffffff",
            marker_line_width=0.6,
            customdata=_hover_rows(gray, label, is_rate),
            hovertemplate=hover,
            name="",
        ))
    figure.update_layout(height=640)
    badge_actual()
    style_fig(
        figure,
        f"{label} đang cao ở bang nào?",
        scope_subtitle(extra=level),
        legend=False,
    )
    figure.update_layout(
        height=640,
        margin=dict(t=88, b=0, l=0, r=4),
        title=dict(y=1, yanchor="bottom", yref="paper"),
    )
    figure.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
        showframe=False,
        showcoastlines=False,
        showcountries=False,
        showland=False,
        showlakes=False,
        showocean=False,
        projection_type="mercator",
        projection_scale=1.2,
        domain=dict(x=[0.0, 0.82], y=[0.0, 1.0]),
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    event = st.plotly_chart(
        figure,
        width="stretch",
        theme=None,
        on_select="rerun",
        selection_mode="points",
        key="where_brazil_map",
    )
    picked = _selected_state(event)
    current = _text(st.session_state.get("filter_state")).upper()
    if picked and picked != current:
        st.session_state["pending_filter_state"] = picked
        st.rerun()
    if is_rate:
        chart_note("Màu càng đậm, tỷ lệ càng cao; bang xám là bang có dưới 30 đơn.")
    else:
        chart_note("Màu càng đậm, GMV càng cao; bang xám là bang có dưới 30 đơn.")


def _place_bar(frame: pd.DataFrame, label: str, is_rate: bool, place: str) -> None:
    data = frame[frame["n"] > 0].dropna(subset=["value"]).sort_values("value", ascending=True)
    if data.empty:
        st.info("Không có đủ mẫu cho chỉ số này trong bộ lọc.")
        return
    counts = pd.to_numeric(data["n"], errors="coerce").fillna(0)
    hidden = int((counts < MIN_N_DISPLAY).sum())
    data = data.loc[counts >= MIN_N_DISPLAY]
    if data.empty:
        st.info("Không có đủ mẫu cho chỉ số này trong bộ lọc.")
        st.caption(f"Ẩn {fmt_int(hidden)} nhóm có dưới {fmt_int(MIN_N_DISPLAY)} mẫu")
        return
    color = LATE if is_rate else NAVY
    errors = []
    if is_rate:
        for top, bottom, rate in zip(data["numerator"], data["n"], data["value"]):
            high = wilson_ci(top, bottom)[1]
            errors.append(0 if high is None or rate is None else max(0, high - rate))
    hover = (
        "%{y}<br>%{x:.1%}<br>n %{customdata[0]:,.0f}<br>GMV R$ %{customdata[1]:,.0f}<extra></extra>"
        if is_rate
        else "%{y}<br>R$ %{x:,.0f}<br>n %{customdata[0]:,.0f}<extra></extra>"
    )
    figure = go.Figure(go.Bar(
        x=data["value"],
        y=data["label"],
        orientation="h",
        name=label,
        showlegend=False,
        marker=dict(color=color),
        error_x=dict(type="data", array=errors) if is_rate else None,
        customdata=list(zip(data["n"], data["gmv"])),
        hovertemplate=hover,
    ))
    add_legend_swatch(figure, label, color)
    if is_rate:
        add_vertical_platform_reference(figure, _rate(data["numerator"].sum(), data["n"].sum()))
    axis = f"{label} (%)" if is_rate else "GMV (R$)"
    figure.update_layout(height=_PAIR_HEIGHT, margin_l=120, margin_b=12)
    figure.update_xaxes(title=axis, tickformat=".0%" if is_rate else ",.0f", tickprefix=None if is_rate else "R$ ")
    figure.update_yaxes(
        title=place,
        automargin=True,
        categoryorder="array",
        categoryarray=list(data["label"]),
    )
    st.plotly_chart(
        style_fig(figure, f"{label} đang cao ở {place.lower()} nào?", scope_subtitle()),
        width="stretch",
        key="where_bar",
    )
    if is_rate:
        chart_note(
            f"Thanh vượt đường đứt là {place.lower()} tệ hơn trung bình sàn; "
            "thanh sai số dài nghĩa là ít đơn, kém chắc chắn."
        )
    else:
        chart_note(f"Thanh dài hơn là {place.lower()} có GMV cao hơn.")
    st.caption(f"Ẩn {fmt_int(hidden)} nhóm có dưới {fmt_int(MIN_N_DISPLAY)} mẫu")


def _category_scatter(categories: pd.DataFrame) -> None:
    if categories is None or categories.empty or "bad_orders" not in categories.columns:
        return
    data = categories.copy()
    data["gmv"] = pd.to_numeric(data["gmv"], errors="coerce")
    data["bad_orders"] = pd.to_numeric(data["bad_orders"], errors="coerce")
    data["eligible_orders"] = pd.to_numeric(data["eligible_orders"], errors="coerce")
    data["rate"] = [_rate(top, bottom) for top, bottom in zip(data["bad_orders"], data["eligible_orders"])]
    if "orders" in data.columns:
        orders = pd.to_numeric(data["orders"], errors="coerce").fillna(0)
    else:
        orders = data["eligible_orders"].fillna(0)
    peak = float(orders.max()) if len(orders) else 0.0
    sizes = (orders / peak * 36).clip(lower=8) if peak > 0 else 8
    platform = _rate(data["bad_orders"].sum(), data["eligible_orders"].sum())
    top_index = data["gmv"].fillna(0).sort_values(ascending=False).head(5).index
    top_names = set(data.loc[top_index, "category_group"].astype(str))
    labels = []
    for name, rate in zip(data["category_group"].astype(str), data["rate"]):
        above = platform is not None and rate is not None and rate > platform
        labels.append(name if name in top_names or above else "")
    figure = go.Figure(go.Scatter(
        x=data["gmv"],
        y=data["rate"],
        name="Nhóm danh mục",
        mode="markers+text",
        text=labels,
        textposition="top center",
        textfont=dict(size=11, color=NAVY),
        showlegend=False,
        marker=dict(size=sizes, color=NAVY, opacity=point_opacity(data["eligible_orders"])),
        customdata=list(zip(data["category_group"].astype(str), data["eligible_orders"], data["gmv"])),
        hovertemplate="%{customdata[0]}<br>n %{customdata[1]:,.0f}<br>GMV R$ %{customdata[2]:,.0f}<extra></extra>",
    ))
    figure.add_scatter(
        x=[None], y=[None], mode="markers", name="Ít đơn",
        marker=dict(size=8, color=NAVY), hoverinfo="skip",
    )
    figure.add_scatter(
        x=[None], y=[None], mode="markers", name="Nhiều đơn",
        marker=dict(size=22, color=NAVY), hoverinfo="skip",
    )
    add_platform_reference(figure, platform)
    figure.update_layout(height=_PAIR_HEIGHT)
    figure.update_xaxes(title="GMV (R$)")
    figure.update_yaxes(title="Tỷ lệ đơn xấu (%)", tickformat=".0%")
    st.plotly_chart(
        style_fig(
            figure,
            "Nhóm hàng nào có GMV cao và tỷ lệ đơn xấu cao?",
            scope_subtitle(),
        ),
        width="stretch",
        key="where_scatter",
    )
    chart_note("Góc trên-phải là nhóm hàng vừa bán nhiều vừa nhiều đơn xấu, cần ưu tiên xử lý.")
    st.caption(f"Điểm mờ: dưới {fmt_int(MIN_N_DISPLAY)} mẫu")


def where_tab(regions: pd.DataFrame, categories: pd.DataFrame, platform_late) -> None:
    del regions, platform_late
    level_col, metric_col = st.columns(2)
    with level_col:
        level = button_dropdown("Mức địa lý", ("Vùng", "Bang"), "where_level")
    with metric_col:
        label = button_dropdown("Chỉ số", [item[0] for item in _WHERE_METRICS], "where_metric")
    geography = st.radio(
        "Địa lý trên bản đồ",
        ("Bang seller", "Bang khách"),
        horizontal=True,
        index=0,
        key="where_geography",
    )
    spec = next(item for item in _WHERE_METRICS if item[0] == label)
    _label, numerator, denominator, is_rate = spec
    chosen = filters()
    month_from = chosen.get("month_from")
    month_to = chosen.get("month_to")
    region = chosen.get("region")
    state = chosen.get("state")
    _category = chosen.get("category")
    side = "seller" if geography == "Bang seller" else "customer"
    try:
        fetched = db.query(*queries.kpi_where_by_state(month_from, month_to, region, state, side))
    except Exception as exc:
        st.error(db.redact(exc))
        _category_scatter(categories)
        return
    _geojson, names = _brazil_states()
    cleaned = _clean_geo(fetched)
    states = _state_rows(cleaned, names)
    if cleaned.empty:
        regions_now = pd.DataFrame(columns=["region_name", *_SUM_COLUMNS])
    else:
        regions_now = cleaned.groupby("region_name", as_index=False)[list(_SUM_COLUMNS)].sum()
    state_metric = _with_metric(states, numerator, denominator, is_rate)
    region_metric = _with_metric(regions_now, numerator, denominator, is_rate)
    state_metric["gmv_show"] = state_metric["gmv"]
    if level == "Vùng":
        lookup = region_metric.set_index("region_name")

        def _from_region(name, column):
            if name not in lookup.index:
                return 0 if column != "value" else None
            return lookup.at[name, column]

        state_metric["value"] = state_metric["region_name"].map(lambda name: _from_region(name, "value"))
        state_metric["n"] = state_metric["region_name"].map(lambda name: _from_region(name, "n"))
        state_metric["numerator"] = state_metric["region_name"].map(lambda name: _from_region(name, "numerator"))
        state_metric["gmv_show"] = state_metric["region_name"].map(lambda name: _from_region(name, "gmv"))
        bar = region_metric.copy()
        bar["label"] = bar["region_name"]
        place = "Vùng"
    else:
        bar = state_metric.copy()
        bar["label"] = bar["state_code"] + " · " + bar["state_name"]
        place = "Bang"
    _choropleth(state_metric, label, is_rate, level)
    left, right = st.columns(2)
    with left:
        _place_bar(bar, label, is_rate, place)
    with right:
        _category_scatter(categories)


def seller_tab(sellers: pd.DataFrame, funnel: pd.DataFrame, risk) -> None:
    if sellers is not None and not sellers.empty:
        ranked = pareto(sellers)
        mark = ranked[ranked["sellers"] <= int(N)].tail(1)
        figure = go.Figure(
            go.Scatter(
                x=ranked["seller_share"],
                y=ranked["bad_share"],
                name="Đơn xấu cộng dồn (%)",
                mode="lines",
                line=dict(color=NAVY),
            )
        )
        if not mark.empty:
            figure.add_scatter(
                x=mark["seller_share"],
                y=mark["bad_share"],
                mode="markers",
                name=f"{fmt_int(N)} seller tệ nhất",
                marker=dict(color=LATE, size=12),
            )
        figure.update_layout(height=360)
        figure.update_xaxes(tickformat=".0%", title="Seller, tệ nhất trước (%)")
        figure.update_yaxes(tickformat=".0%", title="Đơn xấu cộng dồn (%)")
        st.plotly_chart(
            style_fig(
                figure,
                "Phần đơn xấu tập trung vào nhóm seller tệ nhất đến mức nào?",
                scope_subtitle(include_months=True, include_funnel=True),
            ),
            width="stretch",
        )
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
            name="Seller",
            mode="markers",
            marker=dict(size=8, color=NAVY, opacity=point_opacity(kept["eligible_orders"])),
        ))
        figure.update_layout(height=360)
        figure.update_xaxes(title="Số đơn", **count_axis_ticks(kept["n_orders_valid"]))
        figure.update_yaxes(title="Đơn trải nghiệm xấu (%)", tickformat=".0%")
        st.plotly_chart(
            style_fig(
                figure,
                "Tỷ lệ đơn xấu thay đổi thế nào theo số đơn của seller?",
                scope_subtitle(include_months=True, include_funnel=True),
            ),
            width="stretch",
        )
        st.caption(f"Điểm mờ: dưới {fmt_int(MIN_N_DISPLAY)} mẫu")
    if funnel is not None and not funnel.empty:
        for row in funnel.itertuples(index=False):
            label = "Có closed deal" if int(row.has_closed_deal) == 1 else "Không có closed deal"
            st.write(
                f"{label}: {fmt_pct(_rate(row.bad_orders, row.eligible_orders))} "
                f"(n={fmt_int(row.eligible_orders)}, {fmt_int(row.sellers)} seller)."
            )
        st.caption(
            "n của hai nhóm là tổng lượt đơn đủ điều kiện tính trải nghiệm xấu theo từng seller "
            "(có review hoặc ngày giao trên fact_seller_monthly; đơn nhiều seller được tính cho mỗi seller), "
            "nên khác với KPI Số đơn hợp lệ phân biệt toàn sàn."
        )
    risk()
    pages = st.session_state.get("nav_pages", {})
    if pages.get("risk") is not None:
        st.page_link(pages["risk"], label="Mở trang Seller risk")


def trust_tab(series: pd.DataFrame, quality: pd.DataFrame) -> None:
    if series is not None and not series.empty:
        data = series.copy()
        data["sparse"] = data["year_month"].isin(SPARSE_MONTHS)
        figure = go.Figure()
        solid = data[~data["sparse"]]
        thin = data[data["sparse"]]
        if not solid.empty:
            figure.add_bar(x=solid["year_month"], y=solid["n_orders_valid"], name="Số đơn", marker_color=NAVY)
        if not thin.empty:
            figure.add_bar(x=thin["year_month"], y=thin["n_orders_valid"], name="Tháng dữ liệu thưa", marker_color="#c5cdd6")
        figure.update_layout(height=320, barmode="overlay")
        figure.update_xaxes(title="Tháng")
        figure.update_yaxes(title="Số đơn", **count_axis_ticks(data["n_orders_valid"]))
        st.plotly_chart(
            style_fig(
                figure,
                "Tháng nào có ít đơn hợp lệ?",
                scope_subtitle(include_months=True, include_funnel=True),
            ),
            width="stretch",
        )
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
