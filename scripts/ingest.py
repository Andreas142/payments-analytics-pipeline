#!/usr/bin/env python3
"""
Land the raw Olist CSVs as typed Parquet in data/landing/.

This is the ingestion (the E + L of ELT): read each source CSV once, parse the
timestamp columns, and write Parquet. dbt then reads these Parquet files as
`sources` and does all bronze/silver/gold transformation in SQL (Phase 2+).

Why Parquet and not just point dbt at the CSVs?
  - CSV is typeless: every column loads as text until you cast it. Parquet
    stores real types (timestamps stay timestamps), so dbt starts from clean,
    typed inputs.
  - Parquet is columnar and compressed: dbt runs read only the columns a model
    needs, which is faster on every build.
  - It gives you a genuine landing layer to talk about, mirroring how a real
    lakehouse lands raw files before transforming them.

This step is deliberately faithful ("as-is" copy + typing). It does NOT clean,
rename, dedupe, or apply business logic — that is dbt's job in the silver layer,
so the raw record stays auditable.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# For each source file, list the columns that should be parsed as timestamps.
# Everything else is left to pandas' type inference (numeric stays numeric).
SOURCES: dict[str, list[str]] = {
    "olist_customers_dataset": [],
    "olist_sellers_dataset": [],
    "olist_products_dataset": [],
    "product_category_name_translation": [],
    "olist_orders_dataset": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items_dataset": ["shipping_limit_date"],
    "olist_order_payments_dataset": [],
    "olist_order_reviews_dataset": ["review_creation_date", "review_answer_timestamp"],
    "olist_geolocation_dataset": [],  # only present if fetched with geolocation
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Land Olist CSVs as typed Parquet.")
    p.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--out-dir", type=Path, default=Path("data/landing"))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    landed = 0
    print(f"{'table':<38}{'rows':>10}{'cols':>7}   null key cols")
    print("-" * 78)
    for stem, date_cols in SOURCES.items():
        src = args.raw_dir / f"{stem}.csv"
        if not src.exists():
            continue  # skip anything not fetched (e.g. geolocation)

        df = pd.read_csv(src, parse_dates=date_cols or None)
        out = args.out_dir / f"{stem}.parquet"
        df.to_parquet(out, index=False)
        landed += 1

        # Tiny profile: flag columns that contain nulls, so you know upfront
        # where dbt's not_null tests and cleaning will need to focus.
        null_cols = [c for c in df.columns if df[c].isna().any()]
        null_note = ", ".join(null_cols) if null_cols else "(none)"
        print(f"{stem:<38}{len(df):>10,}{df.shape[1]:>7}   {null_note}")

    if landed == 0:
        raise SystemExit(
            "No CSVs found in data/raw/. Run: python scripts/fetch_data.py"
        )
    print("-" * 78)
    print(f"Landed {landed} tables as Parquet in {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()
