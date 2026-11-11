"""Shared presentation helpers. They do not calculate KPI formulas."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from lib import db

NAVY = "#1f3a5f"
LATE = "#d9622b"
REVIEW = "#1b7f79"
NEUTRAL = "#8a93a0"
INK = "#1c2b33"
ALL = "Tất cả"

pio.templates["olist"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Segoe UI, Helvetica, Arial, sans-serif", color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=28, b=8),
        colorway=[NAVY, LATE, REVIEW, NEUTRAL],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(bgcolor="white", font=dict(color=INK)),
        xaxis=dict(showgrid=False, zeroline=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor="#ece7df", zeroline=False, showline=False),
    )
)


def _missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def fmt_brl(value) -> str:
    """Reais. Millions use 'tr'. Thousands separators follow Vietnamese style."""
    if _missing(value):
        return "—"
    amount = float(value)
    sign = "−" if amount < 0 else ""
    amount = abs(amount)
    if amount >= 1_000_000:
        scaled = f"{amount / 1_000_000:,.2f}"
        scaled = scaled.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{sign}R$ {scaled} tr"
    text = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}R$ {text}"


def fmt_pct(value) -> str:
    """A ratio in 0–1 becomes one decimal percent."""
    if _missing(value):
        return "—"
    text = f"{abs(float(value)) * 100:,.1f}"
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "−" if float(value) < 0 else ""
    return f"{sign}{text}%"


def fmt_int(value) -> str:
    if _missing(value):
        return "—"
    text = f"{int(round(float(value))):,}"
    return text.replace(",", ".")


def signed_pct(change) -> str | None:
    if _missing(change):
        return None
    number = float(change)
    if number == 0:
        return "0,0%"
    sign = "+" if number > 0 else "−"
    return sign + fmt_pct(abs(number))


def signed_points(current, previous) -> str | None:
    """Difference of two ratios, shown in percentage points."""
    if _missing(current) or _missing(previous):
        return None
    diff = float(current) - float(previous)
    if diff == 0:
        return "0,0 điểm"
    sign = "+" if diff > 0 else "−"
    body = fmt_pct(abs(diff)).replace("%", " điểm")
    return sign + body


def page_header(title_question: str, subtitle: str, tech_name: str) -> None:
    text, action = st.columns([5, 1], vertical_alignment="center", gap="medium")
    with text:
        st.markdown(f"### {title_question}")
        st.caption(tech_name)
        if subtitle:
            st.write(subtitle)
    with action:
        db.refresh_button(tech_name)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


MIN_N_DISPLAY = 30


def badge_predicted() -> None:
    st.markdown(
        "<span style='background:#ede9fe;color:#6d28d9;padding:2px 8px;border-radius:999px;'>"
        "🔮 Dự báo của mô hình — tháng tới</span>",
        unsafe_allow_html=True,
    )
    st.caption("Số này là ước tính, không phải đã xảy ra.")


def badge_actual() -> None:
    st.markdown(
        "<span style='background:#f3f4f6;color:#374151;padding:2px 8px;border-radius:999px;'>"
        "📊 Số liệu thực tế đã xảy ra</span>",
        unsafe_allow_html=True,
    )


def chart_note(shows: str, how: str) -> None:
    st.caption(f"Biểu đồ này cho thấy {shows} Cách đọc: {how}")


def filter_badge(kind: str, question: str | None = None) -> None:
    if kind == "fixed_spec":
        st.caption(f"Cố định theo câu hỏi SPEC {question}")
    else:
        st.caption("Áp dụng bộ lọc")


def add_platform_reference(fig: go.Figure, value) -> go.Figure:
    """Dashed line for the platform rate. value is a ratio on 0–1."""
    if value is None:
        return fig
    try:
        if pd.isna(value):
            return fig
    except TypeError:
        return fig
    fig.add_hline(
        y=float(value),
        line_dash="dash",
        line_color=NAVY,
        annotation_text="Trung bình toàn sàn",
        annotation_position="top left",
    )
    return fig


def point_opacity(samples) -> list[float]:
    output = []
    for sample in samples:
        try:
            small = sample is None or pd.isna(sample) or float(sample) < MIN_N_DISPLAY
        except TypeError:
            small = True
        output.append(0.3 if small else 1.0)
    return output


def insight_box(text: str) -> None:
    st.info(text)


def next_step(current: str) -> None:
    order = ("home", "kpi", "olap", "risk", "policy")
    if current not in order:
        return
    pages = st.session_state.get("nav_pages", {})
    target_key = order[(order.index(current) + 1) % len(order)]
    target = pages.get(target_key)
    if target is None:
        return
    if st.button("Bước tiếp theo →", key=f"next_{current}"):
        st.switch_page(target)


def kpi_card(label: str, value: str, delta: str | None = None, help_text: str | None = None, delta_color: str = "normal") -> None:
    with st.container(border=True):
        st.metric(label, value, delta=delta, delta_color=delta_color, help=help_text)


def chip(label: str, value: str) -> None:
    """One compact fact. Not a KPI formula."""
    with st.container(border=True):
        st.caption(label)
        st.markdown(f"**{value}**")


def filters() -> tuple[int | None, str | None, str | None, str | None]:
    """Sidebar choices. 'Tất cả' is None. Year is an int when set."""
    year_label = st.session_state.get("filter_year", ALL)
    region = st.session_state.get("filter_region", ALL)
    state = st.session_state.get("filter_state", ALL)
    category = st.session_state.get("filter_category", ALL)
    year = None if year_label in (None, ALL) else int(year_label)
    region = None if region in (None, ALL) else str(region)
    state = None if state in (None, ALL) else str(state)
    category = None if category in (None, ALL) else str(category)
    return year, region, state, category


def apply_theme(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(template="olist", height=height)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#ece7df")
    return fig


def highlight_colors(values: list[float], accent: str = LATE) -> list[str]:
    if not values:
        return []
    peak = max(values)
    return [accent if value == peak else NEUTRAL for value in values]
