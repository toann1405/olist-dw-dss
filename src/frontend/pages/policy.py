"""M2 screen. Slider results stay in the app. Only a confirmed decision is inserted.

Bố cục theo logic quyết định:
  1. Kết luận (3 thẻ so sánh phương án + khuyến nghị)
  2. Điều chỉnh giả định (expander, mặc định đóng)
  3. Ngưỡng gợi ý (goal seek)
  4. Độ tin cậy (sensitivity)
  5. Chốt quyết định (danh sách seller, xác nhận, ghi decision_log)
"""

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

# ---------------------------------------------------------------------------
# Tên hiển thị
# ---------------------------------------------------------------------------

POLICY_NAMES = {
    "P0": "Không can thiệp",
    "P1": "Ngưỡng KPI cố định",
    "P2": "Điểm rủi ro dự báo",
}
POLICY_DESC = {
    "P0": "Giữ nguyên, làm mốc so sánh.",
    "P1": "Xử lý seller giao trễ nhiều hoặc điểm review thấp.",
    "P2": "Xử lý seller có điểm rủi ro dự báo cao.",
}


def _label(code: str) -> str:
    return f"{POLICY_NAMES.get(code, code)} ({code})"


# ---------------------------------------------------------------------------
# Giả định (12 tham số) -- gom nhóm, đặt nhãn business, có giá trị mặc định
# Đơn vị trên UI: các tỷ lệ hiển thị theo %, đổi về 0-1 khi tạo PolicyParams.
# ---------------------------------------------------------------------------

DEFAULTS = {
    "p_theta_1": round(float(THETA_1), 2),
    "p_theta_2": round(float(THETA_2), 2),
    "p_theta_3": round(float(THETA_3), 2),
    "p_e1": int(round(float(E1) * 100)),
    "p_e2": int(round(float(E2) * 100)),
    "p_e3": int(round(float(E3) * 100)),
    "p_e_p1": int(round(float(E_P1) * 100)),
    "p_late": int(round(float(LATE_SHIP_THRESHOLD) * 100)),
    "p_review": round(float(AVG_REVIEW_THRESHOLD), 1),
    "p_r": int(round(float(R) * 100)),
    "p_s": round(float(S), 2),
    "p_min_orders": int(MIN_ORDERS),
}


def _init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def _reset_params() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


def _apply_suggestion(t1: float, t2: float, t3: float) -> None:
    st.session_state["p_theta_1"] = min(1.0, max(0.0, round(float(t1), 2)))
    st.session_state["p_theta_2"] = min(1.0, max(0.0, round(float(t2), 2)))
    st.session_state["p_theta_3"] = min(1.0, max(0.0, round(float(t3), 2)))


def _is_customized() -> bool:
    return any(st.session_state.get(k) != v for k, v in DEFAULTS.items())


def _params_panel() -> PolicyParams:
    """Vẽ các slider (gọi bên trong expander) và trả về PolicyParams."""
    st.caption(
        "Đây là các giả định của mô hình. Nếu không chắc, cứ giữ mặc định. "
        f"Hai ràng buộc cố định: GMV bị ảnh hưởng tối đa {X:g}%, "
        f"tối đa {int(N)} seller/tháng."
    )

    st.markdown("**1. Ngưỡng điểm rủi ro theo hạng seller** (phương án *Điểm rủi ro dự báo*)")
    st.caption(
        "Seller có điểm rủi ro đơn xấu từ ngưỡng này trở lên bị xử lý. "
        "Ngưỡng càng thấp, càng nhiều seller bị xử lý."
    )
    c1, c2, c3 = st.columns(3)
    theta_1 = c1.slider("Hạng 1", 0.0, 1.0, key="p_theta_1", step=0.01,
                        help="Ngưỡng điểm rủi ro áp dụng cho seller hạng 1.")
    theta_2 = c2.slider("Hạng 2", 0.0, 1.0, key="p_theta_2", step=0.01,
                        help="Ngưỡng điểm rủi ro áp dụng cho seller hạng 2.")
    theta_3 = c3.slider("Hạng 3", 0.0, 1.0, key="p_theta_3", step=0.01,
                        help="Ngưỡng điểm rủi ro áp dụng cho seller hạng 3.")

    st.markdown("**2. Hiệu quả can thiệp** (% đơn xấu giảm được ở seller bị xử lý)")
    st.caption("Giả định mỗi lần can thiệp cải thiện được bao nhiêu phần trăm đơn xấu.")
    c1, c2, c3, c4 = st.columns(4)
    e1 = c1.slider("Hạng 1 (%)", 0, 100, key="p_e1", step=5,
                   help="Tỷ lệ đơn xấu giảm được khi xử lý seller hạng 1.")
    e2 = c2.slider("Hạng 2 (%)", 0, 100, key="p_e2", step=5,
                   help="Tỷ lệ đơn xấu giảm được khi xử lý seller hạng 2.")
    e3 = c3.slider("Hạng 3 (%)", 0, 100, key="p_e3", step=5,
                   help="Tỷ lệ đơn xấu giảm được khi xử lý seller hạng 3.")
    e_p1 = c4.slider("Ngưỡng KPI cố định (%)", 0, 100, key="p_e_p1", step=5,
                     help="Tỷ lệ đơn xấu giảm được khi xử lý theo phương án Ngưỡng KPI cố định.")

    st.markdown("**3. Ngưỡng KPI** (phương án *Ngưỡng KPI cố định*)")
    c1, c2 = st.columns(2)
    late_ship = c1.slider("Tỷ lệ bàn giao trễ tối đa (%)", 0, 100, key="p_late", step=1,
                          help="Seller có tỷ lệ bàn giao trễ vượt ngưỡng này bị xử lý.")
    avg_review = c2.slider("Điểm review trung bình tối thiểu", 1.0, 5.0, key="p_review", step=0.1,
                           help="Seller có điểm review trung bình thấp hơn ngưỡng này bị xử lý.")

    st.markdown("**4. Giả định thị trường**")
    c1, c2, c3 = st.columns(3)
    transfer = c1.slider("Đơn chuyển sang seller khác (%)", 0, 100, key="p_r", step=5,
                         help="Phần đơn của seller bị xử lý được chuyển sang seller khác.")
    season = c2.slider("Hệ số mùa vụ", 0.0, 2.0, key="p_s", step=0.05,
                       help="1.0 là mức bình thường. Trên 1.0 là mùa cao điểm, dưới 1.0 là mùa thấp điểm.")
    min_orders = c3.number_input("Số đơn tối thiểu để đánh giá seller", min_value=0, key="p_min_orders", step=1,
                                 help="Seller ít đơn hơn mức này không được đưa vào đánh giá.")

    st.button("Đặt lại về mặc định", on_click=_reset_params)

    return PolicyParams(
        theta_1=theta_1,
        theta_2=theta_2,
        theta_3=theta_3,
        e1=e1 / 100,
        e2=e2 / 100,
        e3=e3 / 100,
        e_p1=e_p1 / 100,
        late_ship_threshold=late_ship / 100,
        avg_review_threshold=avg_review,
        r=transfer / 100,
        s=season,
        min_orders=int(min_orders),
        x_limit=X,
        n_limit=N,
    )


# ---------------------------------------------------------------------------
# Hiển thị kết quả
# ---------------------------------------------------------------------------


def _fmt_pct(value) -> str:
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _ok_mark(ok) -> str:
    return "✓" if bool(ok) else "✗"


def _recommend(results):
    """Phương án (khác P0) đạt cả hai ràng buộc và giảm nhiều đơn xấu nhất."""
    valid = [r for r in results if r.policy_code != "P0" and r.meets_x and r.meets_n]
    if not valid:
        return None
    return min(valid, key=lambda r: r.expected_bad_orders)


def _render_conclusion(results) -> None:
    by_code = {r.policy_code: r for r in results}
    base = by_code.get("P0")
    best = _recommend(results)

    if best is None:
        st.warning(
            "Với giả định hiện tại, không có phương án nào vừa giảm đơn xấu vừa "
            f"giữ GMV bị ảnh hưởng ≤ {X:g}% và ≤ {int(N)} seller. "
            "Hãy thử điều chỉnh giả định hoặc xem mục *Ngưỡng gợi ý* bên dưới."
        )
    else:
        saved = (base.expected_bad_orders - best.expected_bad_orders) if base else None
        saved_txt = ""
        if saved is not None and base.expected_bad_orders:
            saved_txt = (
                f" giảm khoảng {saved:,.0f} đơn xấu "
                f"({saved / base.expected_bad_orders:.0%} so với không can thiệp),"
            )
        st.success(
            f"**Khuyến nghị: {_label(best.policy_code)}**{saved_txt} "
            f"GMV bị ảnh hưởng {_fmt_pct(best.gmv_affected_pct)} (tối đa {X:g}%), "
            f"{int(best.n_sellers_flagged)} seller bị xử lý (tối đa {int(N)})."
        )

    cols = st.columns(len(results))
    for col, item in zip(cols, results):
        with col, st.container(border=True):
            code = item.policy_code
            st.markdown(f"**{POLICY_NAMES.get(code, code)}** · `{code}`")
            st.caption(POLICY_DESC.get(code, ""))
            delta = None
            if base is not None and code != "P0":
                delta = f"{item.expected_bad_orders - base.expected_bad_orders:,.0f} so với P0"
            st.metric(
                "Đơn xấu dự kiến",
                f"{item.expected_bad_orders:,.0f}",
                delta=delta,
                delta_color="inverse",
            )
            st.write(
                f"{_ok_mark(item.meets_x)} GMV bị ảnh hưởng: "
                f"**{_fmt_pct(item.gmv_affected_pct)}** / tối đa {X:g}%"
            )
            st.write(
                f"{_ok_mark(item.meets_n)} Seller bị xử lý: "
                f"**{int(item.n_sellers_flagged)}** / tối đa {int(N)}"
            )
            if best is not None and code == best.policy_code:
                st.caption("⭐ Phương án được khuyến nghị")


def _render_goal_seek(scores: pd.DataFrame, params: PolicyParams):
    chosen, sought = goal_seek(scores, params)
    st.write(
        "Để giảm được nhiều đơn xấu nhất mà GMV bị ảnh hưởng vẫn trong "
        f"{X:g}%, nên dùng các ngưỡng điểm rủi ro: "
        f"**hạng 1 từ {chosen.theta_1:.2f}**, "
        f"hạng 2 từ {chosen.theta_2:.2f}, hạng 3 từ {chosen.theta_3:.2f}."
    )
    st.write(
        f"Kết quả với ngưỡng này: giảm còn **{sought.expected_bad_orders:,.0f}** đơn xấu dự kiến, "
        f"GMV bị ảnh hưởng {_fmt_pct(sought.gmv_affected_pct)}, "
        f"{int(sought.n_sellers_flagged)} seller bị xử lý."
    )
    st.button(
        "Dùng ngưỡng gợi ý này",
        on_click=_apply_suggestion,
        args=(chosen.theta_1, chosen.theta_2, chosen.theta_3),
        help="Áp các ngưỡng gợi ý vào phần Điều chỉnh giả định ở trên.",
    )
    st.caption("Ngưỡng được làm tròn 2 chữ số khi áp vào, nên kết quả có thể lệch rất nhẹ.")
    return chosen


def _flagged_view(flagged: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "seller_id",
        "tier",
        "p_bad",
        "gmv",
        "late_ship_rate",
        "avg_review",
        "n_orders_valid",
        "e_k",
    ]
    return flagged.loc[:, columns].sort_values("p_bad", ascending=False)


FLAGGED_LABELS = {
    "seller_id": "Seller",
    "tier": "Hạng",
    "p_bad": "Điểm rủi ro",
    "gmv": "GMV",
    "late_ship_rate": "Tỷ lệ bàn giao trễ",
    "avg_review": "Điểm review TB",
    "n_orders_valid": "Số đơn hợp lệ",
    "e_k": "Hiệu quả can thiệp",
}


# ---------------------------------------------------------------------------
# Ghi quyết định
# ---------------------------------------------------------------------------


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
    st.success(f"Đã ghi quyết định số {decision_id}.")


def _render_decision(scores: pd.DataFrame, params: PolicyParams, results) -> None:
    codes = [r.policy_code for r in results]
    best = _recommend(results)
    default_index = codes.index(best.policy_code) if best is not None and best.policy_code in codes else 0

    choice = st.radio(
        "Phương án chốt",
        codes,
        index=default_index,
        format_func=_label,
        horizontal=True,
    )
    result = simulate(scores, choice, params)
    meets_x = bool(getattr(result, "meets_x", True))
    meets_n = bool(getattr(result, "meets_n", True))
    violates = not (meets_x and meets_n)

    st.write(
        f"Đơn xấu dự kiến **{result.expected_bad_orders:,.0f}** · "
        f"GMV bị ảnh hưởng **{_fmt_pct(result.gmv_affected_pct)}** (tối đa {X:g}%) · "
        f"Seller bị xử lý **{int(result.n_sellers_flagged)}** (tối đa {int(N)})."
    )
    if violates:
        st.error(
            "Phương án này vượt ràng buộc "
            + ("GMV " if not meets_x else "")
            + ("và " if (not meets_x and not meets_n) else "")
            + ("số seller " if not meets_n else "")
            + "đã khóa. Nếu vẫn chốt, bắt buộc nhập lý do."
        )

    flagged = result.sellers[result.sellers["flagged"]].copy()
    view = _flagged_view(flagged)
    with st.expander(f"Danh sách {len(view)} seller bị xử lý", expanded=False):
        st.dataframe(
            view.rename(columns=FLAGGED_LABELS),
            width="stretch",
            hide_index=True,
        )
        st.download_button(
            "Tải CSV",
            view.to_csv(index=False).encode("utf-8"),
            file_name=f"flagged_sellers_{choice}.csv",
            mime="text/csv",
        )

    with st.form("decision_form"):
        note = st.text_area(
            "Lý do chọn phương án này" + (" (bắt buộc)" if violates else ""),
            "",
        )
        confirm = st.checkbox(
            f"Tôi xác nhận chốt **{_label(choice)}**: "
            f"GMV bị ảnh hưởng {_fmt_pct(result.gmv_affected_pct)}, "
            f"{int(result.n_sellers_flagged)} seller bị xử lý."
        )
        submitted = st.form_submit_button("Ghi quyết định")

    if submitted:
        if not confirm:
            st.warning("Hãy tích xác nhận trước khi ghi.")
        elif violates and not note.strip():
            st.warning("Phương án này vượt ràng buộc, hãy nhập lý do.")
        else:
            try:
                _insert(scores, choice, params, note)
            except Exception as exc:
                db.show_warehouse_error(exc)


# ---------------------------------------------------------------------------
# Trang chính
# ---------------------------------------------------------------------------


def render(settings=None) -> None:
    del settings
    from lib.ui import page_header

    page_header(
        "Chọn chính sách nào?",
        f"GMV bị ảnh hưởng tối đa {X:g}% và tối đa {int(N)} seller.",
        "Policy scenario – M2",
    )
    try:
        with st.spinner("Đang tải dữ liệu..."):
            scores = db.query(*queries.scores())
            snapshot = db.query(*queries.policy_snapshot())
    except Exception as exc:
        db.show_warehouse_error(exc)
        from lib.ui import next_step

        next_step("policy")
        return
    if scores.empty:
        from lib.insights import NOT_ENOUGH
        from lib.ui import insight_box, next_step

        insight_box(NOT_ENOUGH)
        next_step("policy")
        return

    _init_state()
    month = str(scores["as_of_month"].iloc[0])
    st.caption(f"Dữ liệu chốt tại tháng {month}.")

    # Khai báo vị trí các khối theo thứ tự hiển thị.
    conclusion_box = st.container()
    settings_box = st.expander("⚙️ Điều chỉnh giả định (nâng cao)", expanded=False)
    goal_box = st.container()
    trust_box = st.container()
    decide_box = st.container()

    # Slider phải chạy trước để có params; đặt trong expander ở giữa trang.
    with settings_box:
        params = _params_panel()
    results = compare_policies(scores, params)

    with conclusion_box:
        from lib.insights import build_insight_policy
        from lib.ui import insight_box

        insight_rows = pd.DataFrame(
            [
                {
                    "policy_code": item.policy_code,
                    "expected_bad_orders": item.expected_bad_orders,
                    "gmv_affected_pct": item.gmv_affected_pct,
                    "n_sellers_flagged": item.n_sellers_flagged,
                    "meets_x": item.meets_x,
                    "meets_n": item.meets_n,
                }
                for item in results
            ]
        )
        insight_box(build_insight_policy(insight_rows))
        st.subheader("1. Nên chọn phương án nào?")
        if _is_customized():
            st.info("Đang dùng giả định tùy chỉnh. Mở *Điều chỉnh giả định* để đặt lại về mặc định.")
        _render_conclusion(results)
        with st.expander("Kết quả chuẩn của job gần nhất (không đổi khi kéo slider)"):
            st.dataframe(snapshot, width="stretch")

    with goal_box:
        st.subheader("2. Ngưỡng nào tối ưu?")
        chosen = _render_goal_seek(scores, params)

    with trust_box:
        st.subheader("3. Kết quả này đáng tin đến đâu?")
        st.caption(
            "Khi mỗi giả định thay đổi ±20% quanh ngưỡng gợi ý ở mục 2, "
            "kết quả thay đổi bao nhiêu. Giả định nào làm kết quả đổi nhiều nhất "
            "thì cần được kiểm chứng kỹ nhất."
        )
        st.dataframe(tornado(scores, chosen), width="stretch")

    with decide_box:
        st.subheader("4. Chốt quyết định")
        _render_decision(scores, params, results)
    from lib.ui import next_step

    next_step("policy")