"""M2 screen. The model stays in src.dss.policy. This page only presents a decision."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db, queries
from lib.decisions import claim_decision, release_decision
from lib.insights import recommend_policy
from lib.labels import (
    COLUMN_LABELS,
    FACTOR_LABELS,
    POLICY_BLURB,
    POINT_COLUMNS,
    RATIO_COLUMNS,
    fmt_count,
    fmt_limit,
    fmt_number,
    fmt_percent_points,
    fmt_ratio,
    policy_name,
)
from lib.policy_cache import (
    cached_budget,
    cached_budget_curve,
    cached_compare,
    cached_tornado,
    cached_tornado_advice,
    param_token,
    score_token,
)
from lib.ui import (
    LATE,
    NAVY,
    add_legend_swatch,
    chart_note,
    fmt_brl,
    next_step,
    page_header,
    style_fig,
)
from src.dss.params import (
    AS_OF_MONTH,
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
from src.dss.policy import PolicyParams, efficiency, scenario_record, simulate

RECENT_LIMIT = 5
FLAGGED_PREVIEW = 50
ORIGIN_TEXT = {
    "default": "tham số mặc định",
    "custom": "tùy chỉnh",
    "suggested": "ngưỡng gợi ý",
}


def _default_applied() -> dict:
    return {
        "theta_1": float(THETA_1),
        "theta_2": float(THETA_2),
        "theta_3": float(THETA_3),
        "e1": float(E1),
        "e2": float(E2),
        "e3": float(E3),
        "e_p1": float(E_P1),
        "late_ship_threshold": float(LATE_SHIP_THRESHOLD),
        "avg_review_threshold": float(AVG_REVIEW_THRESHOLD),
        "r": float(R),
        "s": float(S),
        "min_orders": int(MIN_ORDERS),
    }


def _near(left, right) -> bool:
    if isinstance(left, int) and isinstance(right, int):
        return left == right
    return abs(float(left) - float(right)) < 1e-9


def _matches_default(applied: dict) -> bool:
    return all(_near(applied[key], value) for key, value in _default_applied().items())


def _sync_draft(applied: dict) -> None:
    st.session_state["draft_theta_1"] = float(applied["theta_1"])
    st.session_state["draft_theta_2"] = float(applied["theta_2"])
    st.session_state["draft_theta_3"] = float(applied["theta_3"])
    st.session_state["draft_e1"] = int(round(float(applied["e1"]) * 100))
    st.session_state["draft_e2"] = int(round(float(applied["e2"]) * 100))
    st.session_state["draft_e3"] = int(round(float(applied["e3"]) * 100))
    st.session_state["draft_e_p1"] = int(round(float(applied["e_p1"]) * 100))
    st.session_state["draft_late"] = int(round(float(applied["late_ship_threshold"]) * 100))
    st.session_state["draft_review"] = float(applied["avg_review_threshold"])
    st.session_state["draft_r"] = int(round(float(applied["r"]) * 100))
    st.session_state["draft_s"] = float(applied["s"])
    st.session_state["draft_min_orders"] = int(applied["min_orders"])


def _ensure_state() -> None:
    applied = st.session_state.get("applied")
    if not isinstance(applied, dict):
        applied = _default_applied()
        st.session_state["applied"] = applied
        st.session_state["param_origin"] = "default"
    if "draft_theta_1" not in st.session_state:
        _sync_draft(applied)


def _params_from(applied: dict) -> PolicyParams:
    return PolicyParams(
        theta_1=float(applied["theta_1"]),
        theta_2=float(applied["theta_2"]),
        theta_3=float(applied["theta_3"]),
        e1=float(applied["e1"]),
        e2=float(applied["e2"]),
        e3=float(applied["e3"]),
        e_p1=float(applied["e_p1"]),
        late_ship_threshold=float(applied["late_ship_threshold"]),
        avg_review_threshold=float(applied["avg_review_threshold"]),
        r=float(applied["r"]),
        s=float(applied["s"]),
        min_orders=int(applied["min_orders"]),
        x_limit=X,
        n_limit=N,
    )


def _store_applied(applied: dict, origin: str) -> None:
    st.session_state["applied"] = applied
    st.session_state["param_origin"] = "default" if _matches_default(applied) else origin
    _sync_draft(applied)


def _reset_params() -> None:
    _store_applied(_default_applied(), "default")


def _use_suggestion(theta_1: float, theta_2: float, theta_3: float) -> None:
    applied = dict(st.session_state.get("applied") or _default_applied())
    applied["theta_1"] = float(theta_1)
    applied["theta_2"] = float(theta_2)
    applied["theta_3"] = float(theta_3)
    _store_applied(applied, "suggested")


def _mark(ok: bool) -> str:
    return "✓" if ok else "✗"


def _bar(value, limit) -> None:
    if limit in (None, 0) or value is None or pd.isna(value):
        st.progress(0.0)
        return
    st.progress(min(1.0, max(0.0, float(value) / float(limit))))


def _results_frame(results) -> pd.DataFrame:
    return pd.DataFrame(
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


def _render_cards(results, recommended: str | None) -> None:
    by_code = {item.policy_code: item for item in results}
    base = by_code.get("P0")
    descriptions = {
        "P0": "Giữ nguyên, không xử lý seller nào (mốc so sánh).",
        "P1": "Xử lý seller có KPI quá khứ vượt ngưỡng cố định.",
        "P2": "Xử lý seller có xác suất đơn xấu dự báo vượt ngưỡng hạng.",
    }
    columns = st.columns(3)
    for column, item in zip(columns, results):
        with column, st.container(border=True, height="stretch"):
            title_line = f"**{policy_name(item.policy_code)}**"
            if item.policy_code == recommended:
                title_line += " :green-badge[Khuyến nghị]"
            st.markdown(title_line)
            st.caption(descriptions.get(item.policy_code, POLICY_BLURB.get(item.policy_code, "")))
            st.metric(
                COLUMN_LABELS["expected_bad_orders"],
                fmt_number(item.expected_bad_orders),
            )
            if base is None or item.policy_code == "P0":
                st.write("Đơn xấu giảm: —")
                st.write("Hiệu quả: —")
            else:
                reduced = base.expected_bad_orders - item.expected_bad_orders
                reduced_pct = (
                    reduced / base.expected_bad_orders
                    if base.expected_bad_orders > 0
                    else 0.0
                )
                st.write(f"Đơn xấu giảm: {fmt_number(reduced)} ({fmt_ratio(reduced_pct)})")
                eff = efficiency(item, base)
                eff_text = "—" if eff is None else f"{fmt_number(eff)} đơn / 1% GMV"
                st.write(f"Hiệu quả: {eff_text}")
            gmv_text = (
                f"{fmt_percent_points(item.gmv_affected_pct)} / tối đa {fmt_limit(X)}% "
                f"{_mark(item.meets_x)}"
            )
            st.write(f"{COLUMN_LABELS['gmv_affected_pct']}: {gmv_text}")
            _bar(item.gmv_affected_pct, X)
            seller_text = (
                f"{fmt_count(item.n_sellers_flagged)} / tối đa {fmt_limit(N)} "
                f"{_mark(item.meets_n)}"
            )
            st.write(f"{COLUMN_LABELS['n_sellers_flagged']}: {seller_text}")
            _bar(item.n_sellers_flagged, N)


def _format_table(frame: pd.DataFrame) -> pd.DataFrame:
    show = frame.copy()
    if "policy_code" in show.columns:
        show["policy_code"] = show["policy_code"].map(lambda code: policy_name(code))
    for column in RATIO_COLUMNS:
        if column in show.columns:
            show[column] = show[column].map(fmt_ratio)
    for column in POINT_COLUMNS:
        if column in show.columns:
            show[column] = show[column].map(fmt_percent_points)
    for column in ("n_sellers_flagged", "n_orders_valid", "n_limit", "min_orders"):
        if column in show.columns:
            show[column] = show[column].map(fmt_count)
    if "expected_bad_orders" in show.columns:
        show["expected_bad_orders"] = show["expected_bad_orders"].map(fmt_number)
    if "gmv" in show.columns:
        show["gmv"] = show["gmv"].map(fmt_brl)
    if "avg_review" in show.columns:
        show["avg_review"] = show["avg_review"].map(fmt_number)
    return show.rename(columns=COLUMN_LABELS)


def _budget_sentence(budget_res, baseline) -> str:
    chosen = budget_res.params
    sought = budget_res.scenario
    delta_bad = (
        baseline.expected_bad_orders - sought.expected_bad_orders
        if baseline is not None
        else 0.0
    )
    delta_pct = (
        delta_bad / baseline.expected_bad_orders
        if baseline is not None and baseline.expected_bad_orders > 0
        else 0.0
    )
    return (
        f"Ràng buộc đang bó là {budget_res.binding}. "
        f"Gắn cờ top {fmt_count(budget_res.k)} seller theo điểm rủi ro "
        f"(tương đương p_bad ≥ {fmt_ratio(chosen.theta_1)}) → "
        f"{fmt_number(sought.expected_bad_orders)} đơn xấu dự kiến, "
        f"giảm {fmt_number(delta_bad)} ({fmt_ratio(delta_pct)}) so với P0, "
        f"GMV ảnh hưởng {fmt_percent_points(sought.gmv_affected_pct)}."
    )


def _budget_curve_chart(curve: pd.DataFrame, p1_result, p2_result) -> None:
    if curve.empty:
        st.info("Chưa đủ seller đủ điều kiện để vẽ đường cong gắn cờ.")
        return
    figure = go.Figure(
        go.Scatter(
            x=curve["k"],
            y=curve["expected_bad_orders"],
            mode="lines",
            name="P2 theo top k seller",
            line=dict(color="#6d28d9", width=2.5),
            customdata=list(zip(curve["theta_1"], curve["gmv_affected_pct"])),
            hovertemplate=(
                "Top %{x} seller (p_bad ≥ %{customdata[0]:.1%})"
                "<br>Đơn xấu dự kiến: %{y:,.1f}"
                "<br>GMV ảnh hưởng: %{customdata[1]:.1f}%<extra></extra>"
            ),
        )
    )
    if p1_result is not None:
        figure.add_hline(
            y=p1_result.expected_bad_orders,
            line_dash="dash",
            line_color=LATE,
        )
        add_legend_swatch(
            figure,
            f"P1 ({fmt_count(p1_result.n_sellers_flagged)} seller)",
            LATE,
            dash="dash",
        )
    if p2_result is not None:
        figure.add_scatter(
            x=[p2_result.n_sellers_flagged],
            y=[p2_result.expected_bad_orders],
            mode="markers",
            name="Vị trí hiện tại (P2)",
            marker=dict(color=NAVY, size=11),
            hovertemplate=(
                "Vị trí hiện tại: %{x} seller"
                "<br>Đơn xấu dự kiến: %{y:,.1f}<extra></extra>"
            ),
        )
    figure.update_layout(height=360)
    figure.update_xaxes(title="Số seller gắn cờ")
    figure.update_yaxes(title="Đơn xấu dự kiến")
    st.plotly_chart(
        style_fig(
            figure,
            "Gắn cờ thêm seller giảm được bao nhiêu đơn xấu?",
            f"Top 1..{fmt_count(len(curve))} seller theo p_bad · tháng chấm {AS_OF_MONTH}",
        ),
        width="stretch",
    )
    chart_note(
        "Đường tím đi xuống cho thấy đơn xấu dự kiến giảm khi mở rộng top seller theo p_bad; "
        "điểm xanh đậm là cấu hình P2 hiện tại."
    )


def _tornado_chart(
    frame: pd.DataFrame,
    advice_stability: tuple[str | None, list[tuple[str, str, str | None]]] | None = None,
) -> None:
    controls, help_col = st.columns([6, 1], vertical_alignment="bottom")
    with controls:
        metric_choice = st.segmented_control(
            "Chỉ số đánh giá độ nhạy",
            ["Đơn xấu dự kiến", "GMV bị ảnh hưởng (%)"],
            default="Đơn xấu dự kiến",
            key="tornado_metric",
        )
    if metric_choice is None:
        metric_choice = "Đơn xấu dự kiến"
    with help_col:
        with st.popover("?"):
            st.markdown(
                "- Mỗi giả định được đẩy lệch ±20%, các giả định khác giữ nguyên.\n"
                "- Độ dài thanh = mức kết quả thay đổi; thanh càng dài, kết quả càng phụ thuộc giả định đó.\n"
                "- Hệ số mùa vụ nhân vào số đơn của mọi seller nên luôn dài nhất, nhưng làm P0/P1/P2 dịch cùng chiều nên không đổi phương án được chọn.\n"
                "- Hiệu quả can thiệp chỉ tác động lên seller bị gắn cờ, cần kiểm chứng bằng thí điểm.\n"
                "- Tỷ lệ chuyển đơn chỉ ảnh hưởng GMV, nên bằng 0 ở chế độ đơn xấu là đúng."
            )

    is_gmv = metric_choice == "GMV bị ảnh hưởng (%)"
    metric_col = "gmv_affected_pct" if is_gmv else "expected_bad_orders"
    rows = []
    for factor, part in frame.groupby("factor"):
        low = part.loc[part["shock"] == "low", metric_col]
        base = part.loc[part["shock"] == "base", metric_col]
        high = part.loc[part["shock"] == "high", metric_col]
        if low.empty or base.empty or high.empty:
            continue
        if pd.isna(low.iloc[0]) or pd.isna(base.iloc[0]) or pd.isna(high.iloc[0]):
            continue
        low_value = float(low.iloc[0])
        base_value = float(base.iloc[0])
        high_value = float(high.iloc[0])
        delta_low = low_value - base_value
        delta_high = high_value - base_value
        span = max(abs(delta_high - delta_low), abs(delta_low), abs(delta_high))
        rows.append(
            {
                "factor": factor,
                "label": FACTOR_LABELS.get(str(factor), str(factor)),
                "span": span,
                "delta_low": delta_low,
                "delta_high": delta_high,
                "low": low_value,
                "base": base_value,
                "high": high_value,
            }
        )
    if not rows:
        st.info("Chưa đủ dữ liệu để kết luận.")
        return

    ordered = sorted(rows, key=lambda row: row["span"])
    unit = "điểm %" if is_gmv else "đơn"
    figure = go.Figure()
    figure.add_bar(
        x=[row["delta_low"] for row in ordered],
        y=[row["label"] for row in ordered],
        orientation="h",
        name="Giảm 20%",
        marker_color=NAVY,
        customdata=[[fmt_number(row["low"]), fmt_number(row["base"])] for row in ordered],
        hovertemplate=(
            "%{y} (Giảm 20%)<br>Độ lệch: %{x:+.2f} " + unit
            + "<br>Kết quả mới: %{customdata[0]} (gốc %{customdata[1]})<extra></extra>"
        ),
    )
    figure.add_bar(
        x=[row["delta_high"] for row in ordered],
        y=[row["label"] for row in ordered],
        orientation="h",
        name="Tăng 20%",
        marker_color=LATE,
        customdata=[[fmt_number(row["high"]), fmt_number(row["base"])] for row in ordered],
        hovertemplate=(
            "%{y} (Tăng 20%)<br>Độ lệch: %{x:+.2f} " + unit
            + "<br>Kết quả mới: %{customdata[0]} (gốc %{customdata[1]})<extra></extra>"
        ),
    )
    figure.add_vline(x=0, line_color="#8a93a0", line_width=1)
    figure.update_layout(height=320, barmode="overlay", margin_l=160, margin_r=16, margin_b=16)
    x_title = (
        "Độ lệch GMV bị ảnh hưởng (điểm phần trăm)"
        if is_gmv
        else "Độ lệch đơn xấu dự kiến (đơn)"
    )
    figure.update_xaxes(title=x_title)
    figure.update_yaxes(title="Giả định", automargin=True)
    chart_title = (
        "Giả định nào làm GMV bị ảnh hưởng đổi nhiều nhất?"
        if is_gmv
        else "Giả định nào làm đơn xấu dự kiến đổi nhiều nhất?"
    )
    st.plotly_chart(
        style_fig(
            figure,
            chart_title,
            f"Lệch ±20% quanh ngưỡng gợi ý · tháng chấm {AS_OF_MONTH}",
        ),
        width="stretch",
    )
    chart_note("Thanh dài nhất là giả định nhạy nhất, nhưng chỉ đáng lo nếu nó làm đổi phương án được chọn.")

    if advice_stability is not None:
        base_code, changes = advice_stability
        if not changes:
            if base_code is None:
                st.write("Ở mọi mức lệch ±20%, vẫn chưa có phương án nào đạt cả hai trần.")
            else:
                st.write(f"Ở mọi mức lệch ±20%, phương án khuyến nghị vẫn là {base_code}.")
        else:
            factor, shock, new_code = changes[0]
            factor_name = FACTOR_LABELS.get(str(factor), str(factor))
            shock_text = "−20%" if shock == "low" else "+20%"
            target_text = new_code or "không có phương án đạt trần"
            st.write(
                f"{factor_name} ở {shock_text} làm khuyến nghị đổi sang {target_text}. "
                "Cần kiểm chứng giả định này trước."
            )


def _flagged_source(result) -> pd.DataFrame:
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
    flagged = result.sellers[result.sellers["flagged"]].copy()
    return flagged.loc[:, columns].sort_values("p_bad", ascending=False)


def _insert(scores: pd.DataFrame, choice: str, params: PolicyParams, note: str) -> str:
    if choice not in {"P0", "P1", "P2"}:
        raise ValueError("policy_code must be P0, P1, or P2")
    result = simulate(scores, choice, params)
    decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    record = scenario_record(result, params, str(scores["as_of_month"].iloc[0]), decided_at)
    decision_id = str(uuid4())
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
    db.query_recent.clear()
    return decision_id


@st.dialog("Xác nhận quyết định")
def _confirm_dialog() -> None:
    pending = st.session_state.get("pending_decision")
    if not pending:
        return
    st.write(f"**{policy_name(pending['choice'])}**")
    st.write(
        f"GMV bị ảnh hưởng {pending['gmv_text']}. "
        f"Số seller bị xử lý {pending['seller_text']}."
    )
    st.write(pending["param_text"])
    if pending["note"]:
        st.write(f"Lý do: {pending['note']}")
    if st.button("Ghi vào nhật ký", key="confirm_insert"):
        if not claim_decision(st.session_state, pending["token"]):
            st.warning("Lần bấm này đã được ghi hoặc đang ghi.")
            return
        try:
            decision_id = _insert(
                pending["scores"],
                pending["choice"],
                pending["params"],
                pending["note"],
            )
        except Exception as exc:
            st.session_state["last_decision_token"] = None
            release_decision(st.session_state)
            db.show_warehouse_error(exc)
            return
        release_decision(st.session_state)
        st.session_state["open_confirm"] = False
        st.session_state["last_saved_id"] = decision_id
        st.rerun()


def _render_decision(scores, params: PolicyParams, results, recommended: str | None) -> None:
    codes = [item.policy_code for item in results]
    signature = (param_token(params), recommended)
    if st.session_state.get("choice_signature") != signature:
        st.session_state["policy_choice"] = recommended if recommended in codes else codes[0]
        st.session_state["choice_signature"] = signature
    choice = st.radio(
        "Phương án chốt",
        codes,
        format_func=policy_name,
        horizontal=True,
        key="policy_choice",
    )
    result = simulate(scores, choice, params)
    violates = not (bool(result.meets_x) and bool(result.meets_n))
    if violates:
        st.error("Phương án này vượt trần. Hãy nhập lý do trước khi chốt.")
    note = st.text_area("Lý do chọn phương án này", key="decision_note")
    if st.button("Chốt"):
        if violates and not note.strip():
            st.error("Chưa ghi được vì phương án vượt ràng buộc mà chưa có lý do.")
        else:
            token = f"{choice}|{note.strip()}|{param_token(params)}|{scores['as_of_month'].iloc[0]}"
            st.session_state["pending_decision"] = {
                "scores": scores,
                "choice": choice,
                "params": params,
                "note": note.strip(),
                "token": token,
                "gmv_text": fmt_percent_points(result.gmv_affected_pct),
                "seller_text": fmt_count(result.n_sellers_flagged),
                "param_text": (
                    f"Ngưỡng hạng {fmt_ratio(params.theta_1)}, {fmt_ratio(params.theta_2)}, "
                    f"{fmt_ratio(params.theta_3)}. Hiệu quả can thiệp "
                    f"{fmt_ratio(params.e1)}, {fmt_ratio(params.e2)}, {fmt_ratio(params.e3)}, "
                    f"{fmt_ratio(params.e_p1)}."
                ),
            }
            st.session_state["open_confirm"] = True
    if st.session_state.get("open_confirm"):
        _confirm_dialog()
    if st.session_state.get("last_saved_id"):
        st.success("Đã ghi quyết định.")
        st.session_state["last_saved_id"] = None
    flagged = _flagged_source(result)
    preview = flagged.head(FLAGGED_PREVIEW)
    with st.expander(
        f"Danh sách seller bị xử lý ({fmt_count(len(preview))} / {fmt_count(len(flagged))})",
        expanded=False,
    ):
        st.dataframe(_format_table(preview), width="stretch", hide_index=True)
        st.download_button(
            "Tải CSV",
            flagged.to_csv(index=False).encode("utf-8"),
            file_name=f"flagged_sellers_{choice}.csv",
            mime="text/csv",
        )


def _assumptions_form() -> None:
    st.caption(
        f"GMV tối đa {fmt_limit(X)}% và số seller tối đa {fmt_limit(N)} đã khóa trong SPEC. "
        "Hai số này không chỉnh ở đây."
    )
    with st.form("assumptions"):
        st.markdown("**Ngưỡng điểm rủi ro theo hạng**")
        one, two, three = st.columns(3)
        theta_1 = one.slider(
            "Hạng 1", 0.0, 1.0, key="draft_theta_1", step=0.01,
            help="Điểm rủi ro để vào hạng 1. Hạ ngưỡng thì nhiều seller bị xử lý hơn.",
        )
        theta_2 = two.slider(
            "Hạng 2", 0.0, 1.0, key="draft_theta_2", step=0.01,
            help="Điểm rủi ro để vào hạng 2. Hạ ngưỡng thì nhiều seller lên hạng cao hơn.",
        )
        theta_3 = three.slider(
            "Hạng 3", 0.0, 1.0, key="draft_theta_3", step=0.01,
            help="Điểm rủi ro để vào hạng 3. Hạ ngưỡng thì nhiều seller vào hạng mạnh nhất.",
        )
        st.markdown("**Hiệu quả can thiệp**")
        one, two, three, four = st.columns(4)
        e1 = one.slider(
            "Hạng 1 (%)", 0, 100, key="draft_e1", step=5,
            help="Phần đơn xấu giảm khi xử lý hạng 1. Tăng hiệu quả thì đơn xấu dự kiến giảm.",
        )
        e2 = two.slider(
            "Hạng 2 (%)", 0, 100, key="draft_e2", step=5,
            help="Phần đơn xấu giảm khi xử lý hạng 2. Tăng hiệu quả thì đơn xấu dự kiến giảm.",
        )
        e3 = three.slider(
            "Hạng 3 (%)", 0, 100, key="draft_e3", step=5,
            help="Phần đơn xấu giảm khi xử lý hạng 3. Tăng hiệu quả thì đơn xấu dự kiến giảm.",
        )
        e_p1 = four.slider(
            "Ngưỡng KPI cố định (%)", 0, 100, key="draft_e_p1", step=5,
            help="Phần đơn xấu giảm khi xử lý theo ngưỡng KPI. Tăng hiệu quả thì đơn xấu dự kiến giảm.",
        )
        st.markdown("**Ngưỡng KPI của phương án Ngưỡng KPI cố định**")
        one, two = st.columns(2)
        late_ship = one.slider(
            "Tỷ lệ bàn giao trễ tối đa (%)", 0, 100, key="draft_late", step=1,
            help="Seller vượt tỷ lệ này bị xử lý. Hạ ngưỡng thì nhiều seller bị xử lý hơn.",
        )
        avg_review = two.slider(
            "Điểm review trung bình tối thiểu", 1.0, 5.0, key="draft_review", step=0.1,
            help="Seller dưới điểm này bị xử lý. Tăng ngưỡng thì nhiều seller bị xử lý hơn.",
        )
        st.markdown("**Giả định thị trường**")
        one, two, three = st.columns(3)
        transfer = one.slider(
            "Đơn chuyển sang seller khác (%)", 0, 100, key="draft_r", step=5,
            help="Phần đơn giữ lại được khi seller bị xử lý. Tăng tỷ lệ thì GMV bị ảnh hưởng giảm.",
        )
        season = two.slider(
            "Hệ số mùa vụ", 0.0, 2.0, key="draft_s", step=0.05,
            help="Nhân với số đơn kỳ vọng. Tăng hệ số thì đơn xấu dự kiến tăng.",
        )
        min_orders = three.number_input(
            "Số đơn tối thiểu để đánh giá seller",
            min_value=0,
            key="draft_min_orders",
            step=1,
            help="Seller ít đơn hơn mức này không được gắn cờ. Tăng mức thì ít seller bị xử lý hơn.",
        )
        apply = st.form_submit_button("Áp dụng")
    if apply:
        applied = {
            "theta_1": float(theta_1),
            "theta_2": float(theta_2),
            "theta_3": float(theta_3),
            "e1": float(e1) / 100,
            "e2": float(e2) / 100,
            "e3": float(e3) / 100,
            "e_p1": float(e_p1) / 100,
            "late_ship_threshold": float(late_ship) / 100,
            "avg_review_threshold": float(avg_review),
            "r": float(transfer) / 100,
            "s": float(season),
            "min_orders": int(min_orders),
        }
        _store_applied(applied, "custom")
        st.rerun()


def _recent() -> None:
    st.subheader("Quyết định gần đây")
    try:
        frame = db.query_recent(*queries.recent_decisions(RECENT_LIMIT))
    except Exception as exc:
        st.error(db.redact(exc))
        return
    if frame.empty:
        st.caption("Chưa có quyết định nào được ghi.")
        return
    st.dataframe(_format_table(frame), width="stretch", hide_index=True)


def _saved_orders(results, code: str | None):
    by_code = {item.policy_code: item for item in results}
    chosen = by_code.get(code)
    base = by_code.get("P0")
    if chosen is None or base is None:
        return chosen, None
    return chosen, base.expected_bad_orders - chosen.expected_bad_orders


def _decision_conclusion(results, advice: dict) -> str:
    chosen, saved = _saved_orders(results, advice.get("code"))
    if chosen is None:
        return advice.get("sentence") or "Chưa đủ dữ liệu để kết luận."
    by_code = {item.policy_code: item for item in results}
    base = by_code.get("P0")
    if saved is None:
        change = "chưa so được với P0"
    else:
        pct = (
            saved / base.expected_bad_orders
            if base is not None and base.expected_bad_orders > 0
            else 0.0
        )
        if saved >= 0:
            change = f"giảm {fmt_number(saved)} đơn xấu ({fmt_ratio(pct)})"
        else:
            change = f"tăng {fmt_number(abs(saved))} đơn xấu ({fmt_ratio(abs(pct))})"
    return (
        f"Khuyến nghị {chosen.policy_code}: "
        f"xử lý {fmt_count(chosen.n_sellers_flagged)} seller, "
        f"{change}, "
        f"đổi lại {fmt_percent_points(chosen.gmv_affected_pct)} GMV (trần {fmt_limit(X)}%)."
    )


def render(settings=None) -> None:
    del settings
    try:
        with st.spinner("Đang tải dữ liệu…"):
            scores = db.query(*queries.scores())
            snapshot = db.query(*queries.policy_snapshot())
    except Exception as exc:
        page_header("Chọn chính sách nào?", "Chưa tải được dữ liệu để kết luận.", "predicted")
        db.show_warehouse_error(exc)
        next_step("policy")
        return
    if scores.empty:
        page_header("Chọn chính sách nào?", "Chưa có điểm rủi ro cho kỳ này.", "predicted")
        next_step("policy")
        return
    scores = scores[scores["as_of_month"].astype(str) == AS_OF_MONTH].copy()
    if scores.empty:
        page_header("Chọn chính sách nào?", "Kỳ này chưa đủ dữ liệu để chấm.", "predicted")
        next_step("policy")
        return

    _ensure_state()
    applied = st.session_state["applied"]
    origin = st.session_state.get("param_origin", "default")
    params = _params_from(applied)
    token = score_token(scores)
    results = cached_compare(token, param_token(params))
    advice = recommend_policy(_results_frame(results), X, N)
    page_header("Chọn chính sách nào?", _decision_conclusion(results, advice), "predicted")
    month = str(scores["as_of_month"].iloc[0])
    n_scored = len(scores)
    n_eligible = int((pd.to_numeric(scores["n_orders_valid"], errors="coerce").fillna(0) >= int(params.min_orders)).sum())
    st.caption(
        f"Đang dùng: {ORIGIN_TEXT.get(origin, origin)} · "
        f"Tháng chấm {month} · tính trên {fmt_count(n_scored)} seller được chấm "
        f"({fmt_count(n_eligible)} seller ≥ {fmt_count(params.min_orders)} đơn đủ điều kiện gắn cờ; "
        f"s = {fmt_number(params.s)}). "
        f"Trần GMV {fmt_limit(X)}%, tối đa {fmt_limit(N)} seller."
    )

    _render_cards(results, advice["code"])

    st.markdown("**Xem lập luận**")
    goal_tab, trust_tab, assume_tab = st.tabs(
        ["Ngưỡng nào tối ưu", "Kết quả đáng tin đến đâu", "Giả định"],
    )
    budget_res = cached_budget(token, param_token(params))
    chosen = budget_res.params
    sought = budget_res.scenario
    by_code = {item.policy_code: item for item in results}
    p0_result = by_code.get("P0")
    p1_result = by_code.get("P1")
    p2_result = by_code.get("P2")
    with goal_tab:
        st.write(_budget_sentence(budget_res, p0_result))
        eff_p2 = efficiency(sought, p0_result) if p0_result is not None else None
        eff_p1 = efficiency(p1_result, p0_result) if p0_result is not None and p1_result is not None else None
        if eff_p2 is not None:
            eff_text = f"Hiệu quả biên P2 gợi ý: giảm {fmt_number(eff_p2)} đơn xấu / 1% GMV ảnh hưởng"
            if eff_p1 is not None:
                eff_text += f" (so với P1: {fmt_number(eff_p1)})."
            else:
                eff_text += "."
            st.caption(eff_text)
        st.button(
            "Dùng ngưỡng gợi ý này",
            on_click=_use_suggestion,
            args=(chosen.theta_1, chosen.theta_2, chosen.theta_3),
            help="Ghi ngưỡng gợi ý vào giả định và tính lại phần chốt quyết định.",
        )
        curve = cached_budget_curve(token, param_token(params))
        _budget_curve_chart(curve, p1_result, p2_result)
    with trust_tab:
        st.caption("Mỗi giả định lệch ±20% quanh ngưỡng gợi ý, không phải slider hiện tại.")
        shocks = cached_tornado(token, param_token(chosen))
        advice_stability = cached_tornado_advice(token, param_token(chosen))
        _tornado_chart(shocks, advice_stability)
        if st.toggle("Xem bảng", key="tornado_table"):
            table = shocks.copy()
            table["factor"] = table["factor"].map(lambda name: FACTOR_LABELS.get(str(name), str(name)))
            table["expected_bad_orders"] = table["expected_bad_orders"].map(fmt_number)
            table["gmv_affected_pct"] = table["gmv_affected_pct"].map(fmt_percent_points)
            table["n_sellers_flagged"] = table["n_sellers_flagged"].map(fmt_count)
            st.dataframe(table.rename(columns=COLUMN_LABELS), width="stretch", hide_index=True)
        with st.expander("Kết quả chuẩn của job gần nhất (không đổi khi chỉnh giả định)"):
            st.dataframe(_format_table(snapshot), width="stretch", hide_index=True)
    with assume_tab:
        st.button("Đặt lại về mặc định", on_click=_reset_params)
        _assumptions_form()

    st.markdown("**Chốt phương án**")
    with st.container(border=True):
        _render_decision(scores, params, results, advice["code"])

    _recent()
    next_step("policy")
