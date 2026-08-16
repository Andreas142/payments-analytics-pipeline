#!/usr/bin/env python3
"""
Get the real Olist Brazilian E-Commerce CSVs into data/raw/.

Data source: "Brazilian E-Commerce Public Dataset by Olist" — real, anonymised
commercial data, ~100k orders (2016-2018). Licensed CC BY-NC-SA 4.0. See the
attribution note in the README before redistributing.

=============================================================================
RECOMMENDED (zero setup, no token, browser only):
    Open  https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
    click Download, then drag the 9 CSVs into data/raw/ and commit them.
    Nothing to install; works entirely in the Codespaces browser.
=============================================================================

Scripted options (for automation / CI):

  --source kaggle   (default)  Uses the Kaggle CLI. Needs a one-time API token:
                    download kaggle.json from your Kaggle account page and add
                    it as Codespaces secrets KAGGLE_USERNAME / KAGGLE_KEY, or
                    place it at ~/.config/kaggle/kaggle.json. Complete + reliable.

  --source mirror   No-auth GitHub mirror. Convenient but PARTIAL/UNRELIABLE:
                    public mirrors come and go and rarely host all 9 tables.
                    Only use to grab the core tables quickly for a first look.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

KAGGLE_SLUG = "olistbr/brazilian-ecommerce"

# Core tables the payments star schema + reconciliation actually need. A no-auth
# mirror may host only some of these; Kaggle has all 9 (incl. reviews/products/
# sellers/translation/geolocation).
CORE_FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
]
DEFAULT_MIRROR = "https://raw.githubusercontent.com/wheff70/OlistDataAnalysis/main"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch Olist CSVs into data/raw/.")
    p.add_argument("--source", choices=["kaggle", "mirror"], default="kaggle")
    p.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    p.add_argument("--base-url", default=DEFAULT_MIRROR,
                   help="mirror base URL (only used with --source mirror)")
    p.add_argument("--force", action="store_true")
    return p.parse_args()


def fetch_kaggle(out_dir: Path) -> None:
    cmd = ["kaggle", "datasets", "download", "-d", KAGGLE_SLUG,
           "-p", str(out_dir), "--unzip"]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("Kaggle CLI not found. `pip install kaggle` and add your API "
                 "token, or just download from the Kaggle website (see docstring).")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Kaggle download failed ({exc}). Check your API token, or "
                 "download from the Kaggle website (see docstring).")
    print(f"\nDone. CSVs are in {out_dir.resolve()}.")


def fetch_mirror(out_dir: Path, base_url: str, force: bool) -> None:
    print("NOTE: mirror mode is partial — only the core tables, if available.\n")
    for name in CORE_FILES:
        dest = out_dir / name
        if dest.exists() and not force:
            print(f"  skip (exists)  {name}")
            continue
        try:
            urllib.request.urlretrieve(f"{base_url}/{name}", dest)
            print(f"  downloaded     {name}  ({dest.stat().st_size / 1e6:.1f} MB)")
        except Exception as exc:  # noqa: BLE001
            print(f"  MISSING        {name}: {exc} -> get it from Kaggle",
                  file=sys.stderr)


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.source == "kaggle":
        fetch_kaggle(args.out_dir)
    else:
        fetch_mirror(args.out_dir, args.base_url, args.force)
    print("Next: python scripts/ingest.py   (lands typed Parquet for dbt)")


if __name__ == "__main__":
    main()
