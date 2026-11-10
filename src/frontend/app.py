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
from pages import home, kpi, olap, policy, seller_risk


def _labels(frame, column: str) -> list[str]:
    return [ALL] + frame[column].dropna().astype(str).tolist()


def _keep(key: str, options: list[str]) -> None:
    if st.session_state.get(key) not in options:
        st.session_state[key] = ALL


def render_sidebar() -> None:
    st.sidebar.markdown(
        f"<div style='font-size:20px;font-weight:700;color:{NAVY};line-height:1.2;'>Olist<br>Seller Performance</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Dashboard và DSS trên Gold")
    try:
        years = _labels(db.query(*queries.years()), "year")
        years = [ALL] + [str(int(float(value))) for value in years if value != ALL]
        regions = _labels(db.query(*queries.regions()), "region_name")
        _keep("filter_year", years)
        _keep("filter_region", regions)
        st.sidebar.selectbox("Năm mua", years, key="filter_year")
        st.sidebar.selectbox("Vùng seller", regions, key="filter_region")
        region = None if st.session_state["filter_region"] == ALL else st.session_state["filter_region"]
        states = _labels(db.query(*queries.states(region)), "state_code")
        categories = _labels(queries.category_groups(), "category_group")
        _keep("filter_state", states)
        _keep("filter_category", categories)
        st.sidebar.selectbox("Bang seller", states, key="filter_state")
        st.sidebar.selectbox("Nhóm danh mục", categories, key="filter_category")
    except Exception as exc:
        st.sidebar.error(db.redact(exc))
    st.sidebar.caption("Member −1 không nằm trong các danh sách này.")


def main() -> None:
    st.set_page_config(layout="wide", page_title="Olist Seller Performance", page_icon=":material/storefront:")
    render_sidebar()
    pages = {
        "home": st.Page(home.render, title="Home", icon=":material/home:", url_path="home", default=True),
        "kpi": st.Page(kpi.render, title="Tổng quan KPI", icon=":material/monitoring:", url_path="kpi"),
        "olap": st.Page(olap.render, title="OLAP Explorer", icon=":material/account_tree:", url_path="olap"),
        "risk": st.Page(seller_risk.render, title="Seller risk", icon=":material/warning:", url_path="risk"),
        "policy": st.Page(policy.render, title="Policy scenario", icon=":material/rule:", url_path="policy"),
    }
    st.session_state["nav_pages"] = pages
    if hasattr(st, "navigation"):
        st.navigation(list(pages.values())).run()
        return
    choice = st.sidebar.radio("Trang", ("home", "kpi", "olap", "risk", "policy"))
    {"home": home, "kpi": kpi, "olap": olap, "risk": seller_risk, "policy": policy}[choice].render()


if __name__ == "__main__":
    main()
