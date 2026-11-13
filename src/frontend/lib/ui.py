"""Shared presentation helpers. They do not calculate KPI formulas."""

from __future__ import annotations

from html import escape
import math

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
CREAM = "#FAF6EE"
SIDEBAR_NAVY = "#1F2A44"
BORDER = "#E8DFCC"
ALL = "Tất cả"

# Navy sidebar, cream type. Tokens match src/frontend/.streamlit/config.toml.
_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] {
  background-color: #1F2A44;
  color: #F3EBDD;
}
[data-testid="stSidebar"] * {
  color: #F3EBDD !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *,
[data-testid="stSidebar"] small {
  color: #C9BFAE !important;
  opacity: 1 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
  color: #F3EBDD !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span {
  color: inherit !important;
  opacity: 1 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-baseweb="base-input"] {
  background-color: #FFFDF8 !important;
  border-color: #5A6684 !important;
  color: #1E2533 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div *,
[data-testid="stSidebar"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-baseweb="select"] svg,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="base-input"] input {
  color: #1E2533 !important;
  -webkit-text-fill-color: #1E2533 !important;
  caret-color: #1E2533 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"][aria-disabled="true"] > div *,
[data-testid="stSidebar"] [data-baseweb="select"] [aria-disabled="true"] *,
[data-testid="stSidebar"] input:disabled {
  color: #5A6684 !important;
  -webkit-text-fill-color: #5A6684 !important;
}
[data-testid="stSidebar"] input::placeholder {
  color: #5A6684 !important;
  opacity: 1 !important;
}
[data-baseweb="popover"]:has([role="listbox"]) > div,
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"],
[data-baseweb="popover"] [data-testid="stSelectboxVirtualDropdown"] > div,
[data-baseweb="popover"] [role="option"] {
  background-color: #FFFDF8 !important;
  color: #1E2533 !important;
}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"] {
  background-color: #E8DFCC !important;
  color: #1E2533 !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] *,
[data-baseweb="popover"] [role="listbox"] *,
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] * {
  color: #1E2533 !important;
}
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] button[kind="primaryFormSubmit"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primaryFormSubmit"] {
  background-color: #8FA3C7 !important;
  border-color: #8FA3C7 !important;
  color: #1F2A44 !important;
}
[data-testid="stSidebar"] button[kind="primary"] *,
[data-testid="stSidebar"] button[kind="primary"] p,
[data-testid="stSidebar"] button[kind="primaryFormSubmit"] *,
[data-testid="stSidebar"] button[kind="primaryFormSubmit"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-primaryFormSubmit"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-primaryFormSubmit"] p {
  color: #1F2A44 !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover,
[data-testid="stSidebar"] button[kind="primaryFormSubmit"]:hover,
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover,
[data-testid="stSidebar"] [data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background-color: #A9B8D6 !important;
  border-color: #A9B8D6 !important;
}
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] button[kind="secondaryFormSubmit"],
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-secondaryFormSubmit"] {
  background-color: transparent !important;
  border-color: #5A6684 !important;
  color: #F3EBDD !important;
}
[data-testid="stSidebar"] button[kind="secondary"] *,
[data-testid="stSidebar"] button[kind="secondary"] p,
[data-testid="stSidebar"] button[kind="secondaryFormSubmit"] *,
[data-testid="stSidebar"] button[kind="secondaryFormSubmit"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondaryFormSubmit"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondaryFormSubmit"] p {
  color: #F3EBDD !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover,
[data-testid="stSidebar"] button[kind="secondaryFormSubmit"]:hover,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover,
[data-testid="stSidebar"] [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
  background-color: #2E3B5C !important;
  border-color: #8FA3C7 !important;
}
[data-testid="stSidebar"] button:disabled {
  opacity: 0.55 !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label,
[data-testid="stSidebar"] [data-testid="stCheckbox"] label p,
[data-testid="stSidebar"] [data-testid="stCheckbox"] label span {
  color: #F3EBDD !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input[role="switch"]) > div:first-of-type {
  background-color: #5A6684 !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input[role="switch"]:checked) > div:first-of-type {
  background-color: #8FA3C7 !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input[role="switch"]) > div:first-of-type > div {
  background-color: #F3EBDD !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"]:not(:has(input[role="switch"])) > span:first-of-type {
  background-color: #5A6684 !important;
  border-color: #5A6684 !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:not([role="switch"]):checked) > span:first-of-type {
  background-color: #8FA3C7 !important;
  border-color: #8FA3C7 !important;
}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-checked="true"],
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-pressed="true"],
[data-testid="stSidebar"] [data-testid="stBaseButton-segmented_controlActive"],
[data-testid="stSidebar"] [data-testid="stBaseButton-pillsActive"] {
  background-color: #8FA3C7 !important;
  border-color: #8FA3C7 !important;
  color: #1F2A44 !important;
}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-checked="true"] *,
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[aria-pressed="true"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-segmented_controlActive"] *,
[data-testid="stSidebar"] [data-testid="stBaseButton-pillsActive"] * {
  color: #1F2A44 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background-color: #8FA3C7 !important;
  border-radius: 6px;
  padding: 2px 6px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) * {
  color: #1F2A44 !important;
}
</style>
"""


def inject_sidebar_css() -> None:
    """Cream type on the navy sidebar. Main content keeps the light theme."""
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)

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
    sign = "+" if number > 0 else "-"
    return sign + fmt_pct(abs(number))


def signed_points(current, previous) -> str | None:
    """Difference of two ratios, shown in percentage points."""
    if _missing(current) or _missing(previous):
        return None
    diff = float(current) - float(previous)
    if diff == 0:
        return "0,0 điểm"
    sign = "+" if diff > 0 else "-"
    body = fmt_pct(abs(diff)).replace("%", " điểm")
    return sign + body


def page_header(title: str, conclusion: str | None, kind: str | None) -> None:
    """Question, one data conclusion, and a single Thực tế or Dự báo badge."""
    text, action = st.columns([6.1, 1], vertical_alignment="center", gap="small")
    with text:
        badge = ""
        if kind == "actual":
            badge = _badge_html("Thực tế", "#e4eeed", NAVY)
        elif kind == "predicted":
            badge = _badge_html("Dự báo", "#ede9fe", "#6d28d9")
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap'>"
            f"<span style='font-size:28px;font-weight:600;line-height:1.3;color:{INK}'>"
            f"{escape(title)}</span>{badge}</div>",
            unsafe_allow_html=True,
        )
    with action:
        db.refresh_button(title)
    if conclusion:
        st.markdown(f"**{conclusion}**")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


MIN_N_DISPLAY = 30


def _badge_html(text: str, background: str, color: str) -> str:
    return (
        f"<span style='background:{background};color:{color};padding:2px 8px;"
        f"border-radius:999px;font-size:0.85rem;font-weight:600;white-space:nowrap'>"
        f"{escape(text)}</span>"
    )


def _badge(text: str, background: str, color: str) -> None:
    st.markdown(_badge_html(text, background, color), unsafe_allow_html=True)


def badge_predicted() -> None:
    _badge("Dự báo", "#ede9fe", "#6d28d9")


def badge_actual() -> None:
    _badge("Thực tế", "#e4eeed", NAVY)


def chart_card(fig, how_to_read: str | None = None, formula: str | None = None, **kwargs):
    """Draw one chart. The figure is passed through unchanged."""
    kwargs.setdefault("width", "stretch")
    event = st.plotly_chart(fig, **kwargs)
    _chart_aside(how_to_read, formula)
    return event


def _chart_aside(how_to_read: str | None, formula: str | None) -> None:
    if how_to_read and how_to_read.strip():
        st.caption(how_to_read.strip())
    if formula:
        with st.expander("Cách tính"):
            st.write(formula)


def chart_note(shows: str, how: str = "") -> None:
    text = " ".join(part.strip() for part in (shows, how) if part and part.strip())
    _chart_aside(text or None, None)


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
    order = ("home", "kpi", "olap", "risk", "policy", "method")
    if current not in order:
        return
    pages = st.session_state.get("nav_pages", {})
    target_key = order[(order.index(current) + 1) % len(order)]
    target = pages.get(target_key)
    if target is None:
        return
    if st.button("Bước tiếp theo →", key=f"next_{current}"):
        st.switch_page(target)


def kpi_card(
    label: str,
    value: str,
    delta: str | None = None,
    help_text: str | None = None,
    delta_color: str = "normal",
    *,
    border: bool = True,
    help: str | None = None,
) -> None:
    """One metric. border=False when the caller already wraps the card and its chart."""
    text = help if help is not None else help_text
    if border:
        with st.container(border=True):
            st.metric(label, value, delta=delta, delta_color=delta_color, help=text)
        return
    st.metric(label, value, delta=delta, delta_color=delta_color, help=text)


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


def default_filters() -> dict:
    """Filters in effect before the user clicks Áp dụng."""
    from lib.stats import DENSE_FROM, DENSE_TO

    return {
        "month_from": DENSE_FROM,
        "month_to": DENSE_TO,
        "region": None,
        "state": None,
        "category": None,
        "funnel": None,
    }


def filters() -> dict:
    """Applied sidebar filters. Widget edits do not count until Áp dụng."""
    current = st.session_state.get("applied_filters")
    if not isinstance(current, dict):
        current = default_filters()
        st.session_state["applied_filters"] = current
    return current


def apply_theme(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(template="olist", height=height)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#ece7df")
    if getattr(getattr(fig.layout, "yaxis2", None), "overlaying", None):
        fig.layout.yaxis2.showgrid = False
    return fig


def count_axis_ticks(values=None) -> dict:
    """Tick settings (tickformat='d' and integer dtick >= 1) for count axes."""
    peak = 0.0
    if values is not None:
        for item in values:
            try:
                num = float(item)
            except (TypeError, ValueError):
                continue
            if num == num and num > peak:
                peak = num
    if peak <= 8:
        step = 1
    else:
        raw = peak / 5.0
        magnitude = 10 ** int(math.floor(math.log10(raw)))
        residual = raw / magnitude
        if residual <= 1:
            nice = 1
        elif residual <= 2:
            nice = 2
        elif residual <= 5:
            nice = 5
        else:
            nice = 10
        step = max(1, int(nice * magnitude))
    return {"tickformat": "d", "dtick": step}


def highlight_colors(values: list[float], accent: str = LATE) -> list[str]:
    if not values:
        return []
    peak = max(values)
    return [accent if value == peak else NEUTRAL for value in values]


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
    chosen = filters()
    month_from = chosen.get("month_from")
    month_to = chosen.get("month_to")
    region = chosen.get("region")
    state = chosen.get("state")
    category = chosen.get("category")
    parts: list[str] = []
    if include_year or include_months:
        if month_from or month_to:
            left = month_from or "đầu kỳ"
            right = month_to or "cuối kỳ"
            parts.append(f"tháng {left} → {right}")
        else:
            parts.append("mọi tháng")
    if include_region:
        parts.append(f"vùng {region or 'tất cả'}")
    if include_state:
        parts.append(f"bang {state or 'tất cả'}")
    if include_category and category:
        parts.append(f"nhóm {category}")
    if include_funnel:
        funnel = chosen.get("funnel")
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


_COUNT_AXIS_PREFIXES = (
    "Số đơn",
    "Số seller",
    "Số sự kiện",
)


def _enforce_count_axes(fig: go.Figure) -> None:
    def _fix(axis) -> None:
        text = _axis_title_text(axis)
        if text.startswith(_COUNT_AXIS_PREFIXES) and "%" not in text:
            axis.tickformat = "d"
            current = getattr(axis, "dtick", None)
            try:
                step = int(math.ceil(float(current))) if current is not None else 1
            except (TypeError, ValueError):
                step = 1
            axis.dtick = max(1, step)

    fig.for_each_xaxis(_fix)
    fig.for_each_yaxis(_fix)


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
    _enforce_count_axes(fig)
    return fig
