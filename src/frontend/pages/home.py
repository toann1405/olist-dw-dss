"""Landing page. Three marketplace numbers, then links into the monthly path."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, queries
from lib.glossary import explain
from lib.ui import kpi_card, next_step
from pages.method import freshness_sentence
from src.dss.params import N, X


def _num(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        return None
    return float(value)


def _ratio(numerator, denominator):
    top = _num(numerator)
    bottom = _num(denominator)
    if top is None or bottom is None or bottom == 0:
        return None
    return top / bottom


def _marketplace() -> tuple[float | None, float | None, float | None]:
    monthly = db.query(*queries.kpi_seller_month(None, None, None, None)).iloc[0]
    story = db.query(*queries.story_by_region(None, None, None, None, None))
    total = story[story["is_total"].astype(int) == 1].iloc[0]
    sellers = db.query(*queries.active_sellers()).iloc[0]
    gmv = _num(monthly["gmv"])
    rate = _ratio(total["bad_orders"], total["eligible_orders"])
    active = _num(sellers["active_sellers"])
    return gmv, rate, active


def render(settings=None) -> None:
    del settings
    from lib.ui import fmt_brl, fmt_int, fmt_limit, fmt_pct

    st.markdown("# **Olist Seller Performance**")
    st.write(
        "Chọn cách xử lý seller để giảm đơn trải nghiệm xấu mà không mất quá nhiều doanh thu."
    )
    try:
        with st.spinner("Đang tải dữ liệu…"):
            gmv, bad_rate, active = _marketplace()
    except Exception as exc:
        db.show_warehouse_error(exc)
        next_step("home")
        st.stop()

    columns = st.columns(3)
    cards = [
        ("Tổng GMV", fmt_brl(gmv), explain("gmv")),
        ("% đơn trải nghiệm xấu", fmt_pct(bad_rate), explain("bad_experience")),
        ("Số seller đang hoạt động", fmt_int(active), explain("active_sellers")),
    ]
    for column, (label, value, help_text) in zip(columns, cards):
        with column:
            kpi_card(label, value, help_text=help_text)
    st.caption("Ba số này là toàn bộ dữ liệu, không theo bộ lọc sidebar.")

    one, two = st.columns(2)
    with one, st.container(border=True):
        st.markdown(f"**GMV ảnh hưởng ≤ {fmt_limit(X)}%**")
    with two, st.container(border=True):
        st.markdown(f"**Can thiệp ≤ {fmt_int(N)} seller**")

    pages = st.session_state.get("nav_pages", {})
    links = [
        ("kpi", "1", "Sức khỏe marketplace đang thế nào?", "Khi cần biết sàn khỏe hay tệ hơn tháng trước.", "Thực tế"),
        ("olap", "2", "GMV và trải nghiệm xấu đến từ đâu?", "Khi cần biết vùng, kỳ hoặc nhóm hàng kéo số xuống.", "Thực tế"),
        ("risk", "3", "Seller nào đáng lo nhất?", "Khi cần danh sách seller bị gắn cờ tháng tới.", "Dự báo"),
        ("policy", "4", "Chọn chính sách nào?", "Khi cần chốt phương án và ghi quyết định.", "Dự báo"),
    ]
    columns = st.columns(len(links))
    for column, (key, number, question, when, kind) in zip(columns, links):
        with column, st.container(border=True):
            st.markdown(f"**{number}. {question}**")
            st.caption(f"{kind}. {when}")
            target = pages.get(key)
            if target is not None:
                st.page_link(target, label="Mở trang")
    st.caption("Bộ lọc sidebar dùng cho trang 1. Trang 3–4 dùng tháng chấm mô hình.")
    st.caption(freshness_sentence())
    next_step("home")
