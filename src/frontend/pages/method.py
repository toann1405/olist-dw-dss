"""Council page: lineage, definitions, and model assumptions. Not a monthly decision screen."""

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
from lib.ui import badge_actual, badge_predicted, chip, fmt_int, fmt_limit, next_step, page_header
from src.dss.params import AS_OF_MONTH, N, X


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


def freshness_sentence() -> str:
    """One line for Home. Numbers come from the warehouse when the query runs."""
    try:
        profile, _months, _tables = _context()
        job_ts, _source = _latest_job(profile)
    except Exception:
        job_ts = "chưa ghi nhận"
    return f"Dữ liệu đến {DATA_AS_OF} · tháng chấm {AS_OF_MONTH} · job chạy lần cuối {job_ts}"


def _context_block(fmt_int, profile) -> None:
    st.markdown(
        "Olist nối seller nhỏ với các sàn lớn ở Brazil. "
        f"[Brazilian E-Commerce]({OLIST_DATASET_URL}) và [Marketing Funnel]({FUNNEL_DATASET_URL})."
    )
    if profile is None:
        return
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
        "Số bang là bang của seller."
    )


def _audience() -> None:
    st.write("Trưởng bộ phận chất lượng seller mở app mỗi tháng, sau khi số liệu đã chốt.")
    st.markdown(
        """
- **(a)** Nắm tình hình chất lượng của sàn.
- **(b)** Tìm nguồn gốc: vùng, kỳ, hoặc nhóm hàng.
- **(c)** Chọn seller và chính sách, rồi ghi quyết định.
        """
    )


def _reading() -> None:
    done, forecast = st.columns(2)
    with done:
        badge_actual()
        st.write("Việc đã xảy ra trong kho. Trang sức khỏe và trang nguyên nhân đọc loại này.")
    with forecast:
        badge_predicted()
        st.write("Chưa xảy ra. M1 ước tính tháng tới. M2 mô phỏng một chính sách.")
    for term in HOME_SHORT_TERMS:
        st.markdown(f"**{short_label(term)}** — {short_text(term)}")
    st.write(MODEL_M1)
    st.write(MODEL_M2)
    with st.expander("Giải thích chỉ số"):
        for term in HOME_TERMS:
            row = GLOSSARY[term]
            st.markdown(f"**{row['label']}**")
            st.write(explain(term))


def _lineage(fmt_int, profile, months, tables) -> None:
    if profile is None:
        job_ts, job_source = "chưa ghi nhận", ""
    else:
        job_ts, job_source = _latest_job(profile)
    st.markdown(
        f"**Dữ liệu đến {DATA_AS_OF} · tháng chấm mô hình {AS_OF_MONTH} · job chạy lần cuối {job_ts}**"
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
        st.write(f"Giấy phép nguồn: [{LICENSE_NAME}]({LICENSE_URL}).")
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


def _assumptions() -> None:
    st.write(MODEL_M1)
    st.write(MODEL_M2)
    st.write(
        f"SPEC khóa trần GMV {fmt_limit(X)}% và trần {fmt_int(N)} seller. "
        "Các ngưỡng còn lại nằm trong src/dss/params.py và không khóa trong SPEC."
    )
    st.write("Hiệu quả can thiệp và tỷ lệ đơn chuyển sang seller khác là giả định, không phải số đã đo.")


def render(settings=None) -> None:
    del settings
    from lib.ui import fmt_int

    profile = months = tables = None
    try:
        with st.spinner("Đang tải dữ liệu…"):
            profile, months, tables = _context()
    except Exception as exc:
        db.show_warehouse_error(exc)
    if profile is None:
        conclusion = f"Dữ liệu đến {DATA_AS_OF} · tháng chấm {AS_OF_MONTH} · job chạy lần cuối chưa ghi nhận"
    else:
        job_ts, _source = _latest_job(profile)
        conclusion = f"Dữ liệu đến {DATA_AS_OF} · tháng chấm {AS_OF_MONTH} · job chạy lần cuối {job_ts}"
    page_header("Dữ liệu đến từ đâu, mới đến khi nào, giới hạn gì?", conclusion, None)
    with st.expander("Bối cảnh Olist"):
        _context_block(fmt_int, profile)
    with st.expander("Ai dùng"):
        _audience()
    with st.expander("Số liệu đọc thế nào"):
        _reading()
    with st.expander("Dữ liệu đi qua những tầng nào"):
        _lineage(fmt_int, profile, months, tables)
    with st.expander("Giả định M1 và M2"):
        _assumptions()
    next_step("method")
