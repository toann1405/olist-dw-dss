"""M1 screen. Reads dss.seller_risk_score and does not rescore sellers."""

from __future__ import annotations

import streamlit as st

from lib import db, queries
from src.dss.params import MIN_ORDERS


def render(settings=None) -> None:
    del settings
    st.header("Seller risk")
    st.caption("Điểm lấy từ lần chạy job DSS gần nhất. Lọc min_orders chỉ đổi bảng trên trang này.")
    db.refresh_button("risk")
    min_orders = st.number_input("min_orders", min_value=0, value=MIN_ORDERS, step=1)
    try:
        with st.spinner("Đang hỏi SQL Warehouse..."):
            frame = db.query(*queries.risk_scores(int(min_orders)))
    except Exception as exc:
        db.show_warehouse_error(exc)
        return
    if frame.empty:
        st.info("Bảng điểm chưa có dòng. Chạy notebook src/dss/dss_job.py trên workspace trước.")
        return
    st.dataframe(frame, width="stretch")
    seller_id = st.selectbox("Seller", frame["seller_id"].astype(str).tolist())
    try:
        profile = db.query(*queries.seller_profile(seller_id))
    except Exception as exc:
        db.show_warehouse_error(exc)
        return
    st.subheader("Hồ sơ")
    st.dataframe(profile, width="stretch")
