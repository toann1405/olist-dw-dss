"""Shared presentation helpers. They do not calculate KPI formulas."""

from __future__ import annotations

from html import escape

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
        "Dự báo của mô hình — tháng tới</span>",
        unsafe_allow_html=True,
    )
    st.caption("Số này là ước tính, không phải đã xảy ra.")


def badge_actual() -> None:
    st.markdown(
        "<span style='background:#e4eeed;color:##e4eeed;padding:2px 8px;border-radius:999px;'>"
        "Số liệu thực tế đã xảy ra</span>",
        unsafe_allow_html=True,
    )


def chart_note(shows: str, how: str) -> None:
    st.caption(f"Biểu đồ này cho thấy {shows} Cách đọc: {how}")


def filter_badge(kind: str, question: str | None = None) -> None:
    if kind == "fixed_spec":
        st.caption(f"Cố định theo câu hỏi SPEC {question}")
    else:
        st.caption("Áp dụng bộ lọc")


def add_platform_reference(fig: go.Figure, value, yref: str = "y") -> go.Figure:
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
        yref=yref,
    )
    add_legend_swatch(fig, "Trung bình toàn sàn", NAVY, dash="dash")
    return fig


def add_vertical_platform_reference(fig: go.Figure, value) -> go.Figure:
    """Vertical platform line for a horizontal bar. add_platform_reference stays on add_hline."""
    if value is None:
        return fig
    try:
        if pd.isna(value):
            return fig
    except TypeError:
        return fig
    fig.add_vline(
        x=float(value),
        line_dash="dash",
        line_color=NAVY,
        annotation_text="Trung bình toàn sàn",
        annotation_position="top",
    )
    add_legend_swatch(fig, "Trung bình toàn sàn", NAVY, dash="dash")
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


def button_dropdown(
    label: str,
    options,
    key: str,
    *,
    disabled: bool = False,
    format_func=None,
    index: int | None = None,
    container=None,
):
    """A button that opens a list of choices. Replaces st.selectbox."""
    host = container if container is not None else st
    choices = list(options)
    if not choices:
        host.caption(label)
        return None
    name = format_func if format_func is not None else (lambda value: str(value))
    if key not in st.session_state:
        start = 0 if index is None else int(index)
        if start < 0 or start >= len(choices):
            start = 0
        st.session_state[key] = choices[start]
    if st.session_state.get(key) not in choices:
        start = 0 if index is None else int(index)
        if start < 0 or start >= len(choices):
            start = 0
        st.session_state[key] = choices[start]
    current = st.session_state[key]
    shown = f"{name(current)} ▾"
    host.caption(label)
    if disabled:
        host.button(shown, key=f"{key}__locked", disabled=True, width="stretch")
        return current
    with host.popover(shown, width="stretch"):
        for position, option in enumerate(choices):
            kind = "primary" if option == current else "secondary"
            if host.button(
                name(option),
                key=f"{key}__opt_{position}",
                type=kind,
                width="stretch",
            ):
                st.session_state[key] = option
                st.rerun()
    return st.session_state[key]


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


def small_n_label() -> str:
    """Legend text for a faded mark. Reads MIN_N_DISPLAY so the cutoff is not copied."""
    return f"Mẫu nhỏ (n < {MIN_N_DISPLAY})"


def add_legend_swatch(
    fig: go.Figure,
    name: str,
    color: str,
    opacity: float = 1.0,
    dash: str | None = None,
) -> go.Figure:
    """Legend entry for a color, size, opacity, or reference line. Not a data series."""
    if dash:
        trace = go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            name=name,
            line=dict(color=color, dash=dash, width=2),
            showlegend=True,
            hoverinfo="skip",
        )
    else:
        trace = go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            name=name,
            marker=dict(color=color, opacity=opacity, size=11, symbol="square"),
            showlegend=True,
            hoverinfo="skip",
        )
    fig.add_trace(trace)
    return fig


def scope_subtitle(
    *,
    include_year: bool = True,
    include_region: bool = True,
    include_state: bool = True,
    include_category: bool = False,
    include_months: bool = False,
    include_funnel: bool = False,
    extra: str | None = None,
) -> str:
    """Period and filters actually in effect, for chart subtitles."""
    year, region, state, category = filters()
    parts: list[str] = []
    if include_year:
        parts.append(f"Năm {year if year is not None else 'tất cả'}")
    if include_region:
        parts.append(f"vùng {region or 'tất cả'}")
    if include_state:
        parts.append(f"bang {state or 'tất cả'}")
    if include_category and category:
        parts.append(f"nhóm {category}")
    if include_months:
        start = st.session_state.get("filter_month_from", ALL)
        end = st.session_state.get("filter_month_to", ALL)
        if st.session_state.get("kpi_dense"):
            parts.append("chỉ giai đoạn đủ dữ liệu")
        elif start not in (None, ALL) or end not in (None, ALL):
            left = start if start not in (None, ALL) else "đầu kỳ"
            right = end if end not in (None, ALL) else "cuối kỳ"
            parts.append(f"tháng {left} → {right}")
        else:
            parts.append("mọi tháng")
    if include_funnel:
        funnel = st.session_state.get("filter_funnel", ALL)
        if funnel not in (None, ALL):
            parts.append(str(funnel))
    if extra:
        parts.append(extra)
    return " · ".join(parts)


def _axis_title_text(axis) -> str:
    title = getattr(axis, "title", None)
    if title is None or title.text is None:
        return ""
    return str(title.text)


def _percent_if_needed(colorbar) -> None:
    if colorbar is None:
        return
    title = getattr(colorbar, "title", None)
    text = ""
    if title is not None and getattr(title, "text", None):
        text = str(title.text)
    if "%" in text:
        colorbar.tickformat = ".0%"


def _enforce_percent_axes(fig: go.Figure) -> None:
    def _fix(axis) -> None:
        if "%" in _axis_title_text(axis):
            axis.tickformat = ".0%"

    fig.for_each_xaxis(_fix)
    fig.for_each_yaxis(_fix)
    for trace in fig.data:
        _percent_if_needed(getattr(trace, "colorbar", None))
        marker = getattr(trace, "marker", None)
        if marker is not None:
            _percent_if_needed(getattr(marker, "colorbar", None))
    coloraxis = getattr(fig.layout, "coloraxis", None)
    if coloraxis is not None:
        _percent_if_needed(getattr(coloraxis, "colorbar", None))


def style_fig(
    fig: go.Figure,
    title: str,
    subtitle: str | None = None,
    legend: bool = True,
    legend_side: str = "top",
) -> go.Figure:
    """Question title, period subtitle, and legend on the olist theme.

    Callers pass the sentence the chart answers and the filters in effect.
    Do not set title, legend, or margin after this returns. Axis units stay
    on the axes. legend_side "top" keeps the legend above the plot.
    "right" puts it in the right margin so a long category axis does not cover it.
    """
    height = fig.layout.height
    apply_theme(fig, height=int(height) if height else 360)
    top = 88
    if subtitle:
        top += 36
    on_right = legend and legend_side == "right"
    if legend and not on_right:
        top += 12
    question = f"<b>{escape(title)}</b>"
    if subtitle:
        question += (
            "<br><span style='font-size:12px;font-weight:400'>"
            f"{escape(subtitle)}</span>"
        )
    if on_right:
        legend_layout = dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            xref="paper",
            yref="paper",
        )
    else:
        legend_layout = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        )
    fig.update_layout(
        title=dict(
            text=question,
            x=0,
            xanchor="left",
            y=0.90,
            yanchor="top",
            yref="container",
            font=dict(size=16, color=INK),
        ),
        showlegend=legend,
        legend=legend_layout,
        margin_t=top,
    )
    if on_right:
        fig.update_layout(margin_r=168)
    _enforce_percent_axes(fig)
    return fig
