"""Landing page. No warehouse query."""

from __future__ import annotations

import streamlit as st

from lib.ui import NAVY, page_header


def render(settings=None) -> None:
    del settings
    page_header(
        "Olist Seller Performance",
        "Chọn chính sách seller nào để giảm đơn trải nghiệm xấu mà không đụng quá 10% GMV?",
        "home",
    )
    st.write(
        "Mỗi tháng, trưởng bộ phận chất lượng seller chọn một cách phân hạng: "
        "không can thiệp, ngưỡng KPI cố định, hoặc điểm rủi ro dự báo. "
        "Ràng buộc đã khóa: GMV bị ảnh hưởng tối đa 10%, và không xử lý quá 40 seller."
    )
    left, right = st.columns(2)
    with left:
        st.markdown(
            f"""
            <div style="border:1px solid #e4ddd2;border-radius:12px;padding:16px 18px;">
              <div style="color:{NAVY};font-weight:650;">Phạm vi dữ liệu</div>
              <div style="margin-top:8px;">Đơn Olist từ 2016-09-04 đến 2018-10-17, cộng thuộc tính Marketing Funnel trên seller.</div>
              <div style="margin-top:8px;">Ngày chốt kho: <b>2018-10-17</b>. App đọc Gold và DSS qua SQL Warehouse.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"""
            <div style="border:1px solid #e4ddd2;border-radius:12px;padding:16px 18px;">
              <div style="color:{NAVY};font-weight:650;">Luồng</div>
              <div style="margin-top:8px;">CSV → Bronze → Silver → Gold → DSS → app</div>
              <div style="margin-top:8px;">Dashboard đọc Gold. DSS đọc điểm đã chấm, rồi ghi quyết định vào <code>dss.decision_log</code>.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.write("")
    pages = st.session_state.get("nav_pages", {})
    labels = [
        ("kpi", "Tổng quan KPI"),
        ("olap", "OLAP Explorer"),
        ("risk", "Seller risk"),
        ("policy", "Policy scenario"),
    ]
    columns = st.columns(4)
    for column, (key, label) in zip(columns, labels):
        with column:
            target = pages.get(key)
            if target is not None and st.button(label, width="stretch"):
                st.switch_page(target)
