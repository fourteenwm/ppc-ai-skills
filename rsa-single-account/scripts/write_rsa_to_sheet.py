#!/usr/bin/env python3
"""
Write RSA Data to Google Sheet (Step 8 of the rsa-single-account skill)

Writes generated RSA headlines and descriptions to a Google Sheet for
review and import into Google Ads Editor. Clears the sheet, writes a
header row, then one row per ad group:
Account | Campaign | Ad Group | Headline 1-15 | Description 1-4

Auth (first match wins):
    1. --sheets-token token-sheets.json — a dedicated OAuth token with the
       spreadsheets scope
    2. --config google-ads.yaml — reuses its OAuth client + refresh token
       (the token must have been granted the spreadsheets scope)

Usage:
    python write_rsa_to_sheet.py --sheet-id <YOUR_RSA_SHEET_ID> rsa_data.json
    python write_rsa_to_sheet.py --sheet-id "https://docs.google.com/spreadsheets/d/<ID>/edit" rsa_data.json

rsa_data.json format (one entry per ad group):
    [
      {
        "account_name": "Example Auto",
        "campaign_name": "Example Auto - Search",
        "ad_group_name": "Brake Repair",
        "headlines": ["...", "..."],       # up to 15
        "descriptions": ["...", "..."]     # up to 4
      }
    ]

Prerequisites:
    - google-ads.yaml at project root (see the google-ads-api-setup skill)
      OR a token-sheets.json with the spreadsheets scope
    - pip install google-api-python-client google-auth google-auth-oauthlib pyyaml
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

import yaml
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Windows console encoding fix
if sys.platform == 'win32' and sys.stdout is not None:
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def extract_sheet_id(sheet_ref):
    """Accept a bare sheet ID or a full Google Sheets URL."""
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_ref)
    if match:
        return match.group(1)
    if re.fullmatch(r'[a-zA-Z0-9-_]+', sheet_ref):
        return sheet_ref
    raise ValueError(f"Could not extract sheet ID from: {sheet_ref}")


def get_sheets_credentials(sheets_token_path, config_path):
    """Google Sheets OAuth credentials.

    Prefers a dedicated token file (spreadsheets scope); falls back to
    reusing the OAuth client + refresh token in google-ads.yaml.
    """
    token_file = Path(sheets_token_path)
    if token_file.exists():
        try:
            return Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception as e:
            print(f"Warning: could not load {sheets_token_path} ({e}); "
                  f"falling back to {config_path}")

    config_file = Path(config_path)
    if not config_file.exists():
        print(f"Error: neither {sheets_token_path} nor {config_path} found.")
        print("See the google-ads-api-setup skill for creating google-ads.yaml, "
              "or provide --sheets-token pointing at an OAuth token with the "
              "spreadsheets scope.")
        return None

    with open(config_file, 'r', encoding='utf-8') as f:
        ads_config = yaml.safe_load(f) or {}

    refresh_token = ads_config.get('refresh_token')
    client_id = ads_config.get('client_id')
    client_secret = ads_config.get('client_secret')
    if not (refresh_token and client_id and client_secret):
        print(f"Error: {config_path} is missing client_id/client_secret/refresh_token.")
        return None

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


def write_rsa_to_sheet(sheet_ref, rsa_data, sheets_token_path='token-sheets.json',
                       config_path='google-ads.yaml'):
    """
    Write RSA data to Google Sheet (clear then write).

    Args:
        sheet_ref (str): Google Sheet ID or URL
        rsa_data (list): List of dicts with RSA data per ad group
        sheets_token_path (str): Path to a dedicated Sheets OAuth token
        config_path (str): Path to google-ads.yaml (auth fallback)

    Returns:
        str: Sheet URL, or None on failure
    """
    sheet_id = extract_sheet_id(sheet_ref)

    creds = get_sheets_credentials(sheets_token_path, config_path)
    if not creds:
        return None

    service = build('sheets', 'v4', credentials=creds)

    try:
        # Clear existing data
        print(f"Clearing existing data in sheet...")
        service.spreadsheets().values().clear(
            spreadsheetId=sheet_id,
            range='A:Z'
        ).execute()

        # Prepare header row
        header = ['Account', 'Campaign', 'Ad Group']
        header += [f'Headline {i}' for i in range(1, 16)]  # H1-H15
        header += [f'Description {i}' for i in range(1, 5)]  # D1-D4

        # Prepare data rows
        rows = [header]
        for rsa in rsa_data:
            row = [
                rsa['account_name'],
                rsa['campaign_name'],
                rsa['ad_group_name']
            ]
            # Add 15 headlines
            row += rsa['headlines']
            # Pad if fewer than 15 headlines
            while len(row) < 18:  # 3 metadata + 15 headlines
                row.append('')
            # Add 4 descriptions
            row += rsa['descriptions']
            # Pad if fewer than 4 descriptions
            while len(row) < 22:  # 3 metadata + 15 headlines + 4 descriptions
                row.append('')

            rows.append(row)

        # Write data
        print(f"Writing {len(rsa_data)} RSA ad groups to sheet...")
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='A1',
            valueInputOption='RAW',
            body={'values': rows}
        ).execute()

        print(f"[SUCCESS] Successfully wrote to Google Sheet")
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"

    except HttpError as e:
        print(f"Google Sheets API error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Write RSA data to a Google Sheet for Google Ads Editor import'
    )
    parser.add_argument('json_file', help='Path to the RSA data JSON (schema in script header)')
    parser.add_argument('--sheet-id', required=True,
                        help='Output Google Sheet ID or full URL (the sheet is cleared '
                             'and rewritten each run)')
    parser.add_argument('--sheets-token', default='token-sheets.json',
                        help='Path to a Sheets OAuth token (default: ./token-sheets.json; '
                             'falls back to --config)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml for OAuth reuse '
                             '(default: ./google-ads.yaml)')
    args = parser.parse_args()

    # Load RSA data from JSON
    try:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            rsa_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found: {args.json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.json_file}: {e}")
        sys.exit(1)

    # Validate RSA data structure
    required_keys = ['account_name', 'campaign_name', 'ad_group_name', 'headlines', 'descriptions']
    for i, rsa in enumerate(rsa_data):
        for key in required_keys:
            if key not in rsa:
                print(f"Error: RSA data at index {i} missing required key: {key}")
                sys.exit(1)

    # Write to sheet
    result = write_rsa_to_sheet(args.sheet_id, rsa_data,
                                sheets_token_path=args.sheets_token,
                                config_path=args.config)

    if result:
        print(f"\n[SHEET] Google Sheet URL: {result}")
        print(f"Ready for review and import into Google Ads Editor")
    else:
        print("\n[ERROR] Failed to write to Google Sheet")
        sys.exit(1)


if __name__ == "__main__":
    main()
