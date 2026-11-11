"""M1 screen. Reads dss.seller_risk_score and does not rescore sellers."""

from __future__ import annotations

import streamlit as st

from lib import db, queries
from lib.glossary import explain
from lib.insights import build_insight_risk
from lib.labels import COLUMN_LABELS, RATIO_COLUMNS, fmt_ratio
from lib.ui import insight_box, next_step, page_header
from src.dss.params import MIN_ORDERS


def render(settings=None) -> None:
    del settings
    page_header(
        "Seller nào đáng lo nhất?",
        "Điểm M1 của tháng chấm gần nhất. Bộ lọc sidebar không đổi bảng điểm.",
        "Seller risk – M1",
    )
    min_orders = st.number_input(
        "min_orders",
        min_value=0,
        value=MIN_ORDERS,
        step=1,
        help=explain("risk_score"),
    )
    try:
        with st.spinner("Đang tải dữ liệu…"):
            frame = db.query(*queries.risk_scores(int(min_orders)))
    except Exception as exc:
        db.show_warehouse_error(exc)
        next_step("risk")
        return
    if frame.empty:
        st.info("Chưa có điểm rủi ro cho kỳ này, hãy liên hệ nhóm dữ liệu.")
        next_step("risk")
        return
    insight_box(build_insight_risk(frame, int(min_orders)))
    show = frame.copy()
    for column in RATIO_COLUMNS:
        if column in show.columns:
            show[column] = show[column].map(fmt_ratio)
    st.dataframe(show.rename(columns=COLUMN_LABELS), width="stretch", hide_index=True)
    seller_id = st.selectbox("Seller", frame["seller_id"].astype(str).tolist())
    try:
        profile = db.query(*queries.seller_profile(seller_id))
    except Exception as exc:
        db.show_warehouse_error(exc)
        next_step("risk")
        return
    st.subheader("Hồ sơ")
    st.dataframe(profile, width="stretch")
    next_step("risk")
