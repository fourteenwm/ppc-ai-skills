#!/usr/bin/env python3
"""SQR N-Gram Analysis (optional): per-account 2-word and 3-word n-grams.

Reads the raw search terms from the "SQR" tab, aggregates metrics (clicks,
impressions, cost, conversions) for every 2-gram and 3-gram per account,
filters to a minimum impression threshold, and writes "2-NGram" and "3-NGram"
tabs for human review (mark "x" in the Include? column to negate a whole phrase).

This is an optional supplement to the per-query consensus tabs — useful for
spotting recurring junk phrases (e.g. "free", "jobs", "diy") that span many
queries. Brand names are pulled from the "3-3 Agree" tab if present.

Usage:
    python sqr_ngram_analysis.py --sheet-id YOUR_SHEET_ID
    python sqr_ngram_analysis.py --sheet-id YOUR_SHEET_ID --min-impressions 10

Prerequisites:
    - token.json at project root with Google Sheets scope (or set
      SHEETS_TOKEN_PATH env var)
    - an "SQR" tab populated by mcc_search_query_report.py (or your own pull)
    - pip install google-auth google-api-python-client
"""

import argparse
import os
import re
from collections import defaultdict
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SHEETS_TOKEN_PATH = Path(os.getenv("SHEETS_TOKEN_PATH", "./token.json"))
DEFAULT_MIN_IMPRESSIONS = 5


def format_cid(cid):
    digits = re.sub(r'\D', '', str(cid))
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return str(cid)


def get_ngrams(text, n):
    words = text.lower().split()
    if len(words) < n:
        return []
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]


def load_service():
    if not SHEETS_TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"Sheets token not found at {SHEETS_TOKEN_PATH.absolute()}\n"
            "Set up OAuth credentials first or set SHEETS_TOKEN_PATH env var.\n"
            "See the google-ads-api-setup skill for the walkthrough."
        )
    creds = Credentials.from_authorized_user_file(
        str(SHEETS_TOKEN_PATH), scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(SHEETS_TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)


def ensure_tab_exists(service, sheet_id, tab_name, num_cols=10):
    metadata = service.spreadsheets().get(
        spreadsheetId=sheet_id, fields='sheets.properties.title'
    ).execute()
    existing = [s['properties']['title'] for s in metadata.get('sheets', [])]
    if tab_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': [{'addSheet': {'properties': {
                'title': tab_name,
                'gridProperties': {'rowCount': 5000, 'columnCount': num_cols}
            }}}]}
        ).execute()
        print(f"  Created tab '{tab_name}'")


def clear_tab(service, sheet_id, tab_name):
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=sheet_id, range=f"'{tab_name}'!A:Z"
        ).execute()
    except Exception:
        pass


def ensure_sheet_size(service, sheet_id, tab_name, needed_rows, needed_cols=10):
    metadata = service.spreadsheets().get(
        spreadsheetId=sheet_id, fields='sheets.properties'
    ).execute()
    for sheet in metadata.get('sheets', []):
        props = sheet['properties']
        if props['title'] == tab_name:
            updates = {}
            if props['gridProperties']['rowCount'] < needed_rows:
                updates['rowCount'] = needed_rows + 100
            if props['gridProperties']['columnCount'] < needed_cols:
                updates['columnCount'] = needed_cols + 2
            if updates:
                service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': [{'updateSheetProperties': {
                        'properties': {'sheetId': props['sheetId'], 'gridProperties': updates},
                        'fields': ','.join(f'gridProperties.{k}' for k in updates)
                    }}]}
                ).execute()
            break


def write_tab(service, sheet_id, tab_name, header, rows_out):
    ensure_tab_exists(service, sheet_id, tab_name)
    clear_tab(service, sheet_id, tab_name)
    all_rows = [header] + rows_out
    ensure_sheet_size(service, sheet_id, tab_name, len(all_rows) + 10)
    BATCH_SIZE = 5000
    for i in range(0, len(all_rows), BATCH_SIZE):
        batch = all_rows[i:i + BATCH_SIZE]
        start_row = i + 1
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"'{tab_name}'!A{start_row}",
            valueInputOption='RAW',
            body={'values': batch}
        ).execute()
    print(f"  '{tab_name}': {len(rows_out)} data rows written")


def main():
    parser = argparse.ArgumentParser(description='SQR per-account n-gram analysis')
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID with the "SQR" tab')
    parser.add_argument('--sqr-tab', default='SQR',
                        help='Raw search-terms tab name (default: "SQR")')
    parser.add_argument('--min-impressions', type=int, default=DEFAULT_MIN_IMPRESSIONS,
                        help=f'Minimum impressions to keep an n-gram (default: {DEFAULT_MIN_IMPRESSIONS})')
    args = parser.parse_args()

    service = load_service()

    # Read SQR tab (Account ID, Account Name, Query, Clicks, Impressions, Cost, Conversions)
    print(f"Reading '{args.sqr_tab}' tab...")
    result = service.spreadsheets().values().get(
        spreadsheetId=args.sheet_id, range=f"'{args.sqr_tab}'!A:G"
    ).execute()
    rows = result.get('values', [])
    data = rows[1:]
    print(f"  {len(data)} search terms loaded")

    # Read brand lookup from "3-3 Agree" tab if present (A: CID, D: Brand Names)
    brand_lookup = {}
    try:
        brand_result = service.spreadsheets().values().get(
            spreadsheetId=args.sheet_id, range="'3-3 Agree'!A:D"
        ).execute()
        for row in brand_result.get('values', [])[1:]:
            if len(row) >= 4:
                cid = re.sub(r'\D', '', row[0])
                if cid and row[3]:
                    brand_lookup[cid] = row[3]
    except Exception:
        pass

    # Build ngram data per account
    print("Building ngram analysis per account...")
    ngram_data = {
        2: defaultdict(lambda: {'clicks': 0, 'impressions': 0, 'cost': 0.0, 'conversions': 0.0, 'count': 0}),
        3: defaultdict(lambda: {'clicks': 0, 'impressions': 0, 'cost': 0.0, 'conversions': 0.0, 'count': 0})
    }

    for row in data:
        if len(row) < 7:
            continue
        acct_id = row[0].strip()
        acct_name = row[1].strip()
        query = row[2].strip()
        try:
            clicks = int(row[3])
            impressions = int(row[4])
            cost = float(row[5])
            conversions = float(row[6])
        except (ValueError, IndexError):
            continue

        for n in [2, 3]:
            for ngram in get_ngrams(query, n):
                key = (acct_id, acct_name, ngram)
                d = ngram_data[n][key]
                d['clicks'] += clicks
                d['impressions'] += impressions
                d['cost'] += cost
                d['conversions'] += conversions
                d['count'] += 1

    HEADER = ["CID", "NGram", "Account", "Brand Names",
              "Clicks", "Impressions", "Cost", "Conversions",
              "Include?", "Count"]

    def build_output_rows(n):
        rows_out = []
        for (acct_id, acct_name, ngram), metrics in ngram_data[n].items():
            if metrics['impressions'] < args.min_impressions:
                continue
            rows_out.append([
                format_cid(acct_id),
                ngram,
                acct_name,
                brand_lookup.get(re.sub(r'\D', '', acct_id), ''),
                metrics['clicks'],
                metrics['impressions'],
                round(metrics['cost'], 2),
                round(metrics['conversions'], 2),
                '',  # Include?
                metrics['count']
            ])
        rows_out.sort(key=lambda r: (r[2], -r[5]))  # account name, then impressions desc
        return rows_out

    rows_2 = build_output_rows(2)
    rows_3 = build_output_rows(3)
    print(f"  2-NGram: {len(rows_2)} rows ({args.min_impressions}+ impressions)")
    print(f"  3-NGram: {len(rows_3)} rows ({args.min_impressions}+ impressions)")

    print("\nWriting to sheet...")
    write_tab(service, args.sheet_id, "2-NGram", HEADER, rows_2)
    write_tab(service, args.sheet_id, "3-NGram", HEADER, rows_3)

    accts_2 = len(set(r[0] for r in rows_2))
    accts_3 = len(set(r[0] for r in rows_3))
    print(f"\n{'='*60}")
    print("DONE")
    print(f"{'='*60}")
    print(f"  2-NGram: {len(rows_2)} ngrams across {accts_2} accounts")
    print(f"  3-NGram: {len(rows_3)} ngrams across {accts_3} accounts")
    print(f"  Filter: {args.min_impressions}+ impressions")
    print(f"\n  Sheet: https://docs.google.com/spreadsheets/d/{args.sheet_id}")


if __name__ == '__main__':
    main()
