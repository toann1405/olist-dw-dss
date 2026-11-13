"""Seller risk page. Scores stay as written. Tier and expected orders come from M2."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db, queries
from lib.glossary import explain
from lib.labels import fmt_count, fmt_limit, fmt_number, fmt_percent_points, fmt_ratio
from lib.stats import pareto
from lib.ui import (
    LATE,
    MIN_N_DISPLAY,
    NAVY,
    REVIEW,
    add_legend_swatch,
    chart_note,
    fmt_brl,
    fmt_pct,
    kpi_card,
    next_step,
    page_header,
    style_fig,
)
from src.dss.params import AS_OF_MONTH, MIN_ORDERS, N, R, THETA_1, THETA_2, THETA_3, X
from src.dss.policy import PolicyParams, simulate
from src.dss.recommend import TIER_NAME, action_for_tier, percentile_above, reason_chips

PREDICTED = "#6d28d9"
MISSING = "Không có dữ liệu (seller không qua funnel)"


def _known(value) -> str:
    if value is None:
        return MISSING
    try:
        if pd.isna(value):
            return MISSING
    except TypeError:
        pass
    text = str(value).strip()
    if text == "" or text.lower() == "none":
        return MISSING
    return text


def _rate(top, bottom):
    if top is None or bottom is None or pd.isna(top) or pd.isna(bottom) or float(bottom) == 0:
        return None
    return float(top) / float(bottom)


def _attach(scores: pd.DataFrame, min_orders: int):
    """Add M2 columns. Numbers come from simulate, not a second formula."""
    params = PolicyParams(min_orders=int(min_orders))
    baseline = simulate(scores, "P0", params)
    result = simulate(scores, "P2", params)
    sellers = result.sellers
    out = scores.copy()
    out["tier"] = sellers["tier"].to_numpy()
    out["expected_bad"] = sellers["expected_bad_i"].to_numpy()
    out["flagged"] = sellers["flagged"].to_numpy()
    out["baseline_bad"] = baseline.sellers["expected_bad_i"].to_numpy()
    return out, result


def _kpi_numbers(scored: pd.DataFrame, eligible: pd.DataFrame, scenario) -> dict:
    """Card values from the P2 scenario on all scored sellers; eligibility gates flagging only."""
    flagged = (
        eligible[eligible["flagged"].astype(bool)]
        if not eligible.empty and "flagged" in eligible.columns
        else eligible.iloc[0:0]
    )
    counts = (
        pd.to_numeric(flagged["tier"], errors="coerce").fillna(0).astype(int).value_counts()
        if not flagged.empty
        else pd.Series(dtype=int)
    )
    baseline = float(pd.to_numeric(scored["baseline_bad"], errors="coerce").fillna(0).sum())
    flagged_baseline = float(pd.to_numeric(flagged["baseline_bad"], errors="coerce").fillna(0).sum())
    remaining = float(scenario.expected_bad_orders)
    return {
        "n_eligible": len(eligible),
        "n_scored": len(scored),
        "n_flagged": int(scenario.n_sellers_flagged),
        "tiers": {1: int(counts.get(1, 0)), 2: int(counts.get(2, 0)), 3: int(counts.get(3, 0))},
        "gmv_affected_pct": scenario.gmv_affected_pct,
        "meets_x": bool(scenario.meets_x),
        "baseline_bad": baseline,
        "flagged_share": None if baseline <= 0 else flagged_baseline / baseline,
        "p2_remaining": remaining,
        "p2_reduction": None if baseline <= 0 else (baseline - remaining) / baseline,
    }


def _forecast_month(as_of: str) -> str | None:
    """Month after the scoring month. M1 estimates that next month."""
    parts = str(as_of).split("-")
    if len(parts) != 2:
        return None
    try:
        year = int(parts[0])
        month = int(parts[1])
    except ValueError:
        return None
    if month < 1 or month > 12:
        return None
    month += 1
    if month == 13:
        year += 1
        month = 1
    return f"{year:04d}-{month:02d}"


def _flag_sentence(eligible: pd.DataFrame, scored: pd.DataFrame | None = None) -> str:
    if eligible.empty:
        return "Chưa đủ dữ liệu để kết luận."
    horizon = _forecast_month(AS_OF_MONTH) or "tới"
    when = f"Tháng {horizon}" if horizon != "tới" else "Tháng tới"
    flagged = eligible[eligible["flagged"].astype(bool)] if "flagged" in eligible.columns else eligible.iloc[0:0]
    total_eligible = len(eligible)
    n_flagged = len(flagged)
    if n_flagged == 0:
        return (
            f"{when} dự kiến không có seller nào vượt ngưỡng rủi ro (chính sách P2) "
            f"trong {fmt_count(total_eligible)} seller đủ điều kiện."
        )
    pool = scored if scored is not None and not scored.empty else eligible
    total_bad = float(pd.to_numeric(pool["baseline_bad"], errors="coerce").fillna(0).sum())
    flagged_bad = float(pd.to_numeric(flagged["baseline_bad"], errors="coerce").fillna(0).sum())
    share = None if total_bad <= 0 else flagged_bad / total_bad
    share_text = "" if share is None else f", gom khoảng {fmt_ratio(share)} tổng đơn xấu dự kiến"
    return (
        f"{when} dự kiến có {fmt_count(n_flagged)}/{fmt_count(total_eligible)} seller "
        f"vượt ngưỡng rủi ro (chính sách P2){share_text}; "
        "xem danh sách bên dưới để chọn seller cần xử lý."
    )


def _summary(scored: pd.DataFrame, eligible: pd.DataFrame, scenario, min_orders: int) -> None:
    stats = _kpi_numbers(scored, eligible, scenario)
    watch, warn, halt = stats["tiers"][1], stats["tiers"][2], stats["tiers"][3]
    gmv_ok = "Đạt ✓" if stats["meets_x"] else "Vượt trần ✗"
    cards = [
        (
            "Seller đủ điều kiện xét",
            f"{fmt_count(stats['n_eligible'])} / {fmt_count(stats['n_scored'])}",
            None,
            (
                f"Seller có ít nhất {fmt_count(min_orders)} đơn hợp lệ trong tháng chấm; "
                "seller ít đơn có xác suất dao động mạnh nên không xét."
            ),
        ),
        (
            "Seller bị gắn cờ",
            fmt_count(stats["n_flagged"]),
            f"Theo dõi {fmt_count(watch)} · Cảnh báo {fmt_count(warn)} · Tạm ngưng {fmt_count(halt)}",
            (
                f"Seller có xác suất đơn xấu ≥ {fmt_ratio(THETA_1)} (hạng 1 trở lên theo P2), "
                f"tối đa {fmt_limit(N)} seller."
            ),
        ),
        (
            "GMV bị ảnh hưởng",
            fmt_percent_points(stats["gmv_affected_pct"]),
            f"Trần {fmt_limit(X)}% · {gmv_ok}",
            (
                "Phần GMV có thể mất khi xử lý seller bị gắn cờ, "
                f"giả định {float(R) * 100:.0f}% đơn chuyển sang seller khác, chia cho tổng GMV. "
                f"Không được vượt {fmt_limit(X)}%."
            ),
        ),
        (
            "Đơn xấu dự kiến (chưa can thiệp)",
            fmt_number(stats["baseline_bad"]),
            None
            if stats["flagged_share"] is None
            else f"Seller bị gắn cờ chiếm {fmt_ratio(stats['flagged_share'])}",
            (
                f"Tổng xác suất đơn xấu × số đơn trên toàn bộ {fmt_count(stats['n_scored'])} seller được chấm "
                f"(cùng phạm vi P0 ở trang Chính sách), trước khi áp dụng chính sách."
            ),
        ),
    ]
    columns = st.columns(4)
    for column, (label, value, caption, help_text) in zip(columns, cards):
        with column, st.container(border=True, height="stretch"):
            kpi_card(label, value, help=help_text, border=False)
            if caption:
                st.caption(caption)


def _list_tab(eligible: pd.DataFrame) -> None:
    if eligible.empty:
        st.info("Không có seller nào thỏa điều kiện, thử hạ số đơn tối thiểu.")
        return
    work = eligible.copy()
    regions = ["Tất cả"] + sorted(work["region_name"].dropna().astype(str).unique())
    tier_names = ["Tất cả"] + [
        TIER_NAME.get(int(item), str(item))
        for item in sorted(pd.to_numeric(work["tier"], errors="coerce").dropna().astype(int).unique())
    ]
    if st.session_state.get("risk_region") not in regions:
        st.session_state["risk_region"] = "Tất cả"
    if st.session_state.get("risk_tier") not in tier_names:
        st.session_state["risk_tier"] = "Tất cả"
    one, two, three, four = st.columns(4, vertical_alignment="bottom")
    region = one.selectbox("Vùng", regions, key="risk_region")
    tier = two.selectbox("Hạng", tier_names, key="risk_tier")
    top_n = three.number_input("Top N", min_value=1, value=int(N), step=1, key="risk_top")
    needle = four.text_input("Tìm seller", key="risk_search")
    if region != "Tất cả":
        work = work[work["region_name"].astype(str) == region]
    if tier != "Tất cả":
        work = work[work["tier"].map(lambda item: TIER_NAME.get(int(item), str(item))) == tier]
    if needle.strip():
        work = work[work["seller_id"].astype(str).str.contains(needle.strip(), case=False)]
    work = work.sort_values("p_bad", ascending=False).head(int(top_n))
    show = work.copy()
    show.insert(0, "rank", range(1, len(show) + 1))
    show["seller_short"] = show["seller_id"].astype(str).str.slice(0, 8)
    show["tier_name"] = show["tier"].map(lambda item: TIER_NAME.get(int(item), str(item)))
    show["small"] = pd.to_numeric(show["n_orders_valid"], errors="coerce").fillna(0) < MIN_N_DISPLAY
    view = pd.DataFrame(
        {
            "Thứ hạng": show["rank"],
            "Seller": show["seller_short"],
            "seller_id": show["seller_id"],
            "Hạng": show["tier_name"],
            "Xác suất đơn xấu": pd.to_numeric(show["p_bad"], errors="coerce"),
            "Số đơn hợp lệ": pd.to_numeric(show["n_orders_valid"], errors="coerce"),
            "GMV": show["gmv"].map(fmt_brl),
            "Bàn giao trễ": show["late_ship_rate"].map(fmt_ratio),
            "Review TB": show["avg_review"].map(fmt_number),
            "Vùng": show["region_name"],
            "Bang": show["state_code"],
            f"Ít đơn (<{MIN_N_DISPLAY})": show["small"].map(lambda flag: "⚠" if flag else ""),
        }
    )
    event = st.dataframe(
        view,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Xác suất đơn xấu": st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent"),
            "seller_id": None,
        },
        key="risk_grid",
    )
    selected = event.selection.rows if event is not None else []
    if selected:
        st.session_state["risk_seller_id"] = str(view.iloc[selected[0]]["seller_id"])
        st.caption("Đã chọn seller. Mở tab Chi tiết seller.")
    st.download_button(
        "Tải CSV",
        work.to_csv(index=False).encode("utf-8"),
        file_name="seller_risk.csv",
        mime="text/csv",
    )


def _distribution(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("Chưa đủ dữ liệu để kết luận.")
        return
    figure = go.Figure(
        go.Histogram(
            x=pd.to_numeric(frame["p_bad"], errors="coerce"),
            nbinsx=20,
            name="Số seller",
            marker_color=PREDICTED,
        )
    )
    for value, name in ((THETA_1, "Ngưỡng hạng 1"), (THETA_2, "Ngưỡng hạng 2"), (THETA_3, "Ngưỡng hạng 3")):
        figure.add_vline(x=float(value), line_dash="dash", line_color=PREDICTED, annotation_text=name)
        add_legend_swatch(figure, name, PREDICTED, dash="dash")
    figure.update_layout(height=340)
    figure.update_xaxes(title="Xác suất đơn xấu (%)", tickformat=".0%")
    figure.update_yaxes(title="Số seller")
    st.plotly_chart(
        style_fig(figure, "Xác suất đơn xấu của seller phân bố thế nào?", f"Tháng chấm {AS_OF_MONTH}"),
        width="stretch",
    )
    chart_note("Cột dồn về bên phải là seller đáng lo hơn; đường đứt là ngưỡng từng hạng.")
    ranked = pareto(frame, "baseline_bad")
    n_flagged = int(frame["flagged"].astype(bool).sum()) if "flagged" in frame.columns else 0
    mark = ranked[ranked["sellers"] == n_flagged] if n_flagged else ranked.iloc[0:0]
    figure = go.Figure(go.Scatter(
        x=ranked["seller_share"],
        y=ranked["bad_share"],
        name="Đơn xấu dự kiến cộng dồn (%)",
        mode="lines",
        line=dict(color=PREDICTED, dash="dash"),
    ))
    if not mark.empty:
        figure.add_scatter(
            x=mark["seller_share"],
            y=mark["bad_share"],
            mode="markers",
            marker=dict(color=PREDICTED, size=12),
            name=f"{fmt_count(n_flagged)} seller bị gắn cờ",
        )
    figure.update_layout(height=340)
    figure.update_xaxes(tickformat=".0%", title="Seller, tệ nhất trước (%)")
    figure.update_yaxes(tickformat=".0%", title="Đơn xấu dự kiến cộng dồn (%)")
    st.plotly_chart(
        style_fig(
            figure,
            "Đơn xấu dự kiến dồn vào ít seller hay trải đều?",
            f"Tháng chấm {AS_OF_MONTH}",
        ),
        width="stretch",
    )
    chart_note("Đường dốc lên sớm nghĩa là xử lý ít seller đã gom được nhiều đơn xấu dự kiến.")
    plot = frame.copy()
    plot["gmv_plot"] = pd.to_numeric(plot["gmv"], errors="coerce").clip(lower=1)
    median_gmv = float(plot["gmv_plot"].median())
    figure = go.Figure(go.Scatter(
        x=plot["gmv_plot"],
        y=pd.to_numeric(plot["p_bad"], errors="coerce"),
        name="Seller",
        mode="markers",
        text=plot["seller_id"].astype(str).str.slice(0, 8),
        marker=dict(size=8, color=PREDICTED, opacity=0.75),
    ))
    figure.add_vline(x=median_gmv, line_dash="dot", line_color=PREDICTED, annotation_text="GMV trung vị")
    figure.add_hline(y=float(THETA_1), line_dash="dot", line_color=PREDICTED, annotation_text="Ngưỡng gắn cờ")
    add_legend_swatch(figure, "GMV trung vị", PREDICTED, dash="dot")
    add_legend_swatch(figure, "Ngưỡng gắn cờ", PREDICTED, dash="dot")
    figure.update_layout(height=440)
    figure.update_xaxes(type="log", title="GMV (R$)")
    figure.update_yaxes(title="Xác suất đơn xấu (%)", tickformat=".0%")
    st.plotly_chart(
        style_fig(
            figure,
            "Seller nào vừa rủi ro cao vừa chiếm nhiều GMV?",
            f"Tháng chấm {AS_OF_MONTH}",
        ),
        width="stretch",
    )
    chart_note("Góc trên-trái là seller rủi ro cao mà GMV còn thấp, dễ xử lý hơn góc trên-phải.")


def _detail(seller_id: str, frame: pd.DataFrame, platform: pd.Series | None) -> None:
    match = frame[frame["seller_id"].astype(str) == str(seller_id)]
    if match.empty:
        st.info("Chỉ xem seller đã được chấm trong kỳ này.")
        return
    row = match.iloc[0]
    as_of = str(row.get("as_of_month") or AS_OF_MONTH)
    seller_short = str(seller_id)[:8]

    def _clean_text(value) -> str | None:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except TypeError:
            pass
        text = str(value).strip()
        if text == "" or text.lower() in {"none", "unknown", "nan"}:
            return None
        return text

    def _contrib_label(feature: str, value) -> str:
        name = str(feature)
        if name.startswith(("Vùng:", "Nhóm hàng:")):
            return name
        if value is None or pd.isna(value):
            return name
        lower = name.lower()
        if "tỷ lệ" in lower or "rate" in lower:
            return f"{name}: {fmt_ratio(value)}"
        if name in {"Số đơn hợp lệ", "Tuổi seller (ngày)"}:
            return f"{name}: {fmt_count(value)}"
        return f"{name}: {fmt_number(value)}"

    try:
        categories = db.query(*queries.seller_categories(seller_id, as_of))
    except Exception as exc:
        st.error(db.redact(exc))
        categories = pd.DataFrame()
    valid_cats = pd.DataFrame()
    main_cat: str | None = None
    main_share: float | None = None
    if not categories.empty and "gmv" in categories.columns:
        cats = categories.copy()
        cats["gmv_num"] = pd.to_numeric(cats["gmv"], errors="coerce").fillna(0.0)
        cats = cats[cats["gmv_num"] > 0].sort_values("gmv_num", ascending=False)
        total_cat_gmv = float(cats["gmv_num"].sum())
        if total_cat_gmv > 0 and not cats.empty:
            cats["share"] = cats["gmv_num"] / total_cat_gmv
            valid_cats = cats
            main_cat = str(cats.iloc[0]["category_group"])
            main_share = float(cats.iloc[0]["share"])

    try:
        history = db.query(*queries.seller_history(seller_id))
    except Exception as exc:
        st.error(db.redact(exc))
        history = pd.DataFrame()

    try:
        contrib = db.query(*queries.risk_contrib(seller_id, as_of))
    except Exception:
        contrib = pd.DataFrame()

    # 0. Kết luận
    p_bad_num = None if row.get("p_bad") is None or pd.isna(row.get("p_bad")) else float(row["p_bad"])
    p_series = pd.to_numeric(frame["p_bad"], errors="coerce").dropna()
    share = percentile_above(p_series.tolist(), p_bad_num) if p_bad_num is not None else None
    rank_pos = int((p_series > p_bad_num).sum()) + 1 if p_bad_num is not None and not p_series.empty else None
    top_pct = None if rank_pos is None else rank_pos / len(p_series)

    tier_val = int(row["tier"]) if row.get("tier") is not None and not pd.isna(row.get("tier")) else 0
    is_flagged = (
        bool(row["flagged"])
        if row.get("flagged") is not None and not pd.isna(row.get("flagged"))
        else (tier_val >= 1)
    )
    state_label = _clean_text(row.get("state_code")) or "chưa rõ bang"
    cat_label = main_cat or "chưa rõ danh mục"
    higher = fmt_pct(share) if share is not None else "—"
    st.markdown(
        f"**Seller {seller_short} ({state_label}, {cat_label}) dự kiến ~{fmt_pct(p_bad_num)} đơn tháng tới là đơn xấu, "
        f"cao hơn {higher} seller đang xét.**"
    )
    if is_flagged and tier_val >= 1:
        tier_label = TIER_NAME.get(tier_val, str(tier_val))
        st.write(f"Bị gắn cờ · {tier_label} · gợi ý: {action_for_tier(tier_val)}.")
    elif p_bad_num is not None and p_bad_num < float(THETA_1):
        st.write(f"Chưa gắn cờ vì {fmt_pct(p_bad_num)} < ngưỡng θ1 = {fmt_pct(THETA_1)}.")
    else:
        st.write(f"Chưa gắn cờ (ngoài top {fmt_limit(N)} seller theo giới hạn chính sách P2).")

    baseline_bad_val = None
    if "baseline_bad" in row.index and row.get("baseline_bad") is not None and not pd.isna(row.get("baseline_bad")):
        baseline_bad_val = float(row["baseline_bad"])
    elif p_bad_num is not None and row.get("n_orders_valid") is not None and not pd.isna(row.get("n_orders_valid")):
        baseline_bad_val = p_bad_num * float(row["n_orders_valid"])

    summary_cards = [
        ("Xác suất đơn xấu", fmt_pct(p_bad_num), explain("risk_score")),
        (
            "Thứ hạng rủi ro",
            f"Top {fmt_pct(top_pct)}" if top_pct is not None else "—",
            (
                f"Xếp thứ {fmt_count(rank_pos)}/{fmt_count(len(p_series))} seller đủ điều kiện (cao hơn {higher} seller)."
                if rank_pos is not None
                else "Vị trí theo xác suất đơn xấu trong nhóm seller đủ điều kiện."
            ),
        ),
        (
            "Trạng thái",
            "Gắn cờ" if is_flagged else "Chưa",
            (
                f"Theo chính sách P2 (ngưỡng θ1 = {fmt_pct(THETA_1)}, tối đa {fmt_limit(N)} seller)."
                + (f" Hạng hiện tại: {TIER_NAME.get(tier_val, str(tier_val))}." if is_flagged else "")
            ),
        ),
        (
            "Đơn xấu dự kiến",
            fmt_number(baseline_bad_val),
            "Số đơn xấu ước tính tháng tới khi chưa can thiệp = xác suất đơn xấu × số đơn hợp lệ.",
        ),
    ]
    summary_cols = st.columns(4)
    for column, (label, value, help_text) in zip(summary_cols, summary_cards):
        with column, st.container(border=True, height="stretch"):
            kpi_card(label, value, help=help_text, border=False)

    # ① Vì sao mô hình đánh giá vậy
    st.subheader("① Vì sao mô hình đánh giá vậy")
    if contrib.empty:
        st.caption("Chưa có kết quả đánh giá cho kỳ này.")
    else:
        work_contrib = contrib.copy()
        work_contrib["val_num"] = pd.to_numeric(work_contrib["value"], errors="coerce")
        work_contrib["contrib_num"] = pd.to_numeric(work_contrib["contribution"], errors="coerce")
        work_contrib = work_contrib.dropna(subset=["contrib_num"])
        is_onehot = work_contrib["feature"].astype(str).str.startswith(("Vùng:", "Nhóm hàng:"))
        work_contrib = work_contrib[~(is_onehot & (work_contrib["val_num"].fillna(0.0) == 0.0))].copy()
        if work_contrib.empty:
            st.caption("Chưa có kết quả đánh giá cho kỳ này.")
        else:
            work_contrib["y_label"] = [
                _contrib_label(feat, val)
                for feat, val in zip(work_contrib["feature"], work_contrib["val_num"])
            ]
            pos_rows = work_contrib[work_contrib["contrib_num"] > 0].sort_values("contrib_num", ascending=False)
            neg_rows = work_contrib[work_contrib["contrib_num"] < 0].sort_values("contrib_num", ascending=True)
            top_pos = pos_rows.iloc[0]["y_label"] if not pos_rows.empty else "không có"
            top_neg = neg_rows.iloc[0]["y_label"] if not neg_rows.empty else "không có"
            st.write(f"Yếu tố đẩy rủi ro lên nhiều nhất: {top_pos}; kéo xuống nhiều nhất: {top_neg}.")

            work_contrib["abs_contrib"] = work_contrib["contrib_num"].abs()
            top_contrib = (
                work_contrib.sort_values("abs_contrib", ascending=False)
                .head(6)
                .sort_values("abs_contrib", ascending=True)
            )
            bar_colors = [
                "#dc2626" if val > 0 else ("#16a34a" if val < 0 else "#8a93a0")
                for val in top_contrib["contrib_num"]
            ]
            figure = go.Figure(
                go.Bar(
                    x=top_contrib["contrib_num"],
                    y=top_contrib["y_label"],
                    orientation="h",
                    marker_color=bar_colors,
                    showlegend=False,
                    hovertemplate="%{y}<br>Tác động: %{x:+.3f}<extra></extra>",
                )
            )
            figure.add_vline(x=0, line_color="#8a93a0", line_width=1)
            add_legend_swatch(figure, "Tăng rủi ro", "#dc2626")
            add_legend_swatch(figure, "Giảm rủi ro", "#16a34a")
            figure.update_layout(height=max(240, 34 * len(top_contrib) + 90), margin_l=140, margin_b=12)
            figure.update_xaxes(title="Tác động lên rủi ro")
            figure.update_yaxes(title="Yếu tố", automargin=True)
            st.plotly_chart(
                style_fig(
                    figure,
                    "Yếu tố nào đẩy xác suất đơn xấu của seller này?",
                    f"Tháng chấm {as_of} · seller {seller_short}",
                ),
                width="stretch",
            )
            chart_note("Thanh đỏ làm tăng rủi ro, thanh xanh làm giảm rủi ro (log-odds, so với seller trung bình).")

    # ② Hiệu suất thực tế
    st.subheader("② Hiệu suất thực tế")
    actual_cards = [
        (f"GMV ({as_of})", fmt_brl(row["gmv"])),
        (f"Số đơn hợp lệ ({as_of})", fmt_count(row["n_orders_valid"])),
        (f"Bàn giao trễ ({as_of})", fmt_ratio(row["late_ship_rate"])),
        (f"Review TB ({as_of})", fmt_number(row["avg_review"])),
    ]
    actual_cols = st.columns(4)
    for column, (label, value) in zip(actual_cols, actual_cards):
        with column, st.container(border=True, height="stretch"):
            kpi_card(label, value, border=False)

    active_months = 0
    if not history.empty and "n_orders_valid" in history.columns:
        active_months = int((pd.to_numeric(history["n_orders_valid"], errors="coerce").fillna(0) > 0).sum())

    platform_late = (
        None if platform is None else _rate(platform.get("late_ship_count"), platform.get("late_ship_eligible"))
    )
    platform_neg_review = (
        None
        if platform is None
        else _rate(platform.get("negative_review_count"), platform.get("negative_review_eligible"))
    )
    platform_avg_review = (
        None if platform is None else _rate(platform.get("review_score_sum"), platform.get("review_count"))
    )

    caption_parts = [f"Số tháng có đơn: {fmt_count(active_months)}"]
    if platform_late is not None and row.get("late_ship_rate") is not None and not pd.isna(row["late_ship_rate"]):
        diff = float(row["late_ship_rate"]) - float(platform_late)
        if diff < -1e-9:
            caption_parts.append(f"Bàn giao trễ thấp hơn sàn {fmt_number(abs(diff) * 100)} điểm % (tốt)")
        elif diff > 1e-9:
            caption_parts.append(f"Bàn giao trễ cao hơn sàn {fmt_number(abs(diff) * 100)} điểm % (xấu)")
        else:
            caption_parts.append("Bàn giao trễ ngang mức sàn")
    st.caption(" · ".join(caption_parts) + ".")

    chips = reason_chips(row.get("late_ship_rate"), row.get("avg_review"), platform_late, platform_avg_review)
    if chips:
        with st.container(horizontal=True):
            for chip_text in chips:
                st.badge(chip_text, color="orange")

    hist = history.copy() if not history.empty else pd.DataFrame()
    if not hist.empty and "year_month" in hist.columns:
        hist = hist[hist["year_month"].astype(str).str.match(r"^\d{4}-\d{2}$")].copy()
    if hist.empty:
        st.info("Chưa có dữ liệu lịch sử theo tháng.")
    else:
        hist = hist.sort_values("year_month")
        first_ym = str(hist["year_month"].iloc[0])
        last_ym = str(hist["year_month"].iloc[-1])
        all_months = pd.period_range(first_ym, last_ym, freq="M").astype(str)
        hist = hist.set_index("year_month").reindex(all_months).reset_index().rename(columns={"index": "year_month"})

        orders_num = pd.to_numeric(hist["n_orders_valid"], errors="coerce")
        orders_plot = []
        late_rates = []
        neg_review_rates = []
        for idx in range(len(hist)):
            n_ord = orders_num.iloc[idx]
            if pd.isna(n_ord) or float(n_ord) <= 0:
                orders_plot.append(float("nan"))
                late_rates.append(float("nan"))
                neg_review_rates.append(float("nan"))
            else:
                orders_plot.append(float(n_ord))
                lr = _rate(hist["late_ship_count"].iloc[idx], hist["late_ship_eligible"].iloc[idx])
                nr = _rate(hist["negative_review_count"].iloc[idx], hist["negative_review_eligible"].iloc[idx])
                late_rates.append(float("nan") if lr is None else lr)
                neg_review_rates.append(float("nan") if nr is None else nr)

        figure = go.Figure()
        figure.add_bar(
            x=hist["year_month"],
            y=orders_plot,
            name="Số đơn hợp lệ",
            marker_color="#c5cdd6",
            opacity=0.55,
            yaxis="y2",
            hovertemplate="Tháng %{x}<br>Số đơn hợp lệ: %{y:,.0f}<extra></extra>",
        )
        figure.add_scatter(
            x=hist["year_month"],
            y=late_rates,
            name="Bàn giao trễ (%)",
            mode="lines+markers",
            line=dict(color=LATE, width=2),
            marker=dict(color=LATE, size=7),
            connectgaps=False,
            hovertemplate="Tháng %{x}<br>Bàn giao trễ: %{y:.1%}<extra></extra>",
        )
        figure.add_scatter(
            x=hist["year_month"],
            y=neg_review_rates,
            name="Review tiêu cực (%)",
            mode="lines+markers",
            line=dict(color=REVIEW, width=2),
            marker=dict(color=REVIEW, size=7),
            connectgaps=False,
            hovertemplate="Tháng %{x}<br>Review tiêu cực: %{y:.1%}<extra></extra>",
        )
        if platform_late is not None:
            figure.add_hline(y=platform_late, line_dash="dash", line_color=LATE)
            add_legend_swatch(figure, "TB sàn (bàn giao trễ)", LATE, dash="dash")
        if platform_neg_review is not None:
            figure.add_hline(y=platform_neg_review, line_dash="dot", line_color=REVIEW)
            add_legend_swatch(figure, "TB sàn (review tiêu cực)", REVIEW, dash="dot")
        figure.update_layout(
            height=360,
            yaxis=dict(title="Tỷ lệ (%)", tickformat=".0%", rangemode="tozero"),
            yaxis2=dict(
                title="Số đơn hợp lệ",
                overlaying="y",
                side="right",
                showgrid=False,
                rangemode="tozero",
            ),
            hovermode="x unified",
            barmode="overlay",
        )
        figure.update_xaxes(title="Tháng", type="category")
        st.plotly_chart(
            style_fig(
                figure,
                "Hiệu suất theo tháng của seller so với sàn thế nào?",
                f"{first_ym} → {last_ym} · seller {seller_short}",
            ),
            width="stretch",
        )
        chart_note("Cột xám là số đơn hợp lệ (trục phải); tháng không có đơn được để trống; đường đứt/chấm là trung bình toàn sàn kỳ chấm.")

    # ③ Nếu áp dụng chính sách
    st.subheader("③ Nếu áp dụng chính sách")
    tier_action = action_for_tier(tier_val)
    if tier_val == 0:
        st.write(
            f"Theo chính sách P2, seller ở trạng thái {tier_action} (chưa vượt ngưỡng gắn cờ θ1 = {fmt_pct(THETA_1)}), "
            "chưa cần biện pháp can thiệp và tiếp tục theo dõi định kỳ."
        )
    elif tier_val == 1:
        st.write(
            f"Hạng {TIER_NAME.get(1)} — gợi ý: {tier_action}. "
            "Theo dõi sát tỷ lệ bàn giao trễ và phản hồi khách hàng ở kỳ tiếp theo trước khi nâng mức xử lý."
        )
    elif tier_val == 2:
        st.write(
            f"Hạng {TIER_NAME.get(2)} — gợi ý: {tier_action}. "
            "Gửi cảnh báo sớm kèm hỗ trợ quy trình đóng gói, bàn giao vận chuyển để giảm đơn xấu."
        )
    else:
        st.write(
            f"Hạng {TIER_NAME.get(3)} — gợi ý: {tier_action}. "
            "Tạm ngưng hiển thị cho đến khi seller khắc phục tỷ lệ bàn giao trễ và điểm đánh giá."
        )

    pages = st.session_state.get("nav_pages", {})
    links = st.columns(2)
    if pages.get("policy") is not None:
        with links[0]:
            st.page_link(pages["policy"], label="Mở trang chính sách")
    if pages.get("olap") is not None:
        with links[1]:
            st.page_link(pages["olap"], label="Mở OLAP Slice")

    # Hồ sơ
    region_text = _clean_text(row.get("region_name")) or "—"
    state_text = _clean_text(row.get("state_code")) or "—"
    city_text = _clean_text(row.get("city_name")) or "—"
    cat_summary = (
        f"Danh mục chính: {main_cat} ({fmt_pct(main_share)} GMV)"
        if main_cat is not None and main_share is not None
        else "Danh mục chính: —"
    )
    profile_parts = [f"{region_text} / {state_text} / {city_text}", cat_summary]
    seg = _clean_text(row.get("business_segment"))
    lead = _clean_text(row.get("lead_type"))
    age_raw = row.get("seller_age_days")
    age_text = None if age_raw is None or pd.isna(age_raw) else f"{fmt_count(age_raw)} ngày"
    if seg is not None:
        profile_parts.append(f"Phân khúc: {seg}")
    if lead is not None:
        profile_parts.append(f"Loại lead: {lead}")
    if age_text is not None:
        profile_parts.append(f"Tuổi seller: {age_text}")
    st.caption(" · ".join(profile_parts))

    if len(valid_cats) >= 3:
        plot_cats = valid_cats.sort_values("share", ascending=True)
        figure = go.Figure(
            go.Bar(
                x=plot_cats["share"],
                y=plot_cats["category_group"],
                orientation="h",
                name="Tỷ trọng GMV (%)",
                marker_color=NAVY,
                hovertemplate="%{y}<br>%{x:.1%} GMV<extra></extra>",
            )
        )
        figure.update_layout(height=max(240, 28 * len(plot_cats) + 80), margin_l=140, margin_b=12)
        figure.update_xaxes(tickformat=".0%", title="Tỷ trọng GMV (%)")
        figure.update_yaxes(title="Nhóm danh mục", automargin=True)
        st.plotly_chart(
            style_fig(
                figure,
                "GMV của seller này nằm ở nhóm hàng nào?",
                f"Tháng chấm {as_of} · seller {seller_short}",
            ),
            width="stretch",
        )
        chart_note("Thanh dài là nhóm hàng mang lại nhiều doanh thu nhất cho seller này.")


def _trust(as_of: str, model_name: str, trained_through) -> None:
    st.write(f"Loại mô hình: {model_name or '—'}. Học đến tháng {trained_through or '—'}.")
    st.caption("Đơn có nhiều seller không được tính review cho từng seller.")
    try:
        metrics = db.query(*queries.model_eval(as_of))
        calibration = db.query(*queries.model_calibration(as_of))
    except Exception:
        st.info("Chưa có kết quả đánh giá cho kỳ này.")
        return
    if metrics.empty and calibration.empty:
        st.info("Chưa có kết quả đánh giá cho kỳ này.")
        return
    if not metrics.empty:
        def _metric_number(name: str) -> str:
            rows = metrics.loc[metrics["metric"].astype(str) == name, "value"]
            if rows.empty:
                return "—"
            value = rows.iloc[0]
            if value is None or pd.isna(value):
                return "—"
            text = f"{float(value):,.3f}"
            return text.replace(",", "X").replace(".", ",").replace("X", ".")

        def _test_month_label() -> str:
            rows = metrics.loc[metrics["metric"].astype(str) == "test_month", "value"].dropna()
            labels = []
            for value in rows:
                key = int(round(float(value)))
                year, month = divmod(key, 100)
                if 1 <= month <= 12:
                    labels.append(f"{year:04d}-{month:02d}")
            if not labels:
                return "—"
            return ", ".join(sorted(set(labels)))

        cards = st.columns(3)
        with cards[0]:
            kpi_card(
                "AUC",
                _metric_number("auc"),
                help="Xác suất mô hình xếp một seller xấu cao hơn một seller tốt; 0,5 là đoán bừa, 1 là hoàn hảo.",
            )
        with cards[1]:
            kpi_card(
                "Brier",
                _metric_number("brier"),
                help="Sai số bình phương trung bình của xác suất; càng thấp càng tốt, so với Brier của việc đoán bằng tỷ lệ trung bình.",
            )
        with cards[2]:
            kpi_card(
                "Tháng test",
                _test_month_label(),
                help="Các tháng dùng để đánh giá.",
            )
    if not calibration.empty:
        figure = go.Figure()
        figure.add_scatter(
            x=pd.to_numeric(calibration["mean_pred"], errors="coerce"),
            y=pd.to_numeric(calibration["observed_rate"], errors="coerce"),
            name="Tỷ lệ quan sát (%)",
            mode="markers+lines",
            text=calibration["n"].map(lambda item: f"n={fmt_count(item)}"),
            marker_color=NAVY,
        )
        figure.add_scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            line=dict(dash="dash", color="#8a93a0"),
            name="Khớp hoàn hảo",
        )
        figure.update_layout(height=340)
        figure.update_xaxes(title="Xác suất dự báo (%)", tickformat=".0%")
        figure.update_yaxes(title="Tỷ lệ quan sát (%)", tickformat=".0%")
        st.plotly_chart(
            style_fig(
                figure,
                "Xác suất dự báo có khớp tỷ lệ đơn xấu thực tế không?",
                f"Tháng chấm {as_of}",
            ),
            width="stretch",
        )
        chart_note("Điểm gần đường đứt là nhóm được dự báo sát tỷ lệ đơn xấu thực tế.")


def render(settings=None) -> None:
    del settings
    try:
        with st.spinner("Đang tải dữ liệu…"):
            raw = db.query(*queries.risk_board())
    except Exception as exc:
        page_header("Seller nào đáng lo nhất?", "Chưa tải được dữ liệu để kết luận.", "predicted")
        db.show_warehouse_error(exc)
        next_step("risk")
        return
    if raw.empty:
        page_header("Seller nào đáng lo nhất?", "Chưa có điểm rủi ro cho kỳ này.", "predicted")
        next_step("risk")
        return
    raw = raw[raw["as_of_month"].astype(str) == AS_OF_MONTH].copy()
    if raw.empty:
        page_header("Seller nào đáng lo nhất?", "Kỳ này chưa đủ dữ liệu để chấm.", "predicted")
        next_step("risk")
        return
    if "risk_min_orders" not in st.session_state:
        st.session_state["risk_min_orders"] = int(MIN_ORDERS)
    min_orders = int(st.session_state["risk_min_orders"])
    scored, scenario = _attach(raw, min_orders)
    as_of = AS_OF_MONTH
    scored_at = str(scored["scored_at"].iloc[0]).split(".")[0] if "scored_at" in scored.columns else "—"
    eligible = scored[pd.to_numeric(scored["n_orders_valid"], errors="coerce").fillna(0) >= int(min_orders)].copy()
    page_header("Seller nào đáng lo nhất?", _flag_sentence(eligible, scored), "predicted")
    st.number_input(
        "Số đơn tối thiểu để được chấm",
        min_value=0,
        step=1,
        help=explain("risk_score"),
        key="risk_min_orders",
    )
    st.caption(
        f"Tháng chấm {as_of}. Job chạy {scored_at}. "
        f"{fmt_count(len(eligible))} seller đủ điều kiện gắn cờ / {fmt_count(len(scored))} seller được chấm."
    )
    if eligible.empty:
        next_step("risk")
        return
    _summary(scored, eligible, scenario, min_orders)
    stats = _kpi_numbers(scored, eligible, scenario)
    if stats["p2_reduction"] is None:
        st.caption(
            f"Nếu áp dụng P2 trên toàn bộ {fmt_count(stats['n_scored'])} seller được chấm, "
            f"đơn xấu dự kiến còn {fmt_number(stats['p2_remaining'])}."
        )
    else:
        st.caption(
            f"Nếu áp dụng P2 trên toàn bộ {fmt_count(stats['n_scored'])} seller được chấm "
            f"(gắn cờ trong {fmt_count(stats['n_eligible'])} seller đủ điều kiện), "
            f"đơn xấu dự kiến còn {fmt_number(stats['p2_remaining'])} "
            f"(giảm {fmt_ratio(stats['p2_reduction'])})."
        )
    tabs = st.tabs(["Danh sách", "Phân bố", "Chi tiết seller", "Độ tin cậy"])
    with tabs[0]:
        _list_tab(eligible)
    with tabs[1]:
        _distribution(eligible)
    with tabs[2]:
        seller_id = st.session_state.get("risk_seller_id")
        if not seller_id:
            st.info("Chọn một dòng ở tab Danh sách.")
        else:
            try:
                platform = db.query(*queries.platform_month(as_of))
                platform_row = None if platform.empty else platform.iloc[0]
            except Exception as exc:
                st.error(db.redact(exc))
                platform_row = None
            _detail(seller_id, eligible, platform_row)
    with tabs[3]:
        _trust(as_of, str(scored["model_name"].iloc[0]), scored["trained_through_month"].iloc[0])
    next_step("risk")
