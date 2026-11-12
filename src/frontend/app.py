"""One Streamlit app for the KPI dashboard, OLAP explorer, and DSS."""

from __future__ import annotations

import sys
from pathlib import Path

FRONT = Path(__file__).resolve().parent
ROOT = FRONT.parents[1]
for path in (str(ROOT), str(FRONT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import streamlit as st

from lib import db, queries
from lib.stats import DENSE_FROM, DENSE_TO
from lib.ui import ALL, NAVY, default_filters, filters
from pages import home, kpi, method, olap, policy, seller_risk


def _labels(frame, column: str) -> list[str]:
    return [ALL] + frame[column].dropna().astype(str).tolist()


def _keep(key: str, options: list[str]) -> None:
    if st.session_state.get(key) not in options:
        st.session_state[key] = ALL


def _select_months(start: str, end: str) -> None:
    st.session_state["filter_month_from"] = start
    st.session_state["filter_month_to"] = end


def _month_presets(months: list[str]) -> dict[str, tuple[str, str]]:
    """Named ranges. A year preset uses the first and last month that has orders."""
    presets: dict[str, tuple[str, str]] = {}
    if DENSE_FROM in months and DENSE_TO in months:
        presets["Đủ dữ liệu"] = (DENSE_FROM, DENSE_TO)
    for year in ("2017", "2018"):
        chosen = [item for item in months if item.startswith(f"{year}-")]
        if chosen:
            presets[year] = (chosen[0], chosen[-1])
    if months:
        presets["Toàn bộ"] = (months[0], months[-1])
    return presets


def _dropdown(host, label: str, options: list[str], key: str, disabled: bool) -> None:
    """Native select. The sidebar used to open each filter as a button list."""
    if not options:
        host.caption(label)
        return
    host.selectbox(label, options, key=key, disabled=disabled)


def _blank(value) -> str | None:
    if value in (None, ALL):
        return None
    return str(value)


def _applied_from_widgets() -> dict:
    return {
        "month_from": _blank(st.session_state.get("filter_month_from")),
        "month_to": _blank(st.session_state.get("filter_month_to")),
        "region": _blank(st.session_state.get("filter_region")),
        "state": _blank(st.session_state.get("filter_state")),
        "category": _blank(st.session_state.get("filter_category")),
        "funnel": _blank(st.session_state.get("filter_funnel")),
    }


def _reset_filters() -> None:
    fresh = default_filters()
    st.session_state["applied_filters"] = fresh
    st.session_state["filter_month_from"] = fresh["month_from"]
    st.session_state["filter_month_to"] = fresh["month_to"]
    st.session_state["filter_region"] = ALL
    st.session_state["filter_state"] = ALL
    st.session_state["filter_category"] = ALL
    st.session_state["filter_funnel"] = ALL


def _applied_caption(chosen: dict) -> str:
    funnel = chosen.get("funnel") or "tất cả"
    return (
        f"Đang áp dụng: {chosen.get('month_from') or 'đầu'} → {chosen.get('month_to') or 'cuối'} · "
        f"vùng {chosen.get('region') or 'tất cả'} · bang {chosen.get('state') or 'tất cả'} · "
        f"nhóm {chosen.get('category') or 'tất cả'} · funnel {funnel}"
    )


def render_sidebar() -> None:
    pending_state = st.session_state.pop("pending_filter_state", None)
    if pending_state:
        st.session_state["filter_region"] = ALL
        st.session_state["filter_state"] = str(pending_state)
        applied = dict(filters())
        applied["region"] = None
        applied["state"] = str(pending_state)
        st.session_state["applied_filters"] = applied
    st.sidebar.markdown(
        f"<div style='font-size:20px;font-weight:700;color:{NAVY};line-height:1.2;'>Olist<br>Seller Performance</div>",
        unsafe_allow_html=True,
    )
    filters_off = False
    try:
        path = str(st.context.url).rstrip("/")
        filters_off = path.endswith(("/olap", "/risk", "/policy", "/method"))
    except Exception:
        filters_off = False
    if filters_off:
        st.sidebar.caption("Trang này không dùng bộ lọc.")
    try:
        regions = _labels(db.query(*queries.regions()), "region_name")
        _keep("filter_region", regions)
        months = db.query(*queries.months())["year_month"].dropna().astype(str).tolist()
        presets = _month_presets(months)
        default = presets.get("Đủ dữ liệu") or presets.get("Toàn bộ")
        if default:
            if st.session_state.get("filter_month_from") not in months:
                st.session_state["filter_month_from"] = default[0]
            if st.session_state.get("filter_month_to") not in months:
                st.session_state["filter_month_to"] = default[1]
        st.sidebar.caption("Khoảng thời gian")
        grid = (st.sidebar.columns(2), st.sidebar.columns(2))
        slots = (grid[0][0], grid[0][1], grid[1][0], grid[1][1])
        for slot, name in zip(slots, ("Đủ dữ liệu", "2017", "2018", "Toàn bộ")):
            bounds = presets.get(name)
            active = (
                bounds is not None
                and st.session_state.get("filter_month_from") == bounds[0]
                and st.session_state.get("filter_month_to") == bounds[1]
            )
            button_args = {}
            if bounds is not None:
                button_args["on_click"] = _select_months
                button_args["args"] = bounds
            slot.button(
                name,
                key=f"preset_{name}",
                disabled=filters_off or bounds is None,
                type="primary" if active else "secondary",
                width="stretch",
                **button_args,
            )
        with st.sidebar.form("global_filters"):
            _dropdown(st, "Từ tháng", months, "filter_month_from", filters_off)
            _dropdown(st, "Đến tháng", months, "filter_month_to", filters_off)
            _dropdown(st, "Vùng seller", regions, "filter_region", filters_off)
            region = _blank(st.session_state.get("filter_region", ALL))
            states = _labels(db.query(*queries.states(region)), "state_code")
            categories = _labels(queries.category_groups(), "category_group")
            _keep("filter_state", states)
            _keep("filter_category", categories)
            _dropdown(st, "Bang seller", states, "filter_state", filters_off)
            _dropdown(st, "Nhóm danh mục", categories, "filter_category", filters_off)
            funnel_options = ["Tất cả", "Có closed deal", "Không có closed deal"]
            _keep("filter_funnel", funnel_options)
            _dropdown(st, "Funnel", funnel_options, "filter_funnel", filters_off)
            submitted = st.form_submit_button(
                "Áp dụng",
                type="primary",
                use_container_width=True,
                disabled=filters_off,
            )
        if submitted:
            st.session_state["applied_filters"] = _applied_from_widgets()
        st.sidebar.button(
            "Đặt lại",
            on_click=_reset_filters,
            use_container_width=True,
            disabled=filters_off,
        )
        st.sidebar.caption(_applied_caption(filters()))
    except Exception as exc:
        st.sidebar.error(db.redact(exc))


def main() -> None:
    st.set_page_config(layout="wide", page_title="Olist Seller Performance", page_icon=":material/storefront:")
    render_sidebar()
    pages = {
        "home": st.Page(home.render, title="Giới thiệu", icon=":material/home:", url_path="home", default=True),
        "kpi": st.Page(
            kpi.render,
            title="Tổng quan kinh doanh",
            icon=":material/monitoring:",
            url_path="kpi",
        ),
        "olap": st.Page(
            olap.render,
            title="Phân tích đa chiều",
            icon=":material/account_tree:",
            url_path="olap",
        ),
        "risk": st.Page(
            seller_risk.render,
            title="Cảnh báo seller",
            icon=":material/warning:",
            url_path="risk",
        ),
        "policy": st.Page(
            policy.render,
            title="Chọn chính sách",
            icon=":material/rule:",
            url_path="policy",
        ),
        "method": st.Page(
            method.render,
            title="Dữ liệu & phương pháp",
            icon=":material/menu_book:",
            url_path="method",
        ),
    }
    st.session_state["nav_pages"] = pages
    if hasattr(st, "navigation"):
        st.navigation(
            [
                pages["home"],
                pages["kpi"],
                pages["olap"],
                pages["risk"],
                pages["policy"],
                pages["method"],
            ]
        ).run()
        return
    choice = st.sidebar.radio("Trang", ("home", "kpi", "olap", "risk", "policy", "method"))
    {
        "home": home,
        "kpi": kpi,
        "olap": olap,
        "risk": seller_risk,
        "policy": policy,
        "method": method,
    }[choice].render()


if __name__ == "__main__":
    main()
