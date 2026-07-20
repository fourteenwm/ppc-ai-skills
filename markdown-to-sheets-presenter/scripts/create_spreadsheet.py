#!/usr/bin/env python3
"""
Create a formatted Google Spreadsheet for your reports.

Creates the spreadsheet in the Drive root of the authorized account — a
"Data" tab with a frozen, styled header row — and prints its ID and URL
as JSON for the population step that follows. Want it in a folder? Move
it in Drive afterward; the script deliberately stays inside the
Sheets-only scope.

Usage:
    python create_spreadsheet.py "Report Name"
    python create_spreadsheet.py "Report Name" --config path/to/google-ads.yaml
    python create_spreadsheet.py "Report Name" --no-format

Prerequisites:
    - google-ads.yaml at project root (or --config <path>) with the Sheets
      scope on its refresh token -- the google-ads-api-setup skill's
      generator grants it by default
    - pip install google-api-python-client google-auth pyyaml
"""

import argparse
import json
import os
import sys

try:
    import yaml
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Error: missing dependency ({e.name})", file=sys.stderr)
    print("Run: pip install google-api-python-client google-auth pyyaml", file=sys.stderr)
    sys.exit(1)


def get_sheets_service(config_path):
    """Build a Sheets API service from the OAuth credentials in google-ads.yaml.

    House pattern shared by this catalog's Sheets-writing skills (see
    non-serving-keyword-scanner and pmax-builder for the gspread variant):
    the refresh token + client id/secret come straight from google-ads.yaml,
    so one credential file serves both the Ads API and Sheets output.

    Only the spreadsheets scope is requested — creating a spreadsheet and
    formatting it via batchUpdate need nothing from the Drive API. The
    google-ads-api-setup generator grants this scope by default.
    """
    if not os.path.exists(config_path):
        print(f"ERROR: Credentials not found at {config_path}", file=sys.stderr)
        print("See the google-ads-api-setup skill for how to create google-ads.yaml", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        ads_config = yaml.safe_load(f)

    credentials = Credentials(
        token=None,
        refresh_token=ads_config.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=ads_config.get("client_id"),
        client_secret=ads_config.get("client_secret"),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )

    return build("sheets", "v4", credentials=credentials)


def create_spreadsheet(service, name):
    """Create the spreadsheet in the authorized account's Drive root."""
    body = {
        "properties": {
            "title": name
        },
        "sheets": [{
            "properties": {
                "title": "Data",
                "gridProperties": {
                    "frozenRowCount": 1
                }
            }
        }],
    }

    result = service.spreadsheets().create(
        body=body,
        fields="spreadsheetId,spreadsheetUrl,properties,sheets.properties",
    ).execute()

    sheet_id = 0
    if result.get("sheets"):
        sheet_id = result["sheets"][0]["properties"].get("sheetId", 0)

    return {
        "id": result["spreadsheetId"],
        "name": result["properties"]["title"],
        "webViewLink": result["spreadsheetUrl"],
        "sheetId": sheet_id,
    }


def apply_header_formatting(service, spreadsheet_id, sheet_id=0):
    """Apply professional blue formatting to the header row."""
    requests = [
        # Format header row - Google Blue background, white text, bold
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 26
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 0.102,
                            "green": 0.451,
                            "blue": 0.91
                        },
                        "textFormat": {
                            "foregroundColor": {
                                "red": 1,
                                "green": 1,
                                "blue": 1
                            },
                            "bold": True,
                            "fontSize": 11
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
            }
        }
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests}
    ).execute()


def main():
    parser = argparse.ArgumentParser(
        description="Create a formatted Google Spreadsheet for your reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Competitive Analysis - Example Client"
  %(prog)s "Report Name" --config credentials/google-ads.yaml

Note: The sheet is created in the Drive root of the account that authorized
      google-ads.yaml. Move it into a folder in Drive if you organize by client.
        """
    )
    parser.add_argument("name", help="Spreadsheet name")
    parser.add_argument("--config", default="google-ads.yaml",
                        help="Path to google-ads.yaml (default: ./google-ads.yaml)")
    parser.add_argument("--no-format", action="store_true", help="Skip header formatting")

    args = parser.parse_args()

    service = get_sheets_service(args.config)

    print(f"Creating spreadsheet: {args.name}", file=sys.stderr)

    try:
        result = create_spreadsheet(service, args.name)

        if not args.no_format:
            apply_header_formatting(service, result["id"], result.get("sheetId", 0))
    except HttpError as e:
        if "403" in str(e) or "PERMISSION_DENIED" in str(e):
            print("ERROR: Google Sheets refused the request (403).", file=sys.stderr)
            print(f"Most likely the refresh token in {args.config} was minted without", file=sys.stderr)
            print("the Sheets scope. Re-run the google-ads-api-setup generator once", file=sys.stderr)
            print("and paste the new refresh_token into your google-ads.yaml.", file=sys.stderr)
            sys.exit(1)
        raise

    # Output result as JSON (remove internal sheetId from output)
    output = {k: v for k, v in result.items() if k != "sheetId"}
    print(json.dumps(output, indent=2))
    print(f"\nSheet URL: {result.get('webViewLink')}", file=sys.stderr)


if __name__ == "__main__":
    main()
