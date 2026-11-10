"""Streamlit query and DSS UI. Reads Gold and dss through a SQL warehouse.

Screen 7 appends dss.decision_log. This app does not write the score or
scenario tables and does not read CSV files.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dss.params import (  # noqa: E402
    AVG_REVIEW_THRESHOLD,
    E1,
    E2,
    E3,
    E_P1,
    LATE_SHIP_THRESHOLD,
    MIN_ORDERS,
    N,
    R,
    S,
    THETA_1,
    THETA_2,
    THETA_3,
    X,
)
from src.dss.policy import (  # noqa: E402
    PolicyParams,
    compare_policies,
    goal_seek,
    scenario_record,
    simulate,
    tornado,
)

FORBIDDEN = (
    "insert",
    "update",
    "delete",
    "merge",
    "drop",
    "alter",
    "create",
    "grant",
    "truncate",
    "copy",
    "optimize",
    "vacuum",
    "bronze",
    "silver",
)


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def connection_settings() -> dict[str, str]:
    env = load_env(ROOT / ".env")
    return {
        "host": env.get("DATABRICKS_HOST", "").replace("https://", "").strip("/"),
        "http_path": env.get("DATABRICKS_HTTP_PATH", ""),
        "token": env.get("DATABRICKS_TOKEN", ""),
        "catalog": env.get("UC_CATALOG", "olist_catalog") or "olist_catalog",
        "dss": env.get("DSS_SCHEMA", "dss") or "dss",
    }


def connect(settings: dict[str, str]):
    from databricks import sql

    missing = [name for name in ("host", "http_path", "token") if not settings[name]]
    if missing:
        raise RuntimeError(f"Missing .env values: {', '.join(missing)}")
    return sql.connect(
        server_hostname=settings["host"],
        http_path=settings["http_path"],
        access_token=settings["token"],
    )


def fetch(settings: dict[str, str], statement: str, parameters: tuple | None = None) -> pd.DataFrame:
    with connect(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(statement, parameters)
            rows = cursor.fetchall()
            columns = [item[0] for item in cursor.description] if cursor.description else []
    return pd.DataFrame(rows, columns=columns)


def execute(settings: dict[str, str], statement: str, parameters: tuple) -> None:
    with connect(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(statement, parameters)
        conn.commit()


def validate_select(statement: str) -> str:
    text = statement.strip().rstrip(";").strip()
    if not text:
        raise ValueError("Enter one SELECT.")
    if ";" in text:
        raise ValueError("One statement only.")
    lowered = text.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Only a SELECT or WITH query is allowed.")
    for word in FORBIDDEN:
        if re.search(rf"\b{word}\b", lowered):
            raise ValueError(f"Query cannot use {word}.")
    if "gold" not in lowered and "dss" not in lowered:
        raise ValueError("Name a gold or dss table in the query.")
    return text


def sidebar_params() -> PolicyParams:
    st.sidebar.header("Tham số")
    theta_1 = st.sidebar.slider("theta 1", 0.0, 1.0, THETA_1, 0.01)
    theta_2 = st.sidebar.slider("theta 2", 0.0, 1.0, THETA_2, 0.01)
    theta_3 = st.sidebar.slider("theta 3", 0.0, 1.0, THETA_3, 0.01)
    e1 = st.sidebar.slider("e hạng 1", 0.0, 1.0, E1, 0.05)
    e2 = st.sidebar.slider("e hạng 2", 0.0, 1.0, E2, 0.05)
    e3 = st.sidebar.slider("e hạng 3", 0.0, 1.0, E3, 0.05)
    e_p1 = st.sidebar.slider("e của P1", 0.0, 1.0, E_P1, 0.05)
    late_ship = st.sidebar.slider("Ngưỡng bàn giao trễ", 0.0, 1.0, LATE_SHIP_THRESHOLD, 0.01)
    avg_review = st.sidebar.slider("Ngưỡng điểm review", 1.0, 5.0, AVG_REVIEW_THRESHOLD, 0.1)
    transfer = st.sidebar.slider("r chuyển đơn", 0.0, 1.0, R, 0.05)
    season = st.sidebar.slider("s mùa vụ", 0.0, 2.0, S, 0.05)
    min_orders = st.sidebar.number_input("min_orders", min_value=0, value=MIN_ORDERS, step=1)
    return PolicyParams(
        theta_1=theta_1,
        theta_2=theta_2,
        theta_3=theta_3,
        e1=e1,
        e2=e2,
        e3=e3,
        e_p1=e_p1,
        late_ship_threshold=late_ship,
        avg_review_threshold=avg_review,
        r=transfer,
        s=season,
        min_orders=int(min_orders),
        x_limit=X,
        n_limit=N,
    )


def show_scenario_table(settings: dict[str, str], scores: pd.DataFrame, params: PolicyParams) -> list:
    results = compare_policies(scores, params)
    as_of = str(scores["as_of_month"].iloc[0])
    scored_at = scores["scored_at"].iloc[0] if "scored_at" in scores.columns else None
    rows = [scenario_record(item, params, as_of, scored_at) for item in results]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    return results


def page_scores(settings: dict[str, str]) -> None:
    st.header("Điểm rủi ro")
    catalog = settings["catalog"]
    schema = settings["dss"]
    frame = fetch(
        settings,
        f"""
        SELECT seller_id, as_of_month, p_bad, q_bar, gmv, late_ship_rate, avg_review,
               n_orders_valid, model_name, trained_through_month
        FROM {catalog}.{schema}.seller_risk_score
        ORDER BY p_bad DESC
        """,
    )
    if frame.empty:
        st.info("Bảng điểm chưa có dòng. Chạy notebook src/dss/dss_job.py trên workspace trước.")
        return
    st.dataframe(frame, use_container_width=True)


def page_what_if(scores: pd.DataFrame, params: PolicyParams) -> None:
    st.header("What-if")
    st.caption("P0 không can thiệp. P1 dùng ngưỡng KPI cứng. P2 dùng điểm rủi ro. X=10 và N=40.")
    show_scenario_table({}, scores, params)


def page_goal(scores: pd.DataFrame, params: PolicyParams) -> None:
    st.header("Goal seeking và sensitivity")
    chosen, result = goal_seek(scores, params)
    st.write(
        f"theta_1 nhỏ nhất còn trong trần GMV: {chosen.theta_1:.4f}. "
        f"theta_2={chosen.theta_2:.4f}, theta_3={chosen.theta_3:.4f}."
    )
    st.write(
        f"P2: đơn xấu dự kiến {result.expected_bad_orders:.2f}, "
        f"GMV bị ảnh hưởng {result.gmv_affected_pct}, "
        f"seller bị gắn cờ {result.n_sellers_flagged}."
    )
    st.subheader("Sensitivity ±20%")
    st.dataframe(tornado(scores, chosen), use_container_width=True)


def page_decision(settings: dict[str, str], scores: pd.DataFrame, params: PolicyParams) -> None:
    st.header("Quyết định và xuất danh sách")
    choice = st.radio("Phương án chốt", ("P0", "P1", "P2"), horizontal=True)
    result = simulate(scores, choice, params)
    flagged = result.sellers[result.sellers["flagged"]].copy()
    st.write(
        f"Đơn xấu dự kiến {result.expected_bad_orders:.2f}. "
        f"GMV bị ảnh hưởng {result.gmv_affected_pct}. "
        f"Seller bị gắn cờ {result.n_sellers_flagged}."
    )
    export_columns = [
        "seller_id",
        "tier",
        "p_bad",
        "gmv",
        "late_ship_rate",
        "avg_review",
        "n_orders_valid",
        "e_k",
    ]
    st.dataframe(flagged.loc[:, export_columns], use_container_width=True)
    st.download_button(
        "Tải CSV",
        flagged.loc[:, export_columns].to_csv(index=False).encode("utf-8"),
        file_name=f"flagged_sellers_{choice}.csv",
        mime="text/csv",
    )
    note = st.text_input("Ghi chú", "")
    if st.button("Ghi decision_log"):
        catalog = settings["catalog"]
        schema = settings["dss"]
        current = fetch(settings, f"SELECT COALESCE(MAX(decision_id), 0) AS max_id FROM {catalog}.{schema}.decision_log")
        decision_id = int(current["max_id"].iloc[0]) + 1
        record = scenario_record(
            result,
            params,
            str(scores["as_of_month"].iloc[0]),
            datetime.now(timezone.utc).replace(tzinfo=None),
        )
        execute(
            settings,
            f"""
            INSERT INTO {catalog}.{schema}.decision_log (
              decision_id, decided_at, as_of_month, policy_code,
              theta_1, theta_2, theta_3, e1, e2, e3, e_p1,
              late_ship_threshold, avg_review_threshold, r, s, min_orders,
              x_limit, n_limit, expected_bad_orders, gmv_affected_pct,
              n_sellers_flagged, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                record["scored_at"],
                record["as_of_month"],
                record["policy_code"],
                record["theta_1"],
                record["theta_2"],
                record["theta_3"],
                record["e1"],
                record["e2"],
                record["e3"],
                record["e_p1"],
                record["late_ship_threshold"],
                record["avg_review_threshold"],
                record["r"],
                record["s"],
                record["min_orders"],
                record["x_limit"],
                record["n_limit"],
                record["expected_bad_orders"],
                record["gmv_affected_pct"],
                record["n_sellers_flagged"],
                note or None,
            ),
        )
        st.success(f"Đã ghi decision_id {decision_id}.")


def page_query(settings: dict[str, str]) -> None:
    st.header("Truy vấn")
    statement = st.text_area(
        "Một câu SELECT trên gold hoặc dss",
        "SELECT seller_id, as_of_month, p_bad FROM dss.seller_risk_score LIMIT 20",
        height=140,
    )
    if st.button("Chạy"):
        checked = validate_select(statement)
        wrapped = "SELECT * FROM (" + checked + ") AS ad_hoc_query LIMIT 200"
        frame = fetch(settings, wrapped)
        st.dataframe(frame, use_container_width=True)
        st.caption(f"{len(frame)} dòng, tối đa 200.")


def main() -> None:
    st.set_page_config(page_title="Olist DSS", layout="wide")
    st.title("Olist seller DSS")
    settings = connection_settings()
    params = sidebar_params()
    page = st.sidebar.radio(
        "Trang",
        ("Điểm rủi ro", "What-if", "Goal seeking", "Quyết định", "Truy vấn"),
    )
    try:
        fetch(settings, "SELECT 1 AS ok")
    except Exception as exc:
        st.error("Chưa nối được SQL Warehouse (S2).")
        st.write(str(exc))
        st.markdown(
            """
            Hai phương án, dừng ở đây:

            1. Sửa `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_TOKEN` trong `.env` và bật warehouse, rồi mở lại trang này.
            2. Giữ app Streamlit này và chạy sau khi kết nối S2 thành công.

            App không đọc CSV.
            """
        )
        return
    needs_scores = page in ("What-if", "Goal seeking", "Quyết định")
    scores = pd.DataFrame()
    if needs_scores:
        catalog = settings["catalog"]
        schema = settings["dss"]
        scores = fetch(settings, f"SELECT * FROM {catalog}.{schema}.seller_risk_score")
        if scores.empty:
            st.info("Chưa có điểm. Chạy src/dss/dss_job.py trên Databricks trước.")
            return
    if page == "Điểm rủi ro":
        page_scores(settings)
    elif page == "What-if":
        page_what_if(scores, params)
    elif page == "Goal seeking":
        page_goal(scores, params)
    elif page == "Quyết định":
        page_decision(settings, scores, params)
    else:
        page_query(settings)


if __name__ == "__main__":
    main()
