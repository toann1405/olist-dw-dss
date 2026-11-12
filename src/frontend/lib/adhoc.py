"""Ad hoc measure × dimension queries. Fragments are fixed. Filter values stay in parameters."""

from __future__ import annotations

from lib import db

# (value SQL, fact, format). Rates are SUM(numerator) / SUM(denominator), the same
# expressions as kpi_seller_month / seller_month_series / the roll-up item flag.
# "item" matches 01_rollup_seller_late_handoff.sql. The monthly fact has no product.
MEASURES: dict[str, tuple[str, str, str]] = {
    "GMV": ("SUM(f.gmv)", "seller_month", "brl"),
    "Số đơn hợp lệ": ("SUM(f.n_orders_valid)", "seller_month", "int"),
    "AOV": (
        "CASE WHEN SUM(f.n_orders_valid) > 0 THEN SUM(f.gmv) / SUM(f.n_orders_valid) END",
        "seller_month",
        "brl",
    ),
    "Tỷ lệ bàn giao trễ": (
        "CASE WHEN SUM(CASE WHEN i.seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) > 0 "
        "THEN SUM(CASE WHEN i.seller_ship_late_flag = 1 THEN 1 ELSE 0 END) "
        "/ SUM(CASE WHEN i.seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END) END",
        "item",
        "pct",
    ),
    "Tỷ lệ giao trễ tới khách": (
        "CASE WHEN SUM(f.late_delivery_eligible) > 0 "
        "THEN SUM(f.late_delivery_count) / SUM(f.late_delivery_eligible) END",
        "seller_month",
        "pct",
    ),
    "Review xấu": (
        "CASE WHEN SUM(f.negative_review_eligible) > 0 "
        "THEN SUM(f.negative_review_count) / SUM(f.negative_review_eligible) END",
        "seller_month",
        "pct",
    ),
}

# Sample size for the fade rule. Not a second measure.
_SAMPLE = {
    "GMV": "SUM(f.n_orders_valid)",
    "Số đơn hợp lệ": "SUM(f.n_orders_valid)",
    "AOV": "SUM(f.n_orders_valid)",
    "Tỷ lệ bàn giao trễ": "SUM(CASE WHEN i.seller_ship_late_flag IS NOT NULL THEN 1 ELSE 0 END)",
    "Tỷ lệ giao trễ tới khách": "SUM(f.late_delivery_eligible)",
    "Review xấu": "SUM(f.negative_review_eligible)",
}

# (SQL column, extra join). Time columns are the monthly-fact form; items rewrite them.
DIMENSIONS: dict[str, tuple[str, str]] = {
    "Vùng": ("s.region_name", "seller"),
    "Bang": ("s.state_code", "seller"),
    "Nhóm danh mục": ("p.category_group", "product"),
    "Năm": ("m.year", "time"),
    "Quý": ("m.quarter", "time"),
    "Tháng": ("m.year_month", "time"),
}

_FACT_JOINS = {
    "seller_month": frozenset({"seller", "time"}),
    "item": frozenset({"seller", "time", "product"}),
}
_TIME_DIMS = frozenset({"Năm", "Quý", "Tháng"})
_ITEM_TIME = {
    "Năm": "d.year",
    "Quý": "d.quarter",
    "Tháng": "format_string('%04d-%02d', d.year, d.month)",
}


def _expr(fact: str, name: str) -> str:
    column, kind = DIMENSIONS[name]
    if fact == "item" and kind == "time":
        return _ITEM_TIME[name]
    return column


def build_query(measure: str, dims: list[str], filters: dict | None = None) -> tuple[str, tuple]:
    """One grouped query. User text is never concatenated into the SQL."""
    if measure not in MEASURES:
        raise ValueError("measure is not in the list")
    chosen = list(dims or [])
    if not 1 <= len(chosen) <= 2 or len(set(chosen)) != len(chosen):
        raise ValueError("choose one or two different dimensions")
    for name in chosen:
        if name not in DIMENSIONS:
            raise ValueError("dimension is not in the list")
    value_sql, fact, _fmt = MEASURES[measure]
    allowed = _FACT_JOINS[fact]
    scope = dict(filters or {})
    joins = {DIMENSIONS[name][1] for name in chosen}
    if scope.get("region"):
        joins.add("seller")
    if scope.get("month_from") or scope.get("month_to"):
        joins.add("time")
    if scope.get("category"):
        joins.add("product")
    if not joins <= allowed:
        raise ValueError("measure and dimension are not on the same fact")

    cfg = db.settings()
    marker = db.marker()
    catalog, gold = cfg["catalog"], cfg["gold"]
    select = []
    group = []
    for index, name in enumerate(chosen, start=1):
        expr = _expr(fact, name)
        select.append(f"{expr} AS dim_{index}")
        group.append(expr)
    select.append(f"{value_sql} AS value")
    select.append(f"{_SAMPLE[measure]} AS n")

    params: list = []
    where = []

    if fact == "seller_month":
        source = (
            f"FROM {catalog}.{gold}.fact_seller_monthly AS f "
            f"INNER JOIN {catalog}.{gold}.dim_month AS m ON f.month_key = m.month_key "
            f"INNER JOIN {catalog}.{gold}.dim_seller AS s ON f.seller_key = s.seller_key"
        )
        where.append("f.seller_key <> -1 AND m.month_key <> -1 AND s.seller_key <> -1")
        where.append(f"({marker} IS NULL OR m.year_month >= {marker})")
        params.extend((scope.get("month_from"), scope.get("month_from")))
        where.append(f"({marker} IS NULL OR m.year_month <= {marker})")
        params.extend((scope.get("month_to"), scope.get("month_to")))
        where.append(f"({marker} IS NULL OR s.region_name = {marker})")
        params.extend((scope.get("region"), scope.get("region")))
    else:
        tables = [
            f"FROM {catalog}.{gold}.fact_order_item AS i",
        ]
        where.append("i.seller_key <> -1")
        if "seller" in joins:
            tables.append(
                f"INNER JOIN {catalog}.{gold}.dim_seller AS s ON i.seller_key = s.seller_key"
            )
            where.append("s.seller_key <> -1")
        if "time" in joins:
            tables.append(
                f"INNER JOIN {catalog}.{gold}.dim_date AS d ON i.purchase_date_key = d.date_key"
            )
            where.append("d.date_key <> -1")
            month_expr = "format_string('%04d-%02d', d.year, d.month)"
            where.append(f"({marker} IS NULL OR {month_expr} >= {marker})")
            params.extend((scope.get("month_from"), scope.get("month_from")))
            where.append(f"({marker} IS NULL OR {month_expr} <= {marker})")
            params.extend((scope.get("month_to"), scope.get("month_to")))
        if "product" in joins:
            tables.append(
                f"INNER JOIN {catalog}.{gold}.dim_product AS p ON i.product_key = p.product_key"
            )
            where.append("p.product_key <> -1")
            where.append(f"({marker} IS NULL OR p.category_group = {marker})")
            params.extend((scope.get("category"), scope.get("category")))
        if "seller" in joins:
            where.append(f"({marker} IS NULL OR s.region_name = {marker})")
            params.extend((scope.get("region"), scope.get("region")))
        source = " ".join(tables)

    if any(name in _TIME_DIMS for name in chosen):
        order = ", ".join(f"dim_{index}" for index in range(1, len(chosen) + 1))
    else:
        order = "value DESC"
    sql = (
        "SELECT "
        + ", ".join(select)
        + " "
        + source
        + " WHERE "
        + " AND ".join(where)
        + " GROUP BY "
        + ", ".join(group)
        + " ORDER BY "
        + order
        + " LIMIT 500"
    )
    return sql, tuple(params)
