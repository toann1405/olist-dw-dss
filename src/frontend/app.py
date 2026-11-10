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

from pages import kpi, olap, policy, seller_risk


def main() -> None:
    st.set_page_config(page_title="Olist seller performance", layout="wide")
    pages = [
        st.Page(kpi.render, title="Tổng quan KPI", url_path="kpi", default=True),
        st.Page(olap.render, title="OLAP Explorer", url_path="olap"),
        st.Page(seller_risk.render, title="Seller risk", url_path="risk"),
        st.Page(policy.render, title="Policy scenario", url_path="policy"),
    ]
    if hasattr(st, "navigation"):
        st.navigation(pages).run()
        return
    choice = st.sidebar.radio(
        "Trang",
        ("Tổng quan KPI", "OLAP Explorer", "Seller risk", "Policy scenario"),
    )
    if choice == "Tổng quan KPI":
        kpi.render()
    elif choice == "OLAP Explorer":
        olap.render()
    elif choice == "Seller risk":
        seller_risk.render()
    else:
        policy.render()


if __name__ == "__main__":
    main()
