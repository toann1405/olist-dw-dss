"""Landing page. Three marketplace numbers, then the path through the story."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, queries
from lib.glossary import GLOSSARY, HOME_TERMS, explain, freshness_line
from lib.ui import kpi_card, next_step
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
    monthly = db.query(*queries.kpi_seller_month(None, None, None)).iloc[0]
    story = db.query(*queries.story_by_region(None, None, None, None))
    total = story[story["is_total"].astype(int) == 1].iloc[0]
    sellers = db.query(*queries.active_sellers()).iloc[0]
    gmv = _num(monthly["gmv"])
    rate = _ratio(total["bad_orders"], total["eligible_orders"])
    active = _num(sellers["active_sellers"])
    return gmv, rate, active


def render(settings=None) -> None:
    del settings
    from lib.ui import fmt_brl, fmt_int, fmt_pct

    st.markdown(
        "### Một số seller gây ra phần lớn đơn hàng tệ. "
        "Can thiệp thế nào mà không mất doanh thu?"
    )
    try:
        with st.spinner("Đang tải dữ liệu…"):
            gmv, bad_rate, active = _marketplace()
    except Exception as exc:
        db.show_warehouse_error(exc)
        next_step("home")
        return

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
        st.markdown(f"**GMV ảnh hưởng ≤ {X:g}%**")
    with two, st.container(border=True):
        st.markdown(f"**Can thiệp ≤ {int(N)} seller**")

    st.write(freshness_line())

    pages = st.session_state.get("nav_pages", {})
    cards = [
        ("kpi", "1", "Sức khỏe marketplace đang thế nào?", "Dùng khi bạn muốn xem sàn đang khỏe hay đang tệ."),
        ("olap", "2", "GMV và trải nghiệm xấu đến từ đâu?", "Dùng khi bạn muốn biết vùng, kỳ, hoặc nhóm hàng nào kéo số xuống."),
        ("risk", "3", "Seller nào đáng lo nhất?", "Dùng khi bạn muốn xếp seller theo điểm rủi ro tháng sau."),
        ("policy", "4", "Chọn chính sách nào?", "Dùng khi bạn muốn so sánh phương án trước khi chốt."),
    ]
    columns = st.columns(4)
    for column, (key, number, question, when) in zip(columns, cards):
        with column, st.container(border=True):
            st.markdown(f"**{number}**")
            st.markdown(question)
            st.write(when)
            target = pages.get(key)
            if target is not None:
                st.page_link(target, label="Mở trang")

    with st.expander("Giải thích chỉ số"):
        for term in HOME_TERMS:
            row = GLOSSARY[term]
            st.markdown(f"**{row['label']}**")
            st.write(explain(term))

    with st.expander("Dữ liệu đến từ đâu?"):
        st.write("CSV → Bronze → Silver → Gold → DSS → app.")
        st.write("App đọc Gold và DSS qua Databricks SQL Warehouse.")

    next_step("home")
