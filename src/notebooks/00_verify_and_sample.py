"""Verify the Olist raw files and build a key-consistent sample.

Phase 0 helper (not ETL): run once after downloading the dataset into data/raw/.

    python src/notebooks/00_verify_and_sample.py            # verify + sample 5,000 orders
    python src/notebooks/00_verify_and_sample.py --orders 3000 --seed 7

Outputs:
  * a Markdown table (file, rows, columns, size) printed to stdout -> paste into data/README.md
  * differences vs. the expected file list
  * data/sample/*.csv with the same file names, keeping referential integrity:
    orders -> order_items / payments / reviews (by order_id)
           -> customers (by customer_id)
    order_items -> products (by product_id), sellers (by seller_id)
    customers + sellers -> geolocation (by zip_code_prefix)
    product_category_name_translation is copied in full (small lookup).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
EXTERNAL = ROOT / "data" / "external"
SAMPLE = ROOT / "data" / "sample"

EXPECTED = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def read(name: str) -> pd.DataFrame:
    # keep ids/zip prefixes as strings (leading zeros matter)
    return pd.read_csv(RAW / name, dtype=str, keep_default_na=True)


def verify() -> None:
    found = sorted(p.name for p in RAW.glob("*.csv"))
    missing = sorted(set(EXPECTED) - set(found))
    extra = sorted(set(found) - set(EXPECTED))
    print("| File | Rows | Columns | Size (MB) |\n|---|---:|---:|---:|")
    for name in found:
        df = read(name)
        size_mb = (RAW / name).stat().st_size / 1_048_576
        print(f"| `{name}` | {len(df):,} | {df.shape[1]} | {size_mb:.2f} |")
    print(f"\nMissing vs expected: {missing or 'none'}")
    print(f"Extra vs expected:   {extra or 'none'}")
    if missing:
        raise SystemExit("Cannot build sample: expected files are missing.")

    orders = read("olist_orders_dataset.csv")
    ts = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce")
    print(
        f"\norder_purchase_timestamp: min={ts.min()} max={ts.max()} "
        f"(non-null={int(ts.notna().sum()):,}/{len(orders):,})"
    )

    ext_found = sorted(p.name for p in EXTERNAL.glob("*.csv"))
    print("\n| External file | Rows | Columns | Size (MB) |\n|---|---:|---:|---:|")
    if not ext_found:
        print("| _(none)_ | | | |")
    for name in ext_found:
        df = pd.read_csv(EXTERNAL / name, dtype=str, keep_default_na=True)
        size_mb = (EXTERNAL / name).stat().st_size / 1_048_576
        print(f"| `{name}` | {len(df):,} | {df.shape[1]} | {size_mb:.2f} |")


def build_sample(n_orders: int, seed: int) -> None:
    SAMPLE.mkdir(parents=True, exist_ok=True)
    orders = read("olist_orders_dataset.csv")
    orders_s = orders.sample(n=min(n_orders, len(orders)), random_state=seed)
    oid = set(orders_s["order_id"])

    items = read("olist_order_items_dataset.csv")
    items_s = items[items["order_id"].isin(oid)]
    payments_s = read("olist_order_payments_dataset.csv").query("order_id in @oid")
    reviews_s = read("olist_order_reviews_dataset.csv").query("order_id in @oid")

    customers = read("olist_customers_dataset.csv")
    customers_s = customers[customers["customer_id"].isin(orders_s["customer_id"])]
    products_s = read("olist_products_dataset.csv").query("product_id in @items_s.product_id")
    sellers_s = read("olist_sellers_dataset.csv").query("seller_id in @items_s.seller_id")

    zips = set(customers_s["customer_zip_code_prefix"]) | set(sellers_s["seller_zip_code_prefix"])
    geo_s = read("olist_geolocation_dataset.csv").query("geolocation_zip_code_prefix in @zips")
    translation = read("product_category_name_translation.csv")

    out = {
        "olist_orders_dataset.csv": orders_s,
        "olist_order_items_dataset.csv": items_s,
        "olist_order_payments_dataset.csv": payments_s,
        "olist_order_reviews_dataset.csv": reviews_s,
        "olist_customers_dataset.csv": customers_s,
        "olist_products_dataset.csv": products_s,
        "olist_sellers_dataset.csv": sellers_s,
        "olist_geolocation_dataset.csv": geo_s,
        "product_category_name_translation.csv": translation,
    }
    for name, df in out.items():
        df.to_csv(SAMPLE / name, index=False)

    # integrity checks
    assert set(items_s["order_id"]) <= oid
    assert set(orders_s["customer_id"]) <= set(customers_s["customer_id"])
    assert set(items_s["product_id"]) <= set(products_s["product_id"])
    assert set(items_s["seller_id"]) <= set(sellers_s["seller_id"])
    print("\nIntegrity asserts: passed")
    print(f"\nSample written to data/sample/ (n_orders={len(orders_s):,}, seed={seed}):")
    for name, df in out.items():
        print(f"  {name}: {len(df):,} rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--orders", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    verify()
    build_sample(args.orders, args.seed)
