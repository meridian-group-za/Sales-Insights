#!/usr/bin/env python3
"""Dump the same JSON shapes sales-data's API will eventually serve, straight
from sales.duckdb, into local files under mock-data/. Lets the dashboard be
built and viewed against real numbers before Entra ID sign-in (and the Azure
upload) are wired up -- see the DEV_MODE note in index.html.

Reuses sales_queries.py directly (not a reimplementation) so the mock JSON
can never drift from what the real API will return -- once DEV_MODE is
switched off, the page calls the identical functions over HTTP instead.
"""
import json
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path.home() / 'Downloads' / 'Workflow automation portal (2)' / 'backend' / 'azure-function'))
import sales_queries as sq

DB_PATH = Path.home() / 'OneDrive - Meridian Group' / 'Meridian Nexus - Documents' / 'Sales Insights' / 'data' / 'sales.duckdb'
OUT_DIR = Path(__file__).resolve().parent.parent / 'mock-data'


def dump(name, value):
    out = OUT_DIR / f'{name}.json'
    out.write_text(json.dumps(value, default=str), encoding='utf-8')
    print(f'wrote {out} ({len(json.dumps(value, default=str)):,} bytes)')


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=True)

    dump('meta', sq.get_meta(con))
    dump('summary', sq.get_summary(con, None, {}))
    dump('client_monthly', sq.get_client_monthly(con, None, {}))
    dump('province_monthly', sq.get_province_monthly(con, None, {}))
    dump('category_monthly', sq.get_category_monthly(con, None, {}))
    dump('categories', sq.get_categories(con, None, {}))
    dump('brands', sq.get_brands(con, None, {}))
    dump('rolling_summary', sq.get_rolling_summary(con, None, {}))
    dump('bucket_summary', sq.get_bucket_summary(con, None, {}))
    dump('banner_bucket_summary', sq.get_banner_bucket_summary(con, None, {}))
    dump('store_performance', sq.get_store_performance(con, None, {'limit': 500}))
    dump('dimension_region', sq.get_dimension_breakdown(con, None, {'dimension': 'region'}))
    dump('dimension_brand', sq.get_dimension_breakdown(con, None, {'dimension': 'brand'}))
    dump('dimension_banner', sq.get_dimension_breakdown(con, None, {'dimension': 'banner'}))
    dump('monthly_trend', sq.get_monthly_trend(con, None, {}))
    dump('price_mix', sq.get_price_mix(con, None, {}))
    dump('insights_stores_declining', sq.get_insights_stores(con, None, {'type': 'declining'}))
    dump('insights_stores_growing', sq.get_insights_stores(con, None, {'type': 'growing'}))
    dump('insights_stores_at_risk', sq.get_insights_stores(con, None, {'type': 'at_risk'}))
    dump('insights_brands', sq.get_insights_brands(con, None, {}))

    con.close()
    print('Done.')


if __name__ == '__main__':
    main()
