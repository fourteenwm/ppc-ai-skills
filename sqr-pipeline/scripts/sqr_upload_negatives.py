#!/usr/bin/env python3
"""Upload approved negative keywords to Google Ads shared negative keyword lists.

Reads pending rows from a Google Sheet "Uploader" tab, groups by account,
adds each query as a PHRASE match negative to the specified shared set,
and stamps "X" in the Uploaded column for successful uploads.

Two-step mutation safety (see mutation-safety skill for the pattern):
  Step 1 — Dry-run preview generates a deterministic APPROVAL CODE from the
           hash of the pending work. No mutations happen.
  Step 2 — User re-runs the script with that approval code. The code is
           re-computed from current sheet state. If the sheet changed since
           the dry-run, the code will not match and execution is refused.

Never skip the dry-run. Never auto-approve.

Usage:
    # Step 1 — Dry-run preview (prints approval code)
    python sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID

    # Step 2 — Execute with approval code
    python sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID APPROVE-XXXXXXXX

    # Custom tab name (default: "Uploader")
    python sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID --tab-name "My Uploader"

    # Explicit credential paths
    python sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID \
        --config google-ads.yaml --sheets-token token.json

Prerequisites:
    - google-ads.yaml at project root (Google Ads API credentials)
    - token.json at project root OR a refresh token in google-ads.yaml
      with the spreadsheets scope. The script tries token.json first,
      then falls back to google-ads.yaml for OAuth.
    - pip install google-ads google-auth google-api-python-client pyyaml

Uploader tab column schema (required):
    A: CID               (full format, e.g. 123-456-7890 — informational only)
    B: Query             (search term to add as negative — required)
    C: Neg List ID       (shared negative keyword list ID — required)
    D: Trunc CID         (numeric customer ID, e.g. 1234567890 — required)
    E: Uploaded?         (empty = pending, "X" = done — script writes here)

Row 1 is treated as a header and skipped.
"""

import argparse
import hashlib
import io
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import yaml

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BATCH_SIZE = 1000
GOOGLE_ADS_KEYWORD_MAX_LENGTH = 80


# ---------------------------------------------------------------------------
# Sheets authentication
# ---------------------------------------------------------------------------

def get_sheets_service(sheets_token_path: str, ads_config_path: str):
    """Build authenticated Google Sheets API service.

    Prefers a dedicated token.json (OAuth with spreadsheets scope).
    Falls back to the refresh token in google-ads.yaml if present with
    the spreadsheets scope.
    """
    if os.path.exists(sheets_token_path):
        with open(sheets_token_path, 'r', encoding='utf-8') as f:
            token_data = json.load(f)

        credentials = Credentials(
            token=token_data.get('token') or token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=token_data.get('client_id'),
            client_secret=token_data.get('client_secret'),
            scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/spreadsheets']),
        )
    elif os.path.exists(ads_config_path):
        with open(ads_config_path, 'r', encoding='utf-8') as f:
            ads_config = yaml.safe_load(f)

        credentials = Credentials(
            token=None,
            refresh_token=ads_config.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=ads_config.get('client_id'),
            client_secret=ads_config.get('client_secret'),
            scopes=['https://www.googleapis.com/auth/spreadsheets'],
        )
    else:
        print(f"ERROR: Cannot authenticate to Sheets.")
        print(f"  Neither {sheets_token_path} nor {ads_config_path} exists.")
        print(f"  See google-ads-api-setup skill for credential setup.")
        sys.exit(1)

    return build('sheets', 'v4', credentials=credentials)


# ---------------------------------------------------------------------------
# Reading pending rows
# ---------------------------------------------------------------------------

def read_pending_rows(sheets_service, sheet_id: str, tab_name: str):
    """Read Uploader tab and return rows where col B has value and col E is empty."""
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{tab_name}!A:E",
    ).execute()

    rows = result.get('values', [])
    if not rows:
        return []

    pending = []
    for i, row in enumerate(rows):
        if i == 0:  # Skip header row
            continue

        while len(row) < 5:
            row.append('')

        cid = row[0].strip()
        query = row[1].strip()
        shared_set_id = row[2].strip()
        trunc_cid = row[3].strip()
        uploaded = row[4].strip()

        if query and not uploaded:
            if not trunc_cid:
                print(f"  WARNING: Row {i + 1} has query '{query}' but no Trunc CID - skipping")
                continue
            if not shared_set_id:
                print(f"  WARNING: Row {i + 1} has query '{query}' but no Neg List ID - skipping")
                continue

            pending.append({
                'row_num': i + 1,
                'cid': cid,
                'query': query,
                'shared_set_id': shared_set_id,
                'trunc_cid': trunc_cid,
            })

    return pending


def group_by_account(pending_rows):
    """Group pending rows by trunc_cid."""
    groups = defaultdict(list)
    for row in pending_rows:
        groups[row['trunc_cid']].append(row)
    return dict(groups)


# ---------------------------------------------------------------------------
# Mutation safety — deterministic approval code
# ---------------------------------------------------------------------------

def compute_approval_code(pending_rows) -> str:
    """Compute a deterministic APPROVAL CODE from the hash of pending work.

    Same pending data -> same code. If the sheet changes between dry-run
    and execute, the code changes, so stale approvals fail safely.
    """
    key = '\n'.join(sorted(
        f"{r['trunc_cid']}|{r['shared_set_id']}|{r['query']}"
        for r in pending_rows
    ))
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()[:8].upper()
    return f"APPROVE-{digest}"


def print_preview(pending, account_groups, expected_code):
    """Print human-readable dry-run preview with approval code."""
    print("-" * 80)
    print("DRY-RUN PREVIEW: Keywords to upload")
    print("-" * 80)

    for trunc_cid, rows in sorted(account_groups.items()):
        by_set = defaultdict(list)
        for r in rows:
            by_set[r['shared_set_id']].append(r['query'])

        print(f"\n  Account CID: {trunc_cid}")
        for set_id, queries in by_set.items():
            print(f"    Shared Set {set_id}: {len(queries)} keyword(s)")
            for q in queries[:5]:
                print(f"      - \"{q}\"")
            if len(queries) > 5:
                print(f"      ... and {len(queries) - 5} more")

    print()
    print(f"TOTAL: {len(pending)} keywords across {len(account_groups)} account(s)")
    print()
    print("=" * 80)
    print(f"APPROVAL CODE: {expected_code}")
    print("=" * 80)
    print()
    print("To execute these mutations, re-run with the code above:")
    print(f"  python scripts/sqr_upload_negatives.py --sheet-id ... {expected_code}")
    print()
    print("The code is a hash of the current pending work. If the sheet changes")
    print("before you execute, the code will no longer match and execution will")
    print("be refused — you'll need a fresh dry-run preview.")


# ---------------------------------------------------------------------------
# Upload execution
# ---------------------------------------------------------------------------

def upload_negatives_for_account(ads_client, customer_id: str, rows):
    """Upload phrase match negatives to shared sets for one account."""
    shared_criterion_service = ads_client.get_service("SharedCriterionService")

    by_shared_set = defaultdict(list)
    for row in rows:
        by_shared_set[row['shared_set_id']].append(row)

    succeeded = []
    failed = []

    for shared_set_id, set_rows in by_shared_set.items():
        for batch_start in range(0, len(set_rows), BATCH_SIZE):
            batch = set_rows[batch_start:batch_start + BATCH_SIZE]
            operations = []

            for row in batch:
                if len(row['query']) > GOOGLE_ADS_KEYWORD_MAX_LENGTH:
                    failed.append((row['row_num'],
                                   f"Skipped: keyword is {len(row['query'])} chars (max {GOOGLE_ADS_KEYWORD_MAX_LENGTH})"))
                    continue
                operation = ads_client.get_type("SharedCriterionOperation")
                criterion = operation.create
                criterion.shared_set = f"customers/{customer_id}/sharedSets/{shared_set_id}"
                criterion.keyword.text = row['query']
                criterion.keyword.match_type = ads_client.enums.KeywordMatchTypeEnum.PHRASE
                operations.append(operation)

            if not operations:
                continue

            try:
                shared_criterion_service.mutate_shared_criteria(
                    customer_id=customer_id,
                    operations=operations,
                )
                for row in batch:
                    if len(row['query']) <= GOOGLE_ADS_KEYWORD_MAX_LENGTH:
                        succeeded.append(row['row_num'])
            except GoogleAdsException as ex:
                error_msg = str(ex.failure.errors[0].message) if ex.failure.errors else str(ex)
                for row in batch:
                    if len(row['query']) <= GOOGLE_ADS_KEYWORD_MAX_LENGTH:
                        failed.append((row['row_num'], error_msg))
            except Exception as ex:
                for row in batch:
                    if len(row['query']) <= GOOGLE_ADS_KEYWORD_MAX_LENGTH:
                        failed.append((row['row_num'], str(ex)))

    return {'succeeded': succeeded, 'failed': failed}


def mark_rows_uploaded(sheets_service, sheet_id: str, tab_name: str, row_nums):
    """Stamp "X" in col E for successfully uploaded rows."""
    if not row_nums:
        return

    data = [
        {'range': f"{tab_name}!E{row_num}", 'values': [["X"]]}
        for row_num in row_nums
    ]

    sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={'valueInputOption': 'USER_ENTERED', 'data': data},
    ).execute()


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def run_upload(
    sheet_id: str,
    tab_name: str,
    config_path: str,
    sheets_token_path: str,
    approval_code: str = None,
):
    """Main upload workflow. If approval_code is None, dry-run only."""
    print("=" * 80)
    print("SQR NEGATIVE KEYWORD UPLOADER")
    print(f"Sheet: {sheet_id}")
    print(f"Tab: {tab_name}")
    print("=" * 80)
    print()

    print(f"Reading {tab_name} tab from sheet...")
    sheets_service = get_sheets_service(sheets_token_path, config_path)
    pending = read_pending_rows(sheets_service, sheet_id, tab_name)

    if not pending:
        print("\nNo pending rows found (all rows either have no query or are already uploaded).")
        return

    print(f"Found {len(pending)} pending keyword(s) to upload.\n")

    account_groups = group_by_account(pending)
    expected_code = compute_approval_code(pending)

    if approval_code is None:
        # Dry-run mode
        print_preview(pending, account_groups, expected_code)
        return

    # Execute mode — validate approval code
    if approval_code != expected_code:
        print("=" * 80)
        print("ERROR: Approval code mismatch.")
        print("=" * 80)
        print(f"  Provided: {approval_code}")
        print(f"  Expected: {expected_code}")
        print()
        print("The approval code is derived from the hash of the pending work.")
        print("If the sheet changed since your dry-run, the code changes.")
        print()
        print("Re-run without an approval code to see the current pending work")
        print("and get a fresh approval code.")
        sys.exit(1)

    # Code matches — execute
    if not os.path.exists(config_path):
        print(f"ERROR: Google Ads credentials not found at {config_path}")
        print("See google-ads-api-setup skill for setup.")
        sys.exit(1)

    ads_client = GoogleAdsClient.load_from_storage(config_path)

    total_succeeded = []
    total_failed = []

    for trunc_cid, rows in account_groups.items():
        print(f"  Uploading {len(rows)} keyword(s) to account {trunc_cid}...")
        result = upload_negatives_for_account(ads_client, trunc_cid, rows)
        total_succeeded.extend(result['succeeded'])
        total_failed.extend(result['failed'])

        if result['succeeded']:
            print(f"    Uploaded: {len(result['succeeded'])}")
        if result['failed']:
            print(f"    Failed: {len(result['failed'])}")
            for row_num, error in result['failed'][:3]:
                print(f"      Row {row_num}: {error}")

    if total_succeeded:
        print(f"\nMarking {len(total_succeeded)} row(s) as uploaded in sheet...")
        mark_rows_uploaded(sheets_service, sheet_id, tab_name, total_succeeded)

    print()
    print("=" * 80)
    print(f"RESULTS: {len(total_succeeded)} uploaded, {len(total_failed)} failed")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Upload phrase match negatives to shared negative keyword lists.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Step 1 — Dry-run:  python sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID\n"
               "Step 2 — Execute:  python sqr_upload_negatives.py --sheet-id YOUR_SHEET_ID APPROVE-XXXXXXXX",
    )
    parser.add_argument('--sheet-id', required=True,
                        help='Google Sheet ID containing the Uploader tab')
    parser.add_argument('--tab-name', default='Uploader',
                        help='Tab name (default: "Uploader")')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Google Ads credentials YAML (default: ./google-ads.yaml)')
    parser.add_argument('--sheets-token', default='token.json',
                        help='Google Sheets OAuth token JSON (default: ./token.json). '
                             'If not found, falls back to credentials in --config.')
    parser.add_argument('approval_code', nargs='?', default=None,
                        help='APPROVE-XXXXXXXX code from dry-run (omit for dry-run preview)')

    args = parser.parse_args()

    run_upload(
        sheet_id=args.sheet_id,
        tab_name=args.tab_name,
        config_path=args.config,
        sheets_token_path=args.sheets_token,
        approval_code=args.approval_code,
    )


if __name__ == "__main__":
    main()
