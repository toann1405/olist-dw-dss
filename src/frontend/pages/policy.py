"""M2 screen. Slider results stay in the app. Only a confirmed decision is inserted."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from lib import db, queries
from src.dss.params import (
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
from src.dss.policy import (
    PolicyParams,
    compare_policies,
    goal_seek,
    scenario_record,
    simulate,
    tornado,
)


def _params() -> PolicyParams:
    st.caption(
        "Số khởi tạo là quy ước trong src/dss/params.py. "
        "SPEC không khóa các số này. X=10 và N=40 là số đã khóa."
    )
    theta_1 = st.slider("theta 1", 0.0, 1.0, float(THETA_1), 0.01)
    theta_2 = st.slider("theta 2", 0.0, 1.0, float(THETA_2), 0.01)
    theta_3 = st.slider("theta 3", 0.0, 1.0, float(THETA_3), 0.01)
    e1 = st.slider("e hạng 1", 0.0, 1.0, float(E1), 0.05)
    e2 = st.slider("e hạng 2", 0.0, 1.0, float(E2), 0.05)
    e3 = st.slider("e hạng 3", 0.0, 1.0, float(E3), 0.05)
    e_p1 = st.slider("e của P1", 0.0, 1.0, float(E_P1), 0.05)
    late_ship = st.slider("Ngưỡng bàn giao trễ", 0.0, 1.0, float(LATE_SHIP_THRESHOLD), 0.01)
    avg_review = st.slider("Ngưỡng điểm review", 1.0, 5.0, float(AVG_REVIEW_THRESHOLD), 0.1)
    transfer = st.slider("r chuyển đơn", 0.0, 1.0, float(R), 0.05)
    season = st.slider("s mùa vụ", 0.0, 2.0, float(S), 0.05)
    min_orders = st.number_input("min_orders", min_value=0, value=int(MIN_ORDERS), step=1)
    st.caption(f"X = {X:g}% GMV. N = {int(N)} seller/tháng.")
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


def _summary(results) -> pd.DataFrame:
    rows = []
    for item in results:
        rows.append(
            {
                "policy_code": item.policy_code,
                "expected_bad_orders": item.expected_bad_orders,
                "gmv_affected_pct": item.gmv_affected_pct,
                "n_sellers_flagged": item.n_sellers_flagged,
                "meets_x": item.meets_x,
                "meets_n": item.meets_n,
            }
        )
    return pd.DataFrame(rows)


def _insert(scores: pd.DataFrame, choice: str, params: PolicyParams, note: str) -> None:
    if choice not in {"P0", "P1", "P2"}:
        raise ValueError("policy_code must be P0, P1, or P2")
    result = simulate(scores, choice, params)
    decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    record = scenario_record(result, params, str(scores["as_of_month"].iloc[0]), decided_at)
    current = db.query_uncached(*queries.next_decision_id())
    decision_id = int(current["max_id"].iloc[0]) + 1
    values = (
        decision_id,
        decided_at,
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
        note.strip() or None,
    )
    db.execute(*queries.insert_decision(values))
    st.success(f"Đã ghi decision_id {decision_id}.")


def render(settings=None) -> None:
    del settings
    from lib.ui import page_header

    page_header("Policy scenario", "So sánh P0, P1 và P2, rồi ghi một quyết định.", "policy")
    try:
        with st.spinner("Đang hỏi SQL Warehouse..."):
            scores = db.query(*queries.scores())
            snapshot = db.query(*queries.policy_snapshot())
    except Exception as exc:
        db.show_warehouse_error(exc)
        return
    if scores.empty:
        st.info("Chưa có điểm. Chạy src/dss/dss_job.py trên Databricks trước.")
        return

    st.subheader("Kết quả job gần nhất")
    st.caption("Ba dòng này là snapshot trong dss.policy_scenario. Slider bên dưới không ghi đè bảng đó.")
    st.dataframe(snapshot, width="stretch")

    params = _params()
    results = compare_policies(scores, params)
    st.subheader("What-if")
    st.caption("P0 không can thiệp. P1 dùng ngưỡng KPI cứng. P2 dùng điểm rủi ro.")
    st.dataframe(_summary(results), width="stretch")

    st.subheader("Goal seeking")
    chosen, sought = goal_seek(scores, params)
    st.write(
        f"theta_1 nhỏ nhất còn trong trần GMV: {chosen.theta_1:.4f}. "
        f"theta_2={chosen.theta_2:.4f}, theta_3={chosen.theta_3:.4f}."
    )
    st.write(
        f"P2: đơn xấu dự kiến {sought.expected_bad_orders:.2f}, "
        f"GMV bị ảnh hưởng {sought.gmv_affected_pct}, "
        f"seller bị gắn cờ {sought.n_sellers_flagged}."
    )
    st.subheader("Sensitivity ±20%")
    st.dataframe(tornado(scores, chosen), width="stretch")

    st.subheader("Ghi quyết định")
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
    st.dataframe(flagged.loc[:, export_columns], width="stretch")
    st.download_button(
        "Tải CSV",
        flagged.loc[:, export_columns].to_csv(index=False).encode("utf-8"),
        file_name=f"flagged_sellers_{choice}.csv",
        mime="text/csv",
    )
    note = st.text_input("Ghi chú", "")
    if st.button("Ghi quyết định"):
        try:
            _insert(scores, choice, params, note)
        except Exception as exc:
            db.show_warehouse_error(exc)
