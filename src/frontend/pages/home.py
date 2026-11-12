"""Landing page. Marketplace numbers, then the path through the story."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, queries
from lib.glossary import (
    DATA_AS_OF,
    DATA_PLACE,
    DENSE_MONTH_MIN_ORDERS,
    FUNNEL_DATASET_URL,
    GLOSSARY,
    HOME_SHORT_TERMS,
    HOME_TERMS,
    LICENSE_NAME,
    LICENSE_URL,
    MODEL_M1,
    MODEL_M2,
    OLIST_DATASET_URL,
    REPO_URL,
    explain,
    freshness_line,
    short_label,
    short_text,
)
from lib.ui import badge_actual, badge_predicted, chip, kpi_card, next_step
from src.dss.params import AS_OF_MONTH, N, X


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


def _text(value) -> str:
    if value is None:
        return "—"
    try:
        if pd.isna(value):
            return "—"
    except TypeError:
        pass
    if hasattr(value, "strftime"):
        if getattr(value, "tzinfo", None) is not None:
            return value.strftime("%Y-%m-%d %H:%M %Z")
        if hasattr(value, "hour"):
            return value.strftime("%Y-%m-%d %H:%M")
        return value.strftime("%Y-%m-%d")
    return str(value)


def _day(value) -> str:
    text = _text(value)
    if text == "—":
        return text
    return text.split(" ")[0]


def _marketplace() -> tuple[float | None, float | None, float | None]:
    monthly = db.query(*queries.kpi_seller_month(None, None, None, None)).iloc[0]
    story = db.query(*queries.story_by_region(None, None, None, None, None))
    total = story[story["is_total"].astype(int) == 1].iloc[0]
    sellers = db.query(*queries.active_sellers()).iloc[0]
    gmv = _num(monthly["gmv"])
    rate = _ratio(total["bad_orders"], total["eligible_orders"])
    active = _num(sellers["active_sellers"])
    return gmv, rate, active


def _context() -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    profile = db.query(*queries.home_profile()).iloc[0]
    months = db.query(*queries.home_months())
    tables = db.query(*queries.home_tables())
    return profile, months, tables


def _month_notes(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    if frame is None or frame.empty:
        return [], []
    work = frame.copy()
    work["n_orders"] = pd.to_numeric(work["n_orders"], errors="coerce")
    work = work.dropna(subset=["year_month", "n_orders"]).sort_values("year_month")
    if work.empty:
        return [], []
    thin = work.loc[work["n_orders"] < DENSE_MONTH_MIN_ORDERS, "year_month"].astype(str).tolist()
    labels = work["year_month"].astype(str).tolist()
    start = pd.Period(labels[0], freq="M")
    end = pd.Period(labels[-1], freq="M")
    present = set(labels)
    gaps: list[str] = []
    cursor = start
    while cursor <= end:
        label = str(cursor)
        if label not in present:
            gaps.append(label)
        cursor += 1
    return thin, gaps


def _latest_job(row: pd.Series) -> tuple[str, str]:
    choices = []
    for column, source in (
        ("gold_loaded_at", "gold.etl_audit.loaded_at"),
        ("dss_scored_at", "dss.seller_risk_score.scored_at"),
    ):
        raw = row[column]
        shown = _text(raw)
        if shown == "—":
            continue
        choices.append((raw, shown, source))
    if not choices:
        return "chưa ghi nhận", ""
    _raw, shown, source = max(choices, key=lambda item: item[0])
    return shown, source


def _star_counts(tables: pd.DataFrame) -> tuple[int | None, int | None]:
    if tables is None or tables.empty:
        return None, None
    gold_name = db.settings()["gold"]
    names = tables.loc[tables["table_schema"].astype(str) == gold_name, "table_name"].astype(str)
    return int(names.str.startswith("dim_").sum()), int(names.str.startswith("fact_").sum())


def _hero(fmt_brl, fmt_int, fmt_pct) -> None:
    st.markdown("# **Olist Seller Performance**")
    st.write(
        "Hệ hỗ trợ ra quyết định giúp sàn Olist chọn cách xử lý seller "
        "để giảm đơn trải nghiệm xấu mà không mất quá nhiều doanh thu."
    )
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
        st.stop()

    badge_actual()
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


def _context_block(fmt_int) -> tuple[pd.Series | None, pd.DataFrame | None, pd.DataFrame | None]:
    st.markdown("### Bối cảnh: Olist là gì?")
    st.markdown(
        "Olist là marketplace kết nối seller nhỏ với các sàn lớn ở Brazil. "
        f"Dữ liệu là [Brazilian E-Commerce Public Dataset by Olist]({OLIST_DATASET_URL}) "
        f"và [Marketing Funnel by Olist]({FUNNEL_DATASET_URL}). "

    )
    profile = months = tables = None
    try:
        with st.spinner("Đang tải quy mô kho…"):
            profile, months, tables = _context()
    except Exception as exc:
        db.show_warehouse_error(exc)
    if profile is not None:
        span = f"{_day(profile['min_purchase'])} → {_day(profile['max_purchase'])}"
        facts = [
            ("Khoảng thời gian đơn", span),
            ("Số đơn", fmt_int(profile["n_orders"])),
            ("Số seller", fmt_int(profile["n_sellers"])),
            ("Số khách", fmt_int(profile["n_customers"])),
            ("Số danh mục", fmt_int(profile["n_categories"])),
            ("Số bang", fmt_int(profile["n_states"])),
        ]
        columns = st.columns(len(facts))
        for column, (label, value) in zip(columns, facts):
            with column:
                chip(label, value)
        st.caption(
            f"Số seller ở hàng này là mọi seller trong kho ({DATA_PLACE}). "
            "Thẻ phía trên chỉ seller có ít nhất một đơn hợp lệ. Số bang là bang của seller."
        )
    st.write(
        "Đơn giao trễ hoặc review thấp khiến khách bỏ sàn. "
        "Seller là đối tác, nên không thể chặn bừa: chặn nhầm là mất GMV."
    )
    return profile, months, tables


def _audience() -> None:
    st.markdown("### Ai dùng và dùng để làm gì?")
    st.write(
        "Người dùng là trưởng bộ phận chất lượng seller. "
        "Họ mở app mỗi tháng, sau khi số liệu đã chốt."
    )
    st.markdown(
        """
- **(a)** Nắm tình hình chất lượng của sàn.
- **(b)** Tìm nguồn gốc vấn đề: vùng, kỳ, hoặc nhóm hàng.
- **(c)** Chọn seller và chính sách can thiệp, rồi ghi lại quyết định.
        """
    )


def _path() -> None:
    st.markdown("### Dùng thế nào?")
    diagram = [
        ("1", "Sức khỏe marketplace"),
        ("2", "Tìm nguyên nhân"),
        ("3", "Seller đáng lo"),
        ("4", "Chọn chính sách và ghi quyết định"),
    ]
    columns = st.columns(len(diagram))
    for column, (number, name) in zip(columns, diagram):
        with column, st.container(border=True):
            st.markdown(f"**{number}. {name}**")

    pages = st.session_state.get("nav_pages", {})
    cards = [
        ("kpi", "1", "Sức khỏe marketplace đang thế nào?", "Dùng khi bạn muốn xem sàn đang khỏe hay đang tệ.", "actual"),
        ("olap", "2", "GMV và trải nghiệm xấu đến từ đâu?", "Dùng khi bạn muốn biết vùng, kỳ, hoặc nhóm hàng nào kéo số xuống.", "actual"),
        ("risk", "3", "Seller nào đáng lo nhất?", "Dùng khi bạn muốn xếp seller theo điểm rủi ro tháng sau.", "predicted"),
        ("policy", "4", "Chọn chính sách nào?", "Dùng khi bạn muốn so sánh phương án trước khi chốt và ghi lại quyết định.", "predicted"),
    ]
    columns = st.columns(len(cards))
    for column, (key, number, question, when, kind) in zip(columns, cards):
        with column, st.container(border=True):
            st.markdown(f"**{number}**")
            if kind == "actual":
                badge_actual()
            else:
                badge_predicted()
            st.markdown(question)
            st.write(when)
            target = pages.get(key)
            if target is not None:
                st.page_link(target, label="Mở trang")
    st.write(
        "Bộ lọc ở sidebar áp dụng cho trang 1–2; "
        "trang 3–4 dùng kết quả mô hình của tháng chấm."
    )


def _reading() -> None:
    st.markdown("### Số liệu đọc thế nào?")
    done, forecast = st.columns(2)
    with done:
        badge_actual()
        st.write("Thực tế là việc đã xảy ra trong kho. Trang sức khỏe và trang nguyên nhân đọc loại này.")
    with forecast:
        badge_predicted()
        st.write("Dự báo chưa xảy ra. M1 ước tính tháng tới. M2 mô phỏng một chính sách.")
    for term in HOME_SHORT_TERMS:
        st.markdown(f"**{short_label(term)}**")
        st.write(short_text(term))
    st.write(MODEL_M1)
    st.write(MODEL_M2)
    with st.expander("Giải thích chỉ số"):
        for term in HOME_TERMS:
            row = GLOSSARY[term]
            st.markdown(f"**{row['label']}**")
            st.write(explain(term))


def _lineage(fmt_int, profile, months, tables) -> None:
    st.markdown("### Dữ liệu đến từ đâu và mới đến khi nào?")
    if profile is None:
        job_ts, job_source = "chưa ghi nhận", ""
    else:
        job_ts, job_source = _latest_job(profile)
    with st.container(border=True):
        st.markdown(
            f"**Dữ liệu đến {DATA_AS_OF} · tháng chấm mô hình {AS_OF_MONTH} · "
            f"job chạy lần cuối {job_ts}**"
        )
    st.caption(freshness_line())
    if job_source:
        st.caption(f"Mốc job lấy từ {job_source}.")

    n_dim, n_fact = _star_counts(tables) if tables is not None else (None, None)
    if n_dim is None or n_fact is None:
        gold_line = "Kho hình sao: các bảng chiều và bảng sự kiện, để đo GMV và trải nghiệm."
    else:
        gold_line = (
            f"Kho hình sao: {fmt_int(n_dim)} chiều và {fmt_int(n_fact)} bảng sự kiện, "
            "để đo GMV và trải nghiệm."
        )
    layers = [
        ("Kaggle CSV", "File đơn và funnel tải từ Kaggle, là nguồn gốc."),
        ("Bronze", "Bản chép thô, giữ nguyên chữ như file."),
        ("Silver", "Làm sạch: đúng kiểu, bỏ dòng trùng, gắn vùng."),
        ("Gold", gold_line),
        ("DSS", "M1 chấm xác suất đơn xấu. M2 thử chính sách trong trần GMV và số seller."),
        ("App", "Đọc Gold và DSS qua SQL Warehouse. Databricks Jobs chạy các bước trên."),
    ]
    columns = st.columns(len(layers))
    for column, (title, sentence) in zip(columns, layers):
        with column, st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(sentence)

    with st.expander("Chi tiết kỹ thuật"):
        st.write("CSV → Bronze → Silver → Gold → DSS → app.")
        st.write("App đọc Gold và DSS qua Databricks SQL Warehouse.")
        if tables is None or tables.empty:
            st.write("Chưa đọc được danh sách bảng.")
        else:
            for schema, group in tables.groupby("table_schema", sort=True):
                names = ", ".join(group["table_name"].astype(str).tolist())
                st.markdown(f"**{schema}**")
                st.write(names)
        if profile is not None:
            st.write(f"Gold etl_audit.loaded_at: {_text(profile['gold_loaded_at'])}.")
            st.write(f"dss.seller_risk_score.scored_at: {_text(profile['dss_scored_at'])}.")
        st.markdown(
            f"[README]({REPO_URL}/blob/main/README.md) · "
            f"[Nguồn dữ liệu]({REPO_URL}/blob/main/data/README.md) · "
            f"[Kiểm tra pytest]({REPO_URL}/tree/main/src/tests)"
        )
        st.write(
            "Kiểm tra chất lượng: notebook ETL in đối soát số dòng, tổng giá và ràng buộc Delta. "
            "Pytest local nằm ở src/tests."
        )

    with st.expander("Giới hạn dữ liệu"):
        thin, gaps = _month_notes(months) if months is not None else ([], [])
        if thin:
            st.write("Tháng ít đơn: " + ", ".join(thin) + ".")
        else:
            st.write("Chưa tách được tháng ít đơn.")
        if gaps:
            st.write("Không có đơn trong tháng: " + ", ".join(gaps) + ".")
        if profile is not None:
            st.write(f"Đơn gồm nhiều seller: {fmt_int(profile['multi_seller_orders'])}.")
        st.write(
            "Kho là dữ liệu lịch sử đã dừng, nên “tháng tới” trên trang seller và chính sách "
            "là mô phỏng của mô hình, không phải đơn mới phát sinh."
        )

    with st.expander("Dữ liệu đến từ đâu?"):
        st.write("CSV → Bronze → Silver → Gold → DSS → app.")
        st.write("App đọc Gold và DSS qua Databricks SQL Warehouse.")


def render(settings=None) -> None:
    del settings
    from lib.ui import fmt_brl, fmt_int, fmt_pct

    _hero(fmt_brl, fmt_int, fmt_pct)
    profile, months, tables = _context_block(fmt_int)
    _audience()
    _path()
    _reading()
    _lineage(fmt_int, profile, months, tables)
    next_step("home")
