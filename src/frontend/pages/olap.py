"""Five OLAP operators in tabs. The SQL files keep the locked questions."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import adhoc, db, queries
from lib.glossary import explain
from lib.ui import (
    LATE,
    MIN_N_DISPLAY,
    NEUTRAL,
    REVIEW,
    add_legend_swatch,
    button_dropdown,
    filters,
    fmt_brl,
    fmt_int,
    fmt_pct,
    kpi_card,
    next_step,
    page_header,
    style_fig,
)

DICE_MIN_N = MIN_N_DISPLAY
# Fixed pixels above the plot: title, subtitle, then the legend. Not a fraction of figure height.
_ROLLUP_MARGIN_TOP = 168
_ROLLUP_LEGEND_GAP = 96
_LEVEL_LABEL = {"region": "Vùng", "state": "Bang", "city": "Thành phố"}
_CATEGORY_GROUP_VI = {
    "home_furniture_decor": "Nhà cửa và nội thất",
    "health_beauty_fashion": "Sức khỏe, làm đẹp và thời trang",
    "electronics_it_telephony": "Điện tử, tin học và điện thoại",
    "sports_leisure_toys": "Thể thao, giải trí và đồ chơi",
    "auto_tools_construction": "Ô tô, dụng cụ và xây dựng",
    "books_stationery_media": "Sách, văn phòng phẩm và media",
    "baby_pets_food_drinks": "Mẹ và bé, thú cưng, thực phẩm",
    "services_others": "Dịch vụ và nhóm khác",
}


def _category_label(code: str) -> str:
    return _CATEGORY_GROUP_VI.get(str(code), str(code))


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


def _panel(headline: str, reading: str, frame: pd.DataFrame | None = None, key: str = "") -> None:
    st.markdown(f"**{headline}**")
    st.write(reading)
    if frame is not None and key and st.toggle("Xem bảng", key=key):
        st.dataframe(frame, width="stretch", hide_index=True)
        st.download_button(
            "Tải CSV",
            frame.to_csv(index=False).encode("utf-8"),
            file_name=f"{key}.csv",
            mime="text/csv",
        )


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
) -> go.Figure:
    numeric = [float(value) for value in rates]
    peak = max(numeric) if numeric else None
    colors = [color if peak is not None and rate == peak else NEUTRAL for rate in numeric]
    fig = go.Figure(
        go.Bar(
            x=rates,
            y=labels,
            orientation="h",
            name=axis_title,
            showlegend=False,
            marker=dict(color=colors),
            customdata=samples,
            hovertemplate="%{y}<br>" + axis_title + " %{x:.1%}<br>n %{customdata:,.0f}<extra></extra>",
        )
    )
    add_legend_swatch(fig, "Cao nhất", color)
    add_legend_swatch(fig, "Các nhóm còn lại", NEUTRAL)
    fig.update_layout(height=max(280, 34 * len(labels) + 120), margin_l=160, margin_r=16, margin_b=16)
    fig.update_xaxes(tickformat=".0%", title=axis_title)
    fig.update_yaxes(title="Nơi bán", automargin=True)
    styled = style_fig(fig, question, subtitle, legend_side="top")
    # Anchor to the plot edge, not to a fraction of the figure. A tall state or city
    # chart then keeps the same gap under "Xem" as the short region chart.
    styled.update_layout(
        margin=dict(t=_ROLLUP_MARGIN_TOP, r=16),
        title=dict(
            y=1,
            yanchor="bottom",
            yref="paper",
            pad=dict(b=_ROLLUP_LEGEND_GAP, t=0, l=0, r=0),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            yref="paper",
            x=0,
            xanchor="left",
        ),
    )
    return styled


def _kpi_strip() -> None:
    month_from, month_to, region, state, _category = filters()
    try:
        monthly = db.query(*queries.kpi_seller_month(month_from, month_to, region, state)).iloc[0]
        orders = db.query(*queries.kpi_orders(month_from, month_to, region, state)).iloc[0]
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
        quality = db.query(*queries.market_quality(month_from, month_to, region, state))
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
        level = button_dropdown(
            "Mức",
            ("region", "state", "city"),
            "olap_level",
            format_func=lambda value: _LEVEL_LABEL.get(value, value),
        )
    part = _place_label(frame[frame["rollup_level"] == level].copy(), level)
    part["late_ship_rate"] = pd.to_numeric(part["late_ship_rate"], errors="coerce")
    part["eligible_items"] = pd.to_numeric(part["eligible_items"], errors="coerce")
    shown = part.dropna(subset=["late_ship_rate"])
    counts = pd.to_numeric(shown["eligible_items"], errors="coerce").fillna(0)
    qualified = shown[counts >= MIN_N_DISPLAY]
    chart_rows = shown.sort_values("eligible_items", ascending=False).head(20) if level == "city" else shown
    chart_counts = pd.to_numeric(chart_rows["eligible_items"], errors="coerce").fillna(0)
    hidden = int((chart_counts < MIN_N_DISPLAY).sum())
    drawn = chart_rows.loc[chart_counts >= MIN_N_DISPLAY]
    top = qualified.sort_values("late_ship_rate", ascending=False).head(1)
    if top.empty:
        headline = "Chưa đủ dữ liệu để kết luận."
    else:
        row = top.iloc[0]
        headline = f"{row['axis']} cao nhất: {fmt_pct(row['late_ship_rate'])} (n={fmt_int(row['eligible_items'])})."
    if level == "city":
        reading = (
            "Đây là roll-up, mức thành phố chỉ vẽ 20 nơi có nhiều item nhất. "
            "Cột dài hơn là tỷ lệ bàn giao trễ cao hơn."
        )
    else:
        reading = (
            "Đây là roll-up: gộp từ thành phố lên bang rồi vùng. "
            "Cột dài hơn là tỷ lệ bàn giao trễ cao hơn."
        )
    with chart_col:
        mode = _view("rollup_view")
        if mode == "Bảng":
            st.dataframe(part, width="stretch", hide_index=True)
        elif drawn.empty:
            st.info("Không có tỷ lệ để vẽ.")
            st.caption(f"Ẩn {hidden} nhóm có dưới {MIN_N_DISPLAY} mẫu")
        else:
            ordered = drawn.sort_values("late_ship_rate")
            st.plotly_chart(
                _hbar(
                    ordered["axis"],
                    ordered["late_ship_rate"],
                    ordered["eligible_items"],
                    LATE,
                    "Bàn giao trễ (%)",
                    "Bàn giao trễ là chuyện cả vùng hay một nơi?",
                    f"Mức {_LEVEL_LABEL.get(level, level)} · mọi năm · không theo bộ lọc sidebar",
                ),
                width="stretch",
            )
            st.caption(f"Ẩn {hidden} nhóm có dưới {MIN_N_DISPLAY} mẫu")
    with side:
        _panel(headline, reading, part, "rollup_table")


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
    reviewed = pd.to_numeric(grouped["reviewed_orders"], errors="coerce").fillna(0)
    peak = grouped.loc[reviewed >= MIN_N_DISPLAY].sort_values("negative_review_rate", ascending=False).head(1)
    if peak.empty:
        headline = "Chưa đủ dữ liệu để kết luận."
    else:
        row = peak.iloc[0]
        label = row["axis"] if level != "Ngày" else str(row["full_date"])[:10]
        headline = f"{label} cao nhất: {fmt_pct(row['negative_review_rate'])} (n={fmt_int(row['reviewed_orders'])})."
    reading = (
        "Đây là drill-down: từ năm xuống quý, tháng, rồi ngày. "
        "Điểm cao hơn các kỳ quanh nó là kỳ review xấu nổi hơn."
    )
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
                    marker=dict(
                        color="#c8963e",
                        size=8,
                        opacity=[0.35 if count < MIN_N_DISPLAY else 1 for count in reviewed],
                    ),
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
            st.caption(f"Điểm mờ: dưới {MIN_N_DISPLAY} mẫu")
    with side:
        _panel(headline, reading, grouped, "drill_table")


def _tab_slice(groups: pd.DataFrame) -> None:
    names = [
        name
        for name in groups["category_group"].dropna().astype(str).tolist()
        if name != "Unknown"
    ]
    chart_col, side = st.columns([2, 1])
    _month_from, _month_to, _region, _state, category = filters()
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
            format_func=_category_label,
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
    order_counts = pd.to_numeric(data["eligible_orders"], errors="coerce").fillna(0)
    hidden = int((order_counts < MIN_N_DISPLAY).sum())
    ranked = data.loc[order_counts >= MIN_N_DISPLAY]
    top = ranked.head(15)
    if ranked.empty:
        headline = "Chưa đủ dữ liệu để kết luận."
    else:
        row = ranked.iloc[0]
        headline = (
            f"{row['short_id']} cao nhất: {fmt_pct(row['late_delivery_rate'])} "
            f"(n={fmt_int(row['eligible_orders'])})."
        )
    reading = (
        f"Đây là slice: giữ nhóm {_category_label(chosen)} và so seller trong nhóm đó. "
        "Cột dài hơn là tỷ lệ giao trễ tới khách cao hơn."
    )
    with chart_col:
        mode = _view("slice_view")
        if mode == "Bảng":
            show = data.copy()
            show["seller"] = show["seller_id"].astype(str).str.slice(0, 8)
            st.dataframe(show, width="stretch", hide_index=True)
        elif top.empty:
            st.info("Không có seller qua ngưỡng đơn.")
            st.caption(f"Ẩn {hidden} nhóm có dưới {MIN_N_DISPLAY} mẫu")
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
                    f"Nhóm {_category_label(chosen)} · ít nhất {minimum} đơn đủ mẫu · không theo bộ lọc sidebar",
                ),
                width="stretch",
            )
            st.caption(f"Ẩn {hidden} nhóm có dưới {MIN_N_DISPLAY} mẫu")
    with side:
        _panel(headline, reading, data, "slice_table")


def _tab_dice(frame: pd.DataFrame) -> None:
    data = frame.copy()
    for column in ("late_delivery_rate", "seller_negative_review_rate", "late_eligible_orders", "review_eligible_orders"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["n"] = data["late_eligible_orders"].fillna(0)
    hidden = int((data["n"] < MIN_N_DISPLAY).sum())
    kept = data[data["n"] >= DICE_MIN_N].copy()
    if kept.empty:
        headline = "Chưa đủ dữ liệu để kết luận."
    else:
        row = kept.sort_values("late_delivery_rate", ascending=False).iloc[0]
        headline = (
            f"{row['state_code']} giao trễ cao nhất: {fmt_pct(row['late_delivery_rate'])} "
            f"(n={fmt_int(row['n'])})."
        )
    reading = (
        "Đây là dice: cắt cùng lúc khách Norte hoặc Nordeste, quý 1–2/2018 và hàng bulky. "
        "Mỗi bang có hai thanh, giao trễ tới khách và review xấu."
    )
    chart_col, side = st.columns([2, 1])
    with chart_col:
        mode = _view("dice_view")
        if mode == "Bảng":
            st.dataframe(data, width="stretch", hide_index=True)
        elif kept.empty:
            st.info("Không có bang qua ngưỡng mẫu.")
            st.caption(f"Ẩn {hidden} nhóm có dưới {MIN_N_DISPLAY} mẫu")
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
            st.caption(f"Ẩn {hidden} nhóm có dưới {MIN_N_DISPLAY} mẫu")
    with side:
        _panel(headline, reading, data, "dice_table")


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
    if peak.empty:
        headline = "Chưa đủ dữ liệu để kết luận."
    else:
        row = peak.iloc[0]
        headline = (
            f"{_category_label(row['category_group'])} {row['quarter_label']} cao nhất: "
            f"{fmt_pct(row['late_rate'])} (n={fmt_int(row['eligible_items'])})."
        )
    reading = (
        "Đây là pivot: xoay sang nhóm danh mục theo quý, mọi năm gộp lại. "
        "Ô đậm hơn là tỷ lệ bàn giao trễ cao hơn; ô trống là mẫu dưới ngưỡng hiển thị."
    )
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
                    y=[_category_label(name) for name in categories],
                    colorscale=[[0, "#f6f1e7"], [0.5, "#e7b089"], [1, LATE]],
                    customdata=counts.values,
                    text=text.values,
                    texttemplate="%{text}",
                    hovertemplate="%{y} %{x}<br>%{z:.1%}<br>n %{customdata:,.0f}<extra></extra>",
                    colorbar=dict(tickformat=".0%", title="Bàn giao trễ (%)"),
                )
            )
            fig.update_layout(height=max(380, 42 * len(categories) + 120), margin_l=210, margin_r=16, margin_b=16)
            fig.update_xaxes(title="Quý")
            fig.update_yaxes(title="Nhóm danh mục", automargin=True)
            st.plotly_chart(
                style_fig(
                    fig,
                    "Nhóm danh mục nào kéo bàn giao trễ theo quý?",
                    f"Mọi năm gộp theo quý · ô trống khi dưới {MIN_N_DISPLAY} mẫu · không theo bộ lọc sidebar",
                ),
                width="stretch",
            )
    with side:
        _panel(headline, reading, data, "pivot_table")


def _olap_conclusion(frame: pd.DataFrame | None) -> str:
    if frame is None or frame.empty or "rollup_level" not in frame.columns:
        return "Chưa đủ dữ liệu để kết luận."
    part = frame[frame["rollup_level"] == "region"].copy()
    part["late_ship_rate"] = pd.to_numeric(part["late_ship_rate"], errors="coerce")
    part["eligible_items"] = pd.to_numeric(part["eligible_items"], errors="coerce").fillna(0)
    part = part.dropna(subset=["late_ship_rate"])
    part = part[part["eligible_items"] >= MIN_N_DISPLAY]
    if part.empty:
        return "Chưa đủ dữ liệu để kết luận."
    row = part.sort_values(["late_ship_rate"], ascending=False).iloc[0]
    name = row["region_name"] if "region_name" in row.index else "không rõ"
    return f"Vùng {name} có tỷ lệ bàn giao trễ cao nhất ({fmt_pct(row['late_ship_rate'])})."


def _adhoc_label(dim_name: str, value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "(trống)"
    text = str(value)
    if dim_name == "Nhóm danh mục":
        return _category_label(text)
    if dim_name == "Quý":
        return f"Q{text}"
    return text


def _adhoc_text(value, kind: str) -> str:
    if kind == "brl":
        return fmt_brl(value)
    if kind == "pct":
        return fmt_pct(value)
    return fmt_int(value)


def _tab_adhoc() -> None:
    chart_col, side = st.columns([2, 1])
    with side:
        measure = button_dropdown("Chỉ số", tuple(adhoc.MEASURES), "adhoc_measure")
        dim_1 = button_dropdown("Chiều 1", tuple(adhoc.DIMENSIONS), "adhoc_dim_1")
        second = ["(không)"] + [name for name in adhoc.DIMENSIONS if name != dim_1]
        dim_2_label = button_dropdown("Chiều 2", second, "adhoc_dim_2")
        try:
            month_frame = db.query(*queries.months())
            region_frame = db.query(*queries.regions())
            group_frame = queries.category_groups()
        except Exception as exc:
            st.error(db.redact(exc))
            return
        months = ["Tất cả"] + month_frame["year_month"].dropna().astype(str).tolist()
        regions = ["Tất cả"] + region_frame["region_name"].dropna().astype(str).tolist()
        groups = ["Tất cả"] + [
            name
            for name in group_frame["category_group"].dropna().astype(str).tolist()
            if name != "Unknown"
        ]
        month_from = button_dropdown("Từ tháng", months, "adhoc_from")
        month_to = button_dropdown("Đến tháng", months, "adhoc_to")
        region = button_dropdown("Vùng", regions, "adhoc_region")
        category = button_dropdown(
            "Nhóm danh mục",
            groups,
            "adhoc_category",
            format_func=lambda name: "Tất cả" if name == "Tất cả" else _category_label(name),
        )
    dims = [dim_1] if dim_2_label in (None, "(không)") else [dim_1, dim_2_label]
    scope = {
        "month_from": None if month_from in (None, "Tất cả") else month_from,
        "month_to": None if month_to in (None, "Tất cả") else month_to,
        "region": None if region in (None, "Tất cả") else region,
        "category": None if category in (None, "Tất cả") else category,
    }
    try:
        sql, params = adhoc.build_query(measure, dims, scope)
    except ValueError:
        with chart_col:
            st.info("Chỉ số này không gắn được với chiều đã chọn.")
        with side:
            st.warning("Tổ hợp chỉ số và chiều không cùng một bảng fact.")
        return
    try:
        frame = db.query(sql, params)
    except Exception as exc:
        with chart_col:
            st.error(db.redact(exc))
        return
    kind = adhoc.MEASURES[measure][2]
    work = frame.copy()
    for column in ("value", "n"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
    one = "Đường" if dims == ["Tháng"] or dims == ["Quý"] else "Cột"
    with chart_col:
        if len(dims) == 1:
            mode = st.segmented_control("Xem", ["Cột", "Đường", "Bảng"], default=one, key=f"adhoc_one_{dims[0]}")
        else:
            mode = st.segmented_control("Xem", ["Heatmap", "Bảng"], default="Heatmap", key="adhoc_two")
        if work.empty:
            st.info("Không có dòng cho bộ lọc này.")
        elif mode == "Bảng" and len(dims) == 1:
            st.dataframe(work, width="stretch", hide_index=True)
        elif mode == "Bảng":
            matrix = work.pivot(index="dim_1", columns="dim_2", values="value")
            st.dataframe(matrix, width="stretch")
        elif len(dims) == 1 and mode == "Đường":
            labels = [_adhoc_label(dims[0], value) for value in work["dim_1"]]
            opacity = [0.35 if (n or 0) < MIN_N_DISPLAY else 1 for n in work["n"]]
            figure = go.Figure(
                go.Scatter(
                    x=labels,
                    y=work["value"],
                    mode="lines+markers",
                    name=measure,
                    marker=dict(color=LATE, opacity=opacity, size=8),
                    line=dict(color=LATE, width=2),
                    customdata=work["n"],
                    hovertemplate="%{x}<br>%{y}<br>n %{customdata:,.0f}<extra></extra>",
                )
            )
            figure.update_layout(height=360)
            figure.update_xaxes(title=dims[0])
            figure.update_yaxes(title=measure)
            st.plotly_chart(
                style_fig(figure, f"{measure} theo {dims[0]}", "Tự chọn · tối đa 500 dòng"),
                width="stretch",
            )
            st.caption(f"Điểm mờ: dưới {MIN_N_DISPLAY} mẫu")
        elif len(dims) == 1:
            labels = [_adhoc_label(dims[0], value) for value in work["dim_1"]]
            samples = pd.to_numeric(work["n"], errors="coerce").fillna(0)
            hidden = int((samples < MIN_N_DISPLAY).sum())
            keep = (samples >= MIN_N_DISPLAY).tolist()
            labels = [label for label, flag in zip(labels, keep) if flag]
            values = [value for value, flag in zip(work["value"].tolist(), keep) if flag]
            kept_n = [value for value, flag in zip(samples.tolist(), keep) if flag]
            if not labels:
                st.info("Không có nhóm đủ mẫu.")
            else:
                figure = _hbar(
                    labels,
                    values,
                    kept_n,
                    LATE,
                    measure,
                    f"{measure} theo {dims[0]}",
                    "Tự chọn · tối đa 500 dòng",
                )
                if kind != "pct":
                    figure.update_xaxes(tickformat=",.0f", tickprefix="" if kind == "int" else "R$ ")
                st.plotly_chart(figure, width="stretch")
            st.caption(f"Ẩn {hidden} nhóm có dưới {MIN_N_DISPLAY} mẫu")
        else:
            counts = work.pivot(index="dim_1", columns="dim_2", values="n")
            matrix = work.pivot(index="dim_1", columns="dim_2", values="value")
            matrix = matrix.where(counts >= MIN_N_DISPLAY)
            text = matrix.map(lambda value: "—" if pd.isna(value) else _adhoc_text(value, kind))
            y_labels = [_adhoc_label(dims[0], value) for value in matrix.index]
            x_labels = [_adhoc_label(dims[1], value) for value in matrix.columns]
            figure = go.Figure(
                go.Heatmap(
                    z=matrix.values,
                    x=x_labels,
                    y=y_labels,
                    colorscale=[[0, "#f6f1e7"], [0.5, "#e7b089"], [1, LATE]],
                    text=text.values,
                    texttemplate="%{text}",
                    hovertemplate="%{y} · %{x}<br>%{text}<extra></extra>",
                )
            )
            figure.update_layout(height=max(360, 36 * len(y_labels) + 120))
            figure.update_xaxes(title=dims[1])
            figure.update_yaxes(title=dims[0])
            st.plotly_chart(
                style_fig(
                    figure,
                    f"{measure} theo {dims[0]} × {dims[1]}",
                    f"ô trống khi dưới {MIN_N_DISPLAY} mẫu",
                ),
                width="stretch",
            )
    qualified = work.dropna(subset=["value"])
    big = qualified[qualified["n"] >= MIN_N_DISPLAY]
    if big.empty:
        headline = "Chưa đủ dữ liệu để kết luận."
    else:
        row = big.sort_values("value", ascending=False).iloc[0]
        label = _adhoc_label(dims[0], row["dim_1"])
        if len(dims) == 2:
            label = f"{label} × {_adhoc_label(dims[1], row['dim_2'])}"
        headline = f"{label} cao nhất: {_adhoc_text(row['value'], kind)} (n={fmt_int(row['n'])})."
    reading = (
        "Đây là truy vấn tự lắp: một chỉ số và một hoặc hai chiều, không gõ SQL. "
        "Cột chỉ vẽ nhóm đủ mẫu. Điểm mờ và ô trống là mẫu dưới ngưỡng hiển thị."
    )
    with side:
        st.markdown(f"**{headline}**")
        st.write(reading)
        st.download_button(
            "Tải CSV",
            work.to_csv(index=False).encode("utf-8"),
            file_name="adhoc.csv",
            mime="text/csv",
        )
        with st.expander("Xem SQL"):
            st.code(sql, language="sql")
            st.caption(str(params))


def render(settings=None) -> None:
    del settings
    with st.spinner("Đang tải dữ liệu…"):
        rollup, rollup_error = _load(lambda: db.query(*queries.rollup()))
        drill, drill_error = _load(lambda: db.query(*queries.drilldown()))
        groups, groups_error = _load(queries.category_groups)
        dice, dice_error = _load(lambda: db.query(*queries.dice()))
        pivot, pivot_error = _load(lambda: db.query(*queries.pivot_counts()))
    page_header(
        "GMV và trải nghiệm xấu đến từ đâu?",
        _olap_conclusion(rollup),
        "actual",
    )
    st.caption("Năm phép này không theo bộ lọc sidebar.")
    _kpi_strip()
    tabs = st.tabs([
        "Vùng hay cục bộ? (Roll-up)",
        "Tháng nào nổi? (Drill-down)",
        "Seller nào trễ nhất? (Slice)",
        "Lát cắt Norte+Nordeste, Q1–Q2/2018, bulky (Dice)",
        "Nguồn gây trễ? (Pivot)",
        "Tự khám phá (Ad hoc)",
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
    with tabs[5]:
        _tab_adhoc()
    next_step("olap")
