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
from lib.ui import ALL, NAVY
from pages import home, kpi, method, olap, policy, seller_risk


def _labels(frame, column: str) -> list[str]:
    return [ALL] + frame[column].dropna().astype(str).tolist()


def _keep(key: str, options: list[str]) -> None:
    if st.session_state.get(key) not in options:
        st.session_state[key] = ALL


def _dropdown(label: str, options: list[str], key: str, disabled: bool) -> None:
    """Native select. The sidebar used to open each filter as a button list."""
    if not options:
        st.sidebar.caption(label)
        return
    st.sidebar.selectbox(label, options, key=key, disabled=disabled)


def render_sidebar() -> None:
    pending_state = st.session_state.pop("pending_filter_state", None)
    if pending_state:
        st.session_state["filter_region"] = ALL
        st.session_state["filter_state"] = str(pending_state)
    st.sidebar.markdown(
        f"<div style='font-size:20px;font-weight:700;color:{NAVY};line-height:1.2;'>Olist<br>Seller Performance</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Đọc 1 → 4 mỗi tháng. Trang cuối là phương pháp.")
    filters_off = False
    try:
        path = str(st.context.url).rstrip("/")
        filters_off = path.endswith(("/olap", "/risk", "/policy", "/method"))
    except Exception:
        filters_off = False
    if filters_off:
        st.sidebar.caption("Trang này không dùng bộ lọc.")
    try:
        years = _labels(db.query(*queries.years()), "year")
        years = [ALL] + [str(int(float(value))) for value in years if value != ALL]
        regions = _labels(db.query(*queries.regions()), "region_name")
        _keep("filter_year", years)
        _keep("filter_region", regions)
        _dropdown("Năm mua", years, "filter_year", filters_off)
        _dropdown("Vùng seller", regions, "filter_region", filters_off)
        region = None if st.session_state["filter_region"] == ALL else st.session_state["filter_region"]
        states = _labels(db.query(*queries.states(region)), "state_code")
        categories = _labels(queries.category_groups(), "category_group")
        _keep("filter_state", states)
        _keep("filter_category", categories)
        _dropdown("Bang seller", states, "filter_state", filters_off)
        _dropdown("Nhóm danh mục", categories, "filter_category", filters_off)
        months = _labels(db.query(*queries.months()), "year_month")
        _keep("filter_month_from", months)
        _keep("filter_month_to", months)
        _dropdown("Từ tháng", months, "filter_month_from", filters_off)
        _dropdown("Đến tháng", months, "filter_month_to", filters_off)
        funnel_options = ["Tất cả", "Có closed deal", "Không có closed deal"]
        _keep("filter_funnel", funnel_options)
        _dropdown("Funnel", funnel_options, "filter_funnel", filters_off)
    except Exception as exc:
        st.sidebar.error(db.redact(exc))


def main() -> None:
    st.set_page_config(layout="wide", page_title="Olist Seller Performance", page_icon=":material/storefront:")
    render_sidebar()
    pages = {
        "home": st.Page(home.render, title="Giới thiệu", icon=":material/home:", url_path="home", default=True),
        "kpi": st.Page(
            kpi.render,
            title="1. Sức khỏe marketplace",
            icon=":material/monitoring:",
            url_path="kpi",
        ),
        "olap": st.Page(
            olap.render,
            title="2. GMV và trải nghiệm xấu từ đâu",
            icon=":material/account_tree:",
            url_path="olap",
        ),
        "risk": st.Page(
            seller_risk.render,
            title="3. Seller nào đáng lo",
            icon=":material/warning:",
            url_path="risk",
        ),
        "policy": st.Page(
            policy.render,
            title="4. Chọn chính sách nào",
            icon=":material/rule:",
            url_path="policy",
        ),
        "method": st.Page(
            method.render,
            title="5. Dữ liệu & phương pháp",
            icon=":material/menu_book:",
            url_path="method",
        ),
    }
    st.session_state["nav_pages"] = pages
    if hasattr(st, "navigation"):
        st.navigation(
            {
                "Hàng tháng": [pages["home"], pages["kpi"], pages["olap"], pages["risk"], pages["policy"]],
                "Tham khảo": [pages["method"]],
            }
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
