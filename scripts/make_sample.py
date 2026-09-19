#!/usr/bin/env python3
"""
Build a small, COHERENT sample of the Olist dataset for CI.

CI runs on a fresh machine with no data. Rather than download the full ~100k-order
dataset every run, we commit a small representative slice so CI is self-contained,
fast, and reproducible. The key is preserving REFERENTIAL INTEGRITY: we sample
orders first, then keep only the children (items/payments/reviews) and referenced
parents (customers/products/sellers) belonging to those orders, so every child
still points to a real parent and the full dbt test suite passes on the sample.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build a coherent Olist sample.")
    p.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--out-dir", type=Path, default=Path("data/sample"))
    p.add_argument("--n-orders", type=int, default=2000)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def read(raw_dir: Path, stem: str):
    path = raw_dir / f"{stem}.csv"
    if not path.exists():
        print(f"  skip (missing) {stem}")
        return None
    return pd.read_csv(path)


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    orders = read(args.raw_dir, "olist_orders_dataset")
    if orders is None:
        raise SystemExit("orders CSV not found; run fetch_data.py first.")

    n = min(args.n_orders, len(orders))
    orders_s = orders.sample(n=n, random_state=args.seed)
    keep_orders = set(orders_s["order_id"])
    keep_customers = set(orders_s["customer_id"])

    items = read(args.raw_dir, "olist_order_items_dataset")
    payments = read(args.raw_dir, "olist_order_payments_dataset")
    reviews = read(args.raw_dir, "olist_order_reviews_dataset")

    items_s = items[items["order_id"].isin(keep_orders)] if items is not None else None
    payments_s = payments[payments["order_id"].isin(keep_orders)] if payments is not None else None
    reviews_s = reviews[reviews["order_id"].isin(keep_orders)] if reviews is not None else None

    customers = read(args.raw_dir, "olist_customers_dataset")
    customers_s = customers[customers["customer_id"].isin(keep_customers)] if customers is not None else None

    products = read(args.raw_dir, "olist_products_dataset")
    sellers = read(args.raw_dir, "olist_sellers_dataset")
    if items_s is not None:
        keep_products = set(items_s["product_id"])
        keep_sellers = set(items_s["seller_id"])
        products_s = products[products["product_id"].isin(keep_products)] if products is not None else None
        sellers_s = sellers[sellers["seller_id"].isin(keep_sellers)] if sellers is not None else None
    else:
        products_s, sellers_s = products, sellers

    translation_s = read(args.raw_dir, "product_category_name_translation")

    outputs = {
        "olist_orders_dataset": orders_s,
        "olist_order_items_dataset": items_s,
        "olist_order_payments_dataset": payments_s,
        "olist_order_reviews_dataset": reviews_s,
        "olist_customers_dataset": customers_s,
        "olist_products_dataset": products_s,
        "olist_sellers_dataset": sellers_s,
        "product_category_name_translation": translation_s,
    }

    print(f"\n{'table':<38}{'rows':>10}")
    print("-" * 48)
    for stem, df in outputs.items():
        if df is None:
            continue
        df.to_csv(args.out_dir / f"{stem}.csv", index=False)
        print(f"{stem:<38}{len(df):>10,}")
    print("-" * 48)
    print(f"Coherent sample written to {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()
