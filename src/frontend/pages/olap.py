"""Five OLAP operators in tabs. The SQL files keep the locked questions."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import db, queries
from lib.ui import LATE, NEUTRAL, REVIEW, apply_theme, filters, fmt_int, fmt_pct, kpi_card, page_header

DICE_MIN_N = 30


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


def _panel(question: str, lines: list[str]) -> None:
    st.markdown(f"**Câu hỏi.** {question}")
    for line in lines:
        st.write(line)


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


def _hbar(labels, rates, samples, color: str, title: str) -> go.Figure:
    from lib.ui import highlight_colors

    colors = highlight_colors([float(value) for value in rates], color)
    fig = go.Figure(
        go.Bar(
            x=rates,
            y=labels,
            orientation="h",
            marker_color=colors,
            customdata=samples,
            hovertemplate="%{y}<br>" + title + " %{x:.1%}<br>n %{customdata:,.0f}<extra></extra>",
        )
    )
    apply_theme(fig, height=max(260, 34 * len(labels) + 70))
    fig.update_layout(margin=dict(l=160, r=16, t=24, b=16))
    fig.update_xaxes(tickformat=".0%", title=title)
    fig.update_yaxes(automargin=True)
    return fig


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
    columns = st.columns(4)
    values = [
        ("GMV", fmt_brl_local(gmv), "SUM(price), không gồm cước, loại canceled và unavailable."),
        ("AOV", fmt_brl_local(aov), "GMV / số đơn phân biệt còn hiệu lực."),
        ("Bàn giao trễ", fmt_pct(late), f"n = {fmt_int(monthly['late_ship_eligible'])} item có cờ."),
        ("Review xấu", fmt_pct(review), f"n = {fmt_int(monthly['negative_review_eligible'])} đơn seller."),
    ]
    for column, (label, value, help_text) in zip(columns, values):
        with column:
            kpi_card(label, value, help_text=help_text)


def fmt_brl_local(value):
    from lib.ui import fmt_brl

    return fmt_brl(value)


def _tab_rollup(frame: pd.DataFrame) -> None:
    chart_col, side = st.columns([2, 1])
    with side:
        level = st.selectbox("Mức", ("region", "state", "city"), key="olap_level")
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
        lines.append("Mọi nhãn của mức này đều được vẽ, chiều cao theo số dòng.")
    lines.append("Seller −1 không vào mẫu. Tỷ lệ = item trễ / item có cờ khác null.")
    with chart_col:
        mode = _view("rollup_view")
        if mode == "Bảng":
            st.dataframe(part, width="stretch", hide_index=True)
        elif shown.empty:
            st.info("Không có tỷ lệ để vẽ.")
        else:
            ordered = shown.sort_values("late_ship_rate")
            st.plotly_chart(
                _hbar(ordered["axis"], ordered["late_ship_rate"], ordered["eligible_items"], LATE, "Bàn giao trễ"),
                width="stretch",
            )
    with side:
        _panel("Bàn giao trễ là chuyện cả vùng hay một nơi?", lines)


def _tab_drill(frame: pd.DataFrame) -> None:
    chart_col, side = st.columns([2, 1])
    with side:
        level = st.selectbox("Mức", ("Năm", "Quý", "Tháng", "Ngày"), key="drill_level")
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
                    mode="lines+markers",
                    line=dict(color=REVIEW, width=2),
                    marker=dict(color="#c8963e", size=8),
                    customdata=grouped["reviewed_orders"],
                    hovertemplate="%{x}<br>Review xấu %{y:.1%}<br>n %{customdata:,.0f}<extra></extra>",
                )
            )
            apply_theme(fig, 360)
            fig.update_yaxes(tickformat=".0%", title="Review xấu")
            st.plotly_chart(fig, width="stretch")
    with side:
        _panel("Kỳ nào review xấu nổi hơn các kỳ quanh nó?", lines)


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
        chosen = st.selectbox("Nhóm danh mục", names, index=names.index(preferred), key="slice_group")
        minimum = st.slider("min_orders", min_value=1, max_value=50, value=5, key="slice_min")
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
                    marker_color="#c8963e",
                    customdata=list(zip(plot["seller_id"], plot["eligible_orders"])),
                    hovertemplate="%{customdata[0]}<br>Giao trễ %{x:.1%}<br>n %{customdata[1]:,.0f}<extra></extra>",
                )
            )
            apply_theme(fig, max(280, 32 * len(plot) + 60))
            fig.update_xaxes(tickformat=".0%")
            fig.update_layout(margin=dict(l=90, r=12, t=24, b=12))
            st.plotly_chart(fig, width="stretch")
    with side:
        _panel("Trong một nhóm danh mục, seller nào giao trễ tới khách nhiều nhất?", lines)


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
            apply_theme(fig, max(320, 46 * len(kept) + 80))
            fig.update_xaxes(tickformat=".0%")
            fig.update_layout(barmode="group", margin=dict(l=120, r=12, t=24, b=12))
            st.plotly_chart(fig, width="stretch")
    with side:
        _panel("Ở lát cắt này, bang seller nào trễ và bị review xấu?", lines)


def _tab_pivot(frame: pd.DataFrame) -> None:
    data = frame.copy()
    data["late_items"] = pd.to_numeric(data["late_items"], errors="coerce")
    data["eligible_items"] = pd.to_numeric(data["eligible_items"], errors="coerce")
    data["late_rate"] = data["late_items"] / data["eligible_items"].where(data["eligible_items"] > 0)
    data["quarter_label"] = "Q" + data["quarter"].astype(int).astype(str)
    data["sort_key"] = data["category_group"].eq("Unknown").astype(int)
    categories = (
        data[["category_group", "sort_key"]]
        .drop_duplicates()
        .sort_values(["sort_key", "category_group"])["category_group"]
        .tolist()
    )
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    matrix = (
        data.pivot(index="category_group", columns="quarter_label", values="late_rate")
        .reindex(index=categories, columns=quarters)
    )
    counts = (
        data.pivot(index="category_group", columns="quarter_label", values="eligible_items")
        .reindex(index=categories, columns=quarters)
    )
    text = matrix.map(lambda value: "—" if pd.isna(value) else fmt_pct(value))
    peak = data.dropna(subset=["late_rate"]).sort_values("late_rate", ascending=False).head(1)
    lines = ["Mọi năm gộp vào cùng một quý. Unknown nằm cuối. Ô đậm hơn là quý trễ hơn."]
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
                    colorbar=dict(tickformat=".0%", title="Trễ"),
                )
            )
            apply_theme(fig, max(360, 42 * len(categories) + 80))
            fig.update_layout(margin=dict(l=210, r=16, t=24, b=16))
            fig.update_yaxes(automargin=True)
            st.plotly_chart(fig, width="stretch")
    with side:
        _panel("Nhóm danh mục nào kéo bàn giao trễ theo quý?", lines)


def render(settings=None) -> None:
    del settings
    page_header("OLAP Explorer", "Năm phép trên Gold. Mỗi tab là một câu hỏi nghiệp vụ.", "olap")
    _kpi_strip()
    with st.spinner("Đang hỏi SQL Warehouse..."):
        rollup, rollup_error = _load(lambda: db.query(*queries.rollup()))
        drill, drill_error = _load(lambda: db.query(*queries.drilldown()))
        groups, groups_error = _load(queries.category_groups)
        dice, dice_error = _load(lambda: db.query(*queries.dice()))
        pivot, pivot_error = _load(lambda: db.query(*queries.pivot_counts()))
    tabs = st.tabs(["Roll-up", "Drill-down", "Slice", "Dice", "Pivot"])
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
