"""Five OLAP operators in tabs. The SQL files keep the locked questions."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db, queries
from lib.glossary import explain
from lib.ui import (
    LATE,
    MIN_N_DISPLAY,
    NEUTRAL,
    REVIEW,
    add_legend_swatch,
    button_dropdown,
    filters,
    fmt_int,
    fmt_pct,
    highlight_colors,
    kpi_card,
    next_step,
    page_header,
    small_n_label,
    style_fig,
)

DICE_MIN_N = MIN_N_DISPLAY


def _num(series_value):
    if series_value is None:
        return None
    try:
        if pd.isna(series_value):
            return None
    except TypeError:
        return None
    return float(series_value)


def _ratio(numerator, denominator):
    top, bottom = _num(numerator), _num(denominator)
    if top is None or bottom is None or bottom == 0:
        return None
    return top / bottom


def _load(loader):
    try:
        return loader(), None
    except Exception as exc:
        return None, exc


def _view(key: str) -> str:
    return st.segmented_control("Xem", ["Biểu đồ", "Bảng"], default="Biểu đồ", key=key)


def _panel(question: str, lines: list[str], frame: pd.DataFrame | None = None, source: str = "", key: str = "") -> None:
    st.markdown(f"**Câu hỏi.** {question}")
    text = " ".join(lines[:2]) if lines else "Chưa đủ dữ liệu để kết luận."
    st.info(text)
    for line in lines[2:]:
        st.write(line)
    if frame is not None and key and st.toggle("Xem bảng", key=key):
        st.dataframe(frame, width="stretch", hide_index=True)
        st.download_button(
            "Tải CSV",
            frame.to_csv(index=False).encode("utf-8"),
            file_name=f"{key}.csv",
            mime="text/csv",
        )
    if source:
        st.caption(source)


def _review_by_level(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    work = frame.copy()
    work["negative_orders"] = pd.to_numeric(work["negative_orders"], errors="coerce").fillna(0)
    work["reviewed_orders"] = pd.to_numeric(work["reviewed_orders"], errors="coerce").fillna(0)
    grouped = work.groupby(columns, as_index=False, dropna=False)[
        ["negative_orders", "reviewed_orders"]
    ].sum()
    denominator = grouped["reviewed_orders"]
    grouped["negative_review_rate"] = grouped["negative_orders"] / denominator.where(denominator > 0)
    return grouped.sort_values(columns)


def _place_label(frame: pd.DataFrame, level: str) -> pd.DataFrame:
    out = frame.copy()
    if level == "region":
        out["axis"] = out["region_name"].fillna("(không map được vùng)")
    elif level == "state":
        region = out["region_name"].fillna("(không map được vùng)")
        state = out["state_code"].fillna("(trống)")
        out["axis"] = region + " / " + state
    else:
        city = out["city_name"].fillna("(trống)")
        state = out["state_code"].fillna("(trống)")
        out["axis"] = state + " / " + city
    return out


def _hbar(
    labels,
    rates,
    samples,
    color: str,
    axis_title: str,
    question: str,
    subtitle: str,
    legend_side: str = "top",
) -> go.Figure:
    colors = highlight_colors([float(value) for value in rates], color)
    fig = go.Figure(
        go.Bar(
            x=rates,
            y=labels,
            orientation="h",
            name=axis_title,
            showlegend=False,
            marker_color=colors,
            customdata=samples,
            hovertemplate="%{y}<br>" + axis_title + " %{x:.1%}<br>n %{customdata:,.0f}<extra></extra>",
        )
    )
    add_legend_swatch(fig, "Cao nhất", color)
    add_legend_swatch(fig, "Các nhóm còn lại", NEUTRAL)
    fig.update_layout(height=max(280, 34 * len(labels) + 120), margin_l=160, margin_r=16, margin_b=16)
    fig.update_xaxes(tickformat=".0%", title=axis_title)
    fig.update_yaxes(title="Nơi bán", automargin=True)
    return style_fig(fig, question, subtitle, legend_side=legend_side)


def _kpi_strip() -> None:
    year, region, state, _category = filters()
    try:
        monthly = db.query(*queries.kpi_seller_month(year, region, state)).iloc[0]
        orders = db.query(*queries.kpi_orders(year, region, state)).iloc[0]
    except Exception as exc:
        st.error(db.redact(exc))
        return
    gmv = _num(monthly["gmv"])
    late = _ratio(monthly["late_ship_count"], monthly["late_ship_eligible"])
    review = _ratio(monthly["negative_review_count"], monthly["negative_review_eligible"])
    aov = _ratio(orders["gmv_from_items"], orders["valid_orders"])
    values = [
        ("GMV", fmt_brl_local(gmv), explain("gmv")),
        ("AOV", fmt_brl_local(aov), explain("aov")),
        ("Bàn giao trễ", fmt_pct(late), explain("late_ship")),
        ("Review xấu (theo seller)", fmt_pct(review), explain("negative_review")),
    ]
    try:
        quality = db.query(*queries.market_quality(year, region, state))
        if not quality.empty and quality.iloc[0]["bad_eligible"]:
            bad = float(quality.iloc[0]["bad_orders"]) / float(quality.iloc[0]["bad_eligible"])
            values.append(("Đơn trải nghiệm xấu", fmt_pct(bad), explain("bad_experience")))
    except Exception as exc:
        st.error(db.redact(exc))
    columns = st.columns(len(values))
    for column, (label, value, help_text) in zip(columns, values):
        with column:
            kpi_card(label, value, help_text=help_text)


def fmt_brl_local(value):
    from lib.ui import fmt_brl

    return fmt_brl(value)


def _tab_rollup(frame: pd.DataFrame) -> None:
    chart_col, side = st.columns([2, 1])
    with side:
        level = button_dropdown("Mức", ("region", "state", "city"), "olap_level")
    part = _place_label(frame[frame["rollup_level"] == level].copy(), level)
    part["late_ship_rate"] = pd.to_numeric(part["late_ship_rate"], errors="coerce")
    part["eligible_items"] = pd.to_numeric(part["eligible_items"], errors="coerce")
    shown = part.dropna(subset=["late_ship_rate"])
    if level == "city":
        shown = shown.sort_values("eligible_items", ascending=False).head(20)
    top = shown.sort_values("late_ship_rate", ascending=False).head(1)
    lines = []
    if not top.empty:
        row = top.iloc[0]
        lines.append(f"{row['axis']} cao nhất: {fmt_pct(row['late_ship_rate'])} (n={fmt_int(row['eligible_items'])}).")
    if level == "city":
        lines.append("Biểu đồ lấy 20 thành phố có nhiều item đủ mẫu nhất.")
    else:
        lines.append("Mọi nhãn của mức này đều được vẽ.")
    states = frame[frame["rollup_level"] == "state"].copy()
    states["late_items"] = pd.to_numeric(states["late_items"], errors="coerce").fillna(0)
    total_late = float(states["late_items"].sum())
    if total_late > 0:
        top3 = states.sort_values("late_items", ascending=False).head(3)
        share = float(top3["late_items"].sum()) / total_late
        lines.append(f"Top 3 bang chiếm {fmt_pct(share)} số item bàn giao trễ.")
    lines.append("Tỷ lệ = item trễ / item có cờ khác null.")
    with chart_col:
        mode = _view("rollup_view")
        if mode == "Bảng":
            st.dataframe(part, width="stretch", hide_index=True)
        elif shown.empty:
            st.info("Không có tỷ lệ để vẽ.")
        else:
            ordered = shown.sort_values("late_ship_rate")
            st.plotly_chart(
                _hbar(
                    ordered["axis"],
                    ordered["late_ship_rate"],
                    ordered["eligible_items"],
                    LATE,
                    "Bàn giao trễ (%)",
                    "Bàn giao trễ là chuyện cả vùng hay một nơi?",
                    f"Mức {level} · mọi năm · không theo bộ lọc sidebar",
                    legend_side="right" if level == "state" else "top",
                ),
                width="stretch",
            )
    with side:
        _panel(
            "Bàn giao trễ là chuyện cả vùng hay một nơi?",
            lines,
            part,
            "Nguồn: gold.fact_order_item, gold.dim_seller.",
            "rollup_table",
        )


def _tab_drill(frame: pd.DataFrame) -> None:
    chart_col, side = st.columns([2, 1])
    with side:
        level = button_dropdown("Mức", ("Năm", "Quý", "Tháng", "Ngày"), "drill_level")
    columns = {
        "Năm": ["year"],
        "Quý": ["year", "quarter"],
        "Tháng": ["year", "quarter", "month"],
        "Ngày": ["year", "quarter", "month", "day_of_month", "full_date"],
    }[level]
    grouped = _review_by_level(frame, columns)
    if level == "Năm":
        grouped["axis"] = grouped["year"].astype(str)
    elif level == "Quý":
        grouped["axis"] = grouped["year"].astype(str) + " Q" + grouped["quarter"].astype(str)
    elif level == "Tháng":
        grouped["axis"] = grouped["year"].astype(str) + "-" + grouped["month"].astype(int).astype(str).str.zfill(2)
    else:
        grouped["axis"] = pd.to_datetime(grouped["full_date"])
    peak = grouped.sort_values("negative_review_rate", ascending=False).head(1)
    small = grouped[grouped["reviewed_orders"] < 500]
    lines = ["KPI sàn: giữ cross_seller. Tỷ lệ = đơn review xấu / đơn có điểm."]
    lines.append(
        "Đỉnh tháng 3/2018 khoảng 1,6% là giả định, chưa đo lại trên biểu đồ này. Hãy tự đối chiếu."
    )
    if not peak.empty:
        row = peak.iloc[0]
        label = row["axis"] if level != "Ngày" else str(row["full_date"])[:10]
        lines.append(f"{label} cao nhất: {fmt_pct(row['negative_review_rate'])} (n={fmt_int(row['reviewed_orders'])}).")
    if not small.empty:
        lines.append("Có kỳ mẫu nhỏ (n < 500), trong đó thường là 2016. Tỷ lệ những kỳ đó dễ dao động.")
    with chart_col:
        mode = _view("drill_view")
        if mode == "Bảng":
            st.dataframe(grouped, width="stretch", hide_index=True)
        else:
            fig = go.Figure(
                go.Scatter(
                    x=grouped["axis"],
                    y=grouped["negative_review_rate"],
                    name="Review xấu (%)",
                    mode="lines+markers",
                    line=dict(color=REVIEW, width=2),
                    marker=dict(color="#c8963e", size=8),
                    customdata=grouped["reviewed_orders"],
                    hovertemplate="%{x}<br>Review xấu %{y:.1%}<br>n %{customdata:,.0f}<extra></extra>",
                )
            )
            fig.update_layout(height=360)
            fig.update_xaxes(title="Kỳ")
            fig.update_yaxes(tickformat=".0%", title="Review xấu (%)")
            st.plotly_chart(
                style_fig(
                    fig,
                    "Kỳ nào review xấu nổi hơn các kỳ quanh nó?",
                    "Mọi năm · review trên đơn sàn · không theo bộ lọc sidebar",
                ),
                width="stretch",
            )
    with side:
        _panel(
            "Kỳ nào review xấu nổi hơn các kỳ quanh nó?",
            lines,
            grouped,
            "Nguồn: gold.fact_order, gold.dim_date.",
            "drill_table",
        )


def _tab_slice(groups: pd.DataFrame) -> None:
    names = groups["category_group"].dropna().astype(str).tolist()
    chart_col, side = st.columns([2, 1])
    _year, _region, _state, category = filters()
    with side:
        if not names:
            st.info("Không có nhóm danh mục.")
            return
        preferred = category if category in names else "electronics_it_telephony"
        if preferred not in names:
            preferred = names[0]
        chosen = button_dropdown(
            "Nhóm danh mục",
            names,
            "slice_group",
            index=names.index(preferred),
        )
        minimum = st.slider("Số đơn tối thiểu để vẽ", min_value=1, max_value=50, value=5, key="slice_min")
    try:
        frame = db.query(*queries.slice_category(chosen))
    except Exception as exc:
        st.error(db.redact(exc))
        return
    data = frame.copy()
    data["late_delivery_rate"] = pd.to_numeric(data["late_delivery_rate"], errors="coerce")
    data["eligible_orders"] = pd.to_numeric(data["eligible_orders"], errors="coerce")
    data = data[data["eligible_orders"] >= minimum].dropna(subset=["late_delivery_rate"])
    data = data.sort_values(["late_delivery_rate", "eligible_orders"], ascending=[False, False])
    data["short_id"] = data["seller_id"].astype(str).str.slice(0, 8)
    top = data.head(15)
    lines = [f"Đang cắt {chosen}. Chỉ seller có n ≥ {minimum} đơn đủ mẫu."]
    if not top.empty:
        row = top.iloc[0]
        lines.append(
            f"{row['short_id']} cao nhất: {fmt_pct(row['late_delivery_rate'])} (n={fmt_int(row['eligible_orders'])})."
        )
    lines.append("Cờ giao trễ đếm đơn phân biệt, không cộng trên từng item.")
    with chart_col:
        mode = _view("slice_view")
        if mode == "Bảng":
            show = data.copy()
            show["seller"] = show["seller_id"].astype(str).str.slice(0, 8)
            st.dataframe(show, width="stretch", hide_index=True)
        elif top.empty:
            st.info("Không có seller qua ngưỡng đơn.")
        else:
            plot = top.sort_values("late_delivery_rate")
            fig = go.Figure(
                go.Bar(
                    x=plot["late_delivery_rate"],
                    y=plot["short_id"],
                    orientation="h",
                    name="Giao trễ tới khách (%)",
                    marker_color="#c8963e",
                    customdata=list(zip(plot["seller_id"], plot["eligible_orders"])),
                    hovertemplate="%{customdata[0]}<br>Giao trễ %{x:.1%}<br>n %{customdata[1]:,.0f}<extra></extra>",
                )
            )
            fig.update_layout(height=max(300, 32 * len(plot) + 100), margin_l=90, margin_r=12, margin_b=12)
            fig.update_xaxes(tickformat=".0%", title="Giao trễ tới khách (%)")
            fig.update_yaxes(title="Seller", automargin=True)
            st.plotly_chart(
                style_fig(
                    fig,
                    "Seller nào giao trễ tới khách nhiều nhất trong nhóm này?",
                    f"Nhóm {chosen} · ít nhất {minimum} đơn đủ mẫu · không theo bộ lọc sidebar",
                ),
                width="stretch",
            )
    with side:
        _panel(
            "Trong một nhóm danh mục, seller nào giao trễ tới khách nhiều nhất?",
            lines,
            data,
            "Nguồn: gold.fact_order_item, gold.dim_product, gold.dim_seller.",
            "slice_table",
        )


def _tab_dice(frame: pd.DataFrame) -> None:
    data = frame.copy()
    for column in ("late_delivery_rate", "seller_negative_review_rate", "late_eligible_orders", "review_eligible_orders"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["n"] = data["late_eligible_orders"].fillna(0)
    kept = data[data["n"] >= DICE_MIN_N].copy()
    dropped = data[data["n"] < DICE_MIN_N]
    lines = [
        "Khách Norte hoặc Nordeste, quý 1–2/2018, hàng bulky. Câu hỏi này không lấy bộ lọc sidebar.",
        f"Bang có n < {DICE_MIN_N} không vẽ thanh.",
    ]
    if not kept.empty:
        row = kept.sort_values("late_delivery_rate", ascending=False).iloc[0]
        lines.append(f"{row['state_code']} giao trễ cao nhất: {fmt_pct(row['late_delivery_rate'])} (n={fmt_int(row['n'])}).")
    if not dropped.empty:
        names = ", ".join(f"{row.state_code} (n={fmt_int(row.n)})" for row in dropped.itertuples())
        lines.append(f"Dưới ngưỡng: {names}.")
    chart_col, side = st.columns([2, 1])
    with chart_col:
        mode = _view("dice_view")
        if mode == "Bảng":
            st.dataframe(data, width="stretch", hide_index=True)
        elif kept.empty:
            st.info("Không có bang qua ngưỡng mẫu.")
        else:
            kept = kept.sort_values("n")
            labels = [f"{code} · n={fmt_int(n)}" for code, n in zip(kept["state_code"], kept["n"])]
            fig = go.Figure()
            fig.add_bar(
                name="Giao trễ tới khách",
                y=labels,
                x=kept["late_delivery_rate"],
                orientation="h",
                marker_color=LATE,
                customdata=kept["n"],
                hovertemplate="%{y}<br>Giao trễ %{x:.1%}<br>n %{customdata:,.0f}<extra></extra>",
            )
            fig.add_bar(
                name="Review xấu (seller)",
                y=labels,
                x=kept["seller_negative_review_rate"],
                orientation="h",
                marker_color=REVIEW,
                customdata=kept["review_eligible_orders"],
                hovertemplate="%{y}<br>Review xấu %{x:.1%}<br>n %{customdata:,.0f}<extra></extra>",
            )
            fig.update_layout(
                height=max(340, 46 * len(kept) + 120),
                barmode="group",
                margin_l=140,
                margin_r=12,
                margin_b=12,
            )
            fig.update_xaxes(tickformat=".0%", title="Tỷ lệ (%)")
            fig.update_yaxes(title="Bang seller", automargin=True)
            st.plotly_chart(
                style_fig(
                    fig,
                    "Bang nào vừa giao trễ vừa bị review xấu trong lát cắt này?",
                    "Khách Norte hoặc Nordeste · quý 1–2/2018 · hàng bulky · không theo bộ lọc sidebar",
                ),
                width="stretch",
            )
    with side:
        _panel(
            "Ở lát cắt này, bang seller nào trễ và bị review xấu?",
            lines,
            data,
            "Nguồn: đơn và dòng hàng. Lát cắt cố định: khách Norte hoặc Nordeste, quý 1–2 năm 2018, hàng cồng kềnh.",
            "dice_table",
        )


def _tab_pivot(frame: pd.DataFrame) -> None:
    data = frame.copy()
    data["late_items"] = pd.to_numeric(data["late_items"], errors="coerce")
    data["eligible_items"] = pd.to_numeric(data["eligible_items"], errors="coerce")
    data = data[data["category_group"].astype(str) != "Unknown"]
    data["late_rate"] = data["late_items"] / data["eligible_items"].where(data["eligible_items"] > 0)
    data["quarter_label"] = "Q" + data["quarter"].astype(int).astype(str)
    totals = data.groupby("category_group", as_index=False)["late_items"].sum().sort_values("late_items", ascending=False)
    categories = totals["category_group"].tolist()
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    matrix = (
        data.pivot(index="category_group", columns="quarter_label", values="late_rate")
        .reindex(index=categories, columns=quarters)
    )
    counts = (
        data.pivot(index="category_group", columns="quarter_label", values="eligible_items")
        .reindex(index=categories, columns=quarters)
    )
    matrix = matrix.where(counts >= MIN_N_DISPLAY)
    text = matrix.map(lambda value: "—" if pd.isna(value) else fmt_pct(value))
    peak = data[data["eligible_items"] >= MIN_N_DISPLAY].dropna(subset=["late_rate"]).sort_values("late_rate", ascending=False).head(1)
    delta = matrix.diff(axis=1)
    lines = ["Mọi năm gộp vào cùng một quý. Unknown đã loại. Ô có n dưới ngưỡng hiển thị bị làm mờ."]
    if delta.notna().any().any():
        stacked = delta.stack()
        cell = stacked.abs().sort_values(ascending=False).head(1)
        if not cell.empty:
            category, quarter = cell.index[0]
            lines.append(
                f"Độ lệch lớn nhất so với quý trước là {category} {quarter}: {fmt_pct(stacked.loc[(category, quarter)])}."
            )
    if not peak.empty:
        row = peak.iloc[0]
        lines.append(
            f"{row['category_group']} {row['quarter_label']} cao nhất: {fmt_pct(row['late_rate'])} (n={fmt_int(row['eligible_items'])})."
        )
    lines.append("Tooltip có tỷ lệ và số item đủ mẫu.")
    chart_col, side = st.columns([2, 1])
    with chart_col:
        mode = _view("pivot_view")
        if mode == "Bảng":
            show = matrix.copy()
            st.dataframe(show, width="stretch")
        else:
            fig = go.Figure(
                go.Heatmap(
                    z=matrix.values,
                    x=quarters,
                    y=categories,
                    colorscale=[[0, "#f6f1e7"], [0.5, "#e7b089"], [1, LATE]],
                    customdata=counts.values,
                    text=text.values,
                    texttemplate="%{text}",
                    hovertemplate="%{y} %{x}<br>%{z:.1%}<br>n %{customdata:,.0f}<extra></extra>",
                    colorbar=dict(tickformat=".0%", title="Bàn giao trễ (%)"),
                )
            )
            add_legend_swatch(fig, small_n_label(), "#d9d3c9")
            fig.update_layout(height=max(380, 42 * len(categories) + 120), margin_l=210, margin_r=16, margin_b=16)
            fig.update_xaxes(title="Quý")
            fig.update_yaxes(title="Nhóm danh mục", automargin=True)
            st.plotly_chart(
                style_fig(
                    fig,
                    "Nhóm danh mục nào kéo bàn giao trễ theo quý?",
                    f"Mọi năm gộp theo quý · ô trống khi {small_n_label()} · không theo bộ lọc sidebar",
                ),
                width="stretch",
            )
    with side:
        _panel(
            "Nhóm danh mục nào kéo bàn giao trễ theo quý?",
            lines,
            data,
            "Nguồn: gold.fact_order_item, gold.dim_product, gold.dim_date.",
            "pivot_table",
        )


def render(settings=None) -> None:
    del settings
    page_header(
        "GMV và trải nghiệm xấu đến từ đâu?",
        "Năm tab hỏi Gold qua SQL Warehouse bằng năm câu đã soạn sẵn. Bộ lọc bên cạnh không đổi các biểu đồ này.",
        "OLAP Explorer",
    )
    year, region, state, category = filters()
    _kpi_strip()
    with st.spinner("Đang tải dữ liệu…"):
        rollup, rollup_error = _load(lambda: db.query(*queries.rollup()))
        drill, drill_error = _load(lambda: db.query(*queries.drilldown()))
        groups, groups_error = _load(queries.category_groups)
        dice, dice_error = _load(lambda: db.query(*queries.dice()))
        pivot, pivot_error = _load(lambda: db.query(*queries.pivot_counts()))
    tabs = st.tabs([
        "Vùng hay cục bộ? (Roll-up)",
        "Tháng nào nổi? (Drill-down)",
        "Seller nào trễ nhất? (Slice)",
        "Lát cắt Norte+Nordeste, Q1–Q2/2018, bulky (Dice)",
        "Nguồn gây trễ? (Pivot)",
    ])
    with tabs[0]:
        if rollup_error:
            st.error(db.redact(rollup_error))
        else:
            _tab_rollup(rollup)
    with tabs[1]:
        if drill_error:
            st.error(db.redact(drill_error))
        else:
            _tab_drill(drill)
    with tabs[2]:
        if groups_error:
            st.error(db.redact(groups_error))
        else:
            _tab_slice(groups)
    with tabs[3]:
        if dice_error:
            st.error(db.redact(dice_error))
        else:
            _tab_dice(dice)
    with tabs[4]:
        if pivot_error:
            st.error(db.redact(pivot_error))
        else:
            _tab_pivot(pivot)
    next_step("olap")
