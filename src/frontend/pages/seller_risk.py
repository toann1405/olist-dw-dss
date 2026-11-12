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
    MIN_N_DISPLAY,
    NAVY,
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
    result = simulate(scores, "P2", PolicyParams(min_orders=int(min_orders)))
    sellers = result.sellers
    out = scores.copy()
    out["tier"] = sellers["tier"].to_numpy()
    out["expected_bad"] = sellers["expected_bad_i"].to_numpy()
    out["flagged"] = sellers["flagged"].to_numpy()
    probability = pd.to_numeric(out["p_bad"], errors="coerce").fillna(0.0)
    orders = pd.to_numeric(out["n_orders_valid"], errors="coerce").fillna(0.0)
    out["baseline_bad"] = probability * orders
    return out, result


def _kpi_numbers(scored: pd.DataFrame, eligible: pd.DataFrame, scenario) -> dict:
    """Card values from the P2 scenario and the eligible slice."""
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
    baseline = float(pd.to_numeric(eligible["baseline_bad"], errors="coerce").fillna(0).sum())
    flagged_baseline = float(pd.to_numeric(flagged["baseline_bad"], errors="coerce").fillna(0).sum())
    remaining = float(pd.to_numeric(eligible["expected_bad"], errors="coerce").fillna(0).sum())
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


def _flag_sentence(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "Chưa đủ dữ liệu để kết luận."
    horizon = _forecast_month(AS_OF_MONTH) or "tới"
    when = f"Tháng {horizon}" if horizon != "tới" else "Tháng tới"
    flagged = frame[frame["flagged"].astype(bool)] if "flagged" in frame.columns else frame.iloc[0:0]
    total = len(frame)
    n_flagged = len(flagged)
    if n_flagged == 0:
        return (
            f"{when} dự kiến không có seller nào vượt ngưỡng rủi ro (chính sách P2) "
            f"trong {fmt_count(total)} seller đủ điều kiện."
        )
    total_bad = float(pd.to_numeric(frame["baseline_bad"], errors="coerce").fillna(0).sum())
    flagged_bad = float(pd.to_numeric(flagged["baseline_bad"], errors="coerce").fillna(0).sum())
    share = None if total_bad <= 0 else flagged_bad / total_bad
    share_text = "" if share is None else f", gom khoảng {fmt_ratio(share)} đơn xấu dự kiến"
    return (
        f"{when} dự kiến có {fmt_count(n_flagged)}/{fmt_count(total)} seller "
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
            "Tổng xác suất đơn xấu × số đơn của từng seller, trước khi áp dụng chính sách.",
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
    match = frame[frame["seller_id"].astype(str) == seller_id]
    if match.empty:
        st.info("Chỉ xem seller đã được chấm trong kỳ này.")
        return
    row = match.iloc[0]
    share = percentile_above(frame["p_bad"].tolist(), row["p_bad"])
    st.subheader("① Seller này là ai")
    st.write(
        f"{_known(row.get('region_name'))} / {_known(row.get('state_code'))} / {_known(row.get('city_name'))}."
    )
    st.write(f"Phân khúc: {_known(row.get('business_segment'))}.")
    st.write(f"Loại lead: {_known(row.get('lead_type'))}.")
    st.write(f"Tuổi seller: {_known(row.get('seller_age_days'))} ngày." if _known(row.get("seller_age_days")) != MISSING else f"Tuổi seller: {MISSING}.")
    try:
        categories = db.query(*queries.seller_categories(seller_id, str(row["as_of_month"])))
    except Exception as exc:
        st.error(db.redact(exc))
        categories = pd.DataFrame()
    if not categories.empty and "gmv" in categories.columns:
        total = float(pd.to_numeric(categories["gmv"], errors="coerce").fillna(0).sum())
        if total > 0:
            categories = categories.copy()
            categories["share"] = pd.to_numeric(categories["gmv"], errors="coerce").fillna(0) / total
            main = categories.iloc[0]["category_group"]
            st.write(f"Danh mục chính theo GMV: {main}.")
            figure = go.Figure(go.Bar(
                x=categories["share"],
                y=categories["category_group"],
                orientation="h",
                name="Tỷ trọng GMV (%)",
                marker_color=NAVY,
                hovertemplate="%{y}<br>%{x:.1%} GMV<extra></extra>",
            ))
            figure.update_layout(height=max(240, 28 * len(categories) + 80), margin_l=140, margin_b=12)
            figure.update_xaxes(tickformat=".0%", title="Tỷ trọng GMV (%)")
            figure.update_yaxes(title="Nhóm danh mục", automargin=True)
            st.plotly_chart(
                style_fig(
                    figure,
                    "GMV của seller này nằm ở nhóm hàng nào?",
                    f"Tháng chấm {AS_OF_MONTH} · seller {str(seller_id)[:8]}",
                ),
                width="stretch",
            )
            chart_note("Thanh dài là nhóm hàng mang lại nhiều doanh thu nhất cho seller này.")
    try:
        history = db.query(*queries.seller_history(seller_id))
    except Exception as exc:
        st.error(db.redact(exc))
        history = pd.DataFrame()
    active_months = 0
    if not history.empty:
        active_months = int((pd.to_numeric(history["n_orders_valid"], errors="coerce").fillna(0) > 0).sum())
    st.write(f"Số tháng có đơn: {fmt_count(active_months)}.")

    platform_late = None if platform is None else _rate(platform.get("late_ship_count"), platform.get("late_ship_eligible"))
    with st.expander("② Đã làm thế nào"):
        columns = st.columns(4)
        for column, (label, value) in zip(columns, [
            ("GMV", fmt_brl(row["gmv"])),
            ("Số đơn hợp lệ", fmt_count(row["n_orders_valid"])),
            ("Bàn giao trễ", fmt_ratio(row["late_ship_rate"])),
            ("Review TB", fmt_number(row["avg_review"])),
        ]):
            with column:
                kpi_card(label, value)
        if platform_late is not None and row.get("late_ship_rate") is not None and not pd.isna(row["late_ship_rate"]):
            st.caption(f"Bàn giao trễ so với sàn: {fmt_pct(float(row['late_ship_rate']) - platform_late)} điểm.")
        platform_review = None if platform is None else _rate(platform.get("negative_review_count"), platform.get("negative_review_eligible"))
        for chip in reason_chips(row.get("late_ship_rate"), row.get("avg_review"), platform_late, platform_review):
            st.markdown(f"`{chip}`")
        if active_months < 3:
            st.info("Chưa đủ lịch sử để vẽ xu hướng.")
        else:
            history["late_rate"] = [_rate(a, b) for a, b in zip(history["late_ship_count"], history["late_ship_eligible"])]
            figure = go.Figure()
            figure.add_scatter(
                x=history["year_month"],
                y=history["late_rate"],
                name="Seller này",
                mode="lines+markers",
                line=dict(color=NAVY),
            )
            if platform_late is not None:
                figure.add_hline(y=platform_late, line_dash="dash", line_color=NAVY, annotation_text="Trung bình toàn sàn")
                add_legend_swatch(figure, "Trung bình toàn sàn", NAVY, dash="dash")
            figure.update_layout(height=300)
            figure.update_xaxes(title="Tháng")
            figure.update_yaxes(tickformat=".0%", title="Bàn giao trễ (%)")
            st.plotly_chart(
                style_fig(
                    figure,
                    "Bàn giao trễ của seller này so với sàn theo từng tháng?",
                    f"Tháng chấm {AS_OF_MONTH} · seller {str(seller_id)[:8]}",
                ),
                width="stretch",
            )
            chart_note("Điểm nằm trên đường đứt là tháng seller bàn giao trễ hơn mặt bằng sàn.")

    st.subheader("③ Mô hình dự báo gì và nên làm gì")
    higher = fmt_pct(share) if share is not None else "—"
    st.write(
        f"Dự báo ~{fmt_pct(row['p_bad'])} đơn tháng tới là đơn xấu, cao hơn {higher} seller khác "
        f"→ hạng {TIER_NAME.get(int(row['tier']), row['tier'])} → gợi ý: {action_for_tier(int(row['tier']))}."
    )
    try:
        contrib = db.query(*queries.risk_contrib(seller_id, str(row["as_of_month"])))
    except Exception:
        contrib = pd.DataFrame()
    if contrib.empty:
        st.caption("Chưa có kết quả đánh giá cho kỳ này.")
    else:
        figure = go.Figure(go.Bar(
            x=pd.to_numeric(contrib["contribution"], errors="coerce"),
            y=contrib["feature"],
            orientation="h",
            name="Đóng góp (log-odds)",
            marker_color=PREDICTED,
        ))
        figure.update_layout(height=max(240, 28 * len(contrib) + 80), margin_l=140, margin_b=12)
        figure.update_xaxes(title="Đóng góp (log-odds)")
        figure.update_yaxes(title="Yếu tố", automargin=True)
        st.plotly_chart(
            style_fig(
                figure,
                "Yếu tố nào đẩy xác suất đơn xấu của seller này?",
                f"Tháng chấm {AS_OF_MONTH} · seller {str(seller_id)[:8]}",
            ),
            width="stretch",
        )
        chart_note("Thanh dương làm xác suất đơn xấu tăng; thanh âm kéo xác suất xuống.")
    pages = st.session_state.get("nav_pages", {})
    links = st.columns(2)
    if pages.get("policy") is not None:
        with links[0]:
            st.page_link(pages["policy"], label="Mở trang chính sách")
    if pages.get("olap") is not None:
        with links[1]:
            st.page_link(pages["olap"], label="Mở OLAP Slice")


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
    page_header("Seller nào đáng lo nhất?", _flag_sentence(eligible), "predicted")
    st.number_input(
        "Số đơn tối thiểu để được chấm",
        min_value=0,
        step=1,
        help=explain("risk_score"),
        key="risk_min_orders",
    )
    st.caption(
        f"Tháng chấm {as_of}. Job chạy {scored_at}. "
        f"{fmt_count(len(eligible))} seller đủ điều kiện / {fmt_count(len(scored))} seller tổng."
    )
    if eligible.empty:
        next_step("risk")
        return
    _summary(scored, eligible, scenario, min_orders)
    stats = _kpi_numbers(scored, eligible, scenario)
    if stats["p2_reduction"] is None:
        st.caption(f"Nếu áp dụng P2, đơn xấu dự kiến còn {fmt_number(stats['p2_remaining'])}.")
    else:
        st.caption(
            f"Nếu áp dụng P2, đơn xấu dự kiến còn {fmt_number(stats['p2_remaining'])} "
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
