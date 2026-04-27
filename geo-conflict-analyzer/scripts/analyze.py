#!/usr/bin/env python3
"""
GEO Conflict Analyzer

Analyzes search queries for geo targeting conflicts using OpenAI GPT-4o.
Reads queries from a Google Sheet where a status column = "Waiting", sends
them to OpenAI in batches, and writes PASS/FAIL/Confidence results back.

Usage:
    python analyze.py --sheet-id YOUR_SHEET_ID
    python analyze.py --sheet-id YOUR_SHEET_ID --batch-size 100
    python analyze.py --sheet-id YOUR_SHEET_ID --dry-run

Environment variables:
    OPENAI_API_KEY   - required
    GEO_SHEET_ID     - optional (alternative to --sheet-id)

See SKILL.md for full documentation.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from openai import OpenAI

# Defaults (override via CLI args)
DEFAULT_INPUT_TAB = "Have Cost - GEO"
DEFAULT_OUTPUT_TAB = "Have Cost Result - GEO"
DEFAULT_BATCH_SIZE = 50
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TOKEN_PATH = "./token.json"

SCRIPT_DIR = Path(__file__).parent
PROMPT_PATH = SCRIPT_DIR.parent / "prompt.md"


def load_openai_client() -> OpenAI:
    """Load OpenAI client from environment or .env file."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Add it to a .env file or export it as an environment variable."
        )
    return OpenAI(api_key=api_key)


def load_sheets_service(token_path: str):
    """Load Google Sheets API service from an OAuth token file."""
    token_file = Path(token_path)
    if not token_file.exists():
        raise FileNotFoundError(
            f"Sheets token not found at {token_file.absolute()}\n"
            "Set up OAuth credentials first — see the google-ads-api-setup skill "
            "for the walkthrough (the same token.json can be reused with the Sheets scope)."
        )

    creds = Credentials.from_authorized_user_file(
        str(token_file),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_file, 'w') as f:
            f.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


def load_prompt() -> str:
    """Load the GPT prompt from prompt.md."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found at {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding='utf-8')


def read_pending_queries(service, sheet_id: str, input_tab: str, limit: int) -> list[dict[str, Any]]:
    """Read queries from input tab where Column I = 'Waiting'."""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{input_tab}'!A:I"
    ).execute()

    values = result.get('values', [])
    if not values:
        return []

    rows = values[1:]  # Skip header
    pending_queries = []

    for i, row in enumerate(rows):
        if len(row) < 9:
            row.extend([''] * (9 - len(row)))

        cid = row[0] if len(row) > 0 else ''
        account = row[1] if len(row) > 1 else ''
        query = row[2] if len(row) > 2 else ''
        geo_names = row[7] if len(row) > 7 else ''
        status = row[8] if len(row) > 8 else ''

        if status.strip().lower() == 'waiting' and cid and query and geo_names:
            pending_queries.append({
                'CID': cid,
                'Account': account,
                'Query': query,
                'GEO_Names': geo_names,
                'row_number': i + 2
            })

        if len(pending_queries) >= limit:
            break

    return pending_queries


def build_payload(queries: list[dict]) -> dict:
    """Build the JSON payload for OpenAI API."""
    geo_targets = {}
    query_list = []

    for q in queries:
        cid = q['CID']
        geo_names = q['GEO_Names']

        if cid not in geo_targets:
            geos = re.split(r'[,;|]', geo_names)
            geo_targets[cid] = [g.strip() for g in geos if g.strip()]

        query_list.append({'CID': cid, 'Query': q['Query']})

    return {'queries': query_list, 'geo_targets': geo_targets}


def call_openai(client: OpenAI, model: str, prompt: str, payload: dict) -> str:
    """Call OpenAI API with the prompt and payload."""
    user_message = f"Here is the JSON to evaluate:\n\n{json.dumps(payload, indent=2)}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,
        max_tokens=4000
    )
    return response.choices[0].message.content


def parse_response(response_text: str) -> list[list[str]]:
    """Parse the CSV-formatted response into rows."""
    results = []
    pattern_5col = r'\["([^"]+)","([^"]+)","(PASS|FAIL)","([^"]*)","(HIGH|MEDIUM|LOW)"\]'
    matches = re.findall(pattern_5col, response_text)

    if matches:
        for match in matches:
            cid, query, geo_check, conflicting_geo, confidence = match
            results.append([cid, query, geo_check, conflicting_geo, confidence])
    else:
        pattern_4col = r'\["([^"]+)","([^"]+)","(PASS|FAIL)","([^"]*)"\]'
        matches = re.findall(pattern_4col, response_text)
        for match in matches:
            cid, query, geo_check, conflicting_geo = match
            results.append([cid, query, geo_check, conflicting_geo, "N/A"])

    return results


def get_next_empty_row(service, sheet_id: str, output_tab: str) -> int:
    """Get the next empty row in the output tab (1-indexed)."""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{output_tab}'!A:A"
    ).execute()
    values = result.get('values', [])
    return len(values) + 1


def write_results(service, sheet_id: str, output_tab: str, results: list[list[str]], dry_run: bool = False):
    """Write results to the output tab."""
    if not results:
        print("No results to write.")
        return

    if dry_run:
        print(f"\n[DRY RUN] Would write {len(results)} rows to '{output_tab}':")
        for row in results[:5]:
            print(f"  {row}")
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more rows")
        return

    next_row = get_next_empty_row(service, sheet_id, output_tab)
    end_row = next_row + len(results) - 1
    write_range = f"'{output_tab}'!A{next_row}:E{end_row}"

    result = service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=write_range,
        valueInputOption='RAW',
        body={'values': results}
    ).execute()

    print(f"Wrote {result.get('updatedRows', len(results))} rows to '{output_tab}' (rows {next_row}-{end_row})")


def main():
    parser = argparse.ArgumentParser(description='Analyze geo conflicts in search queries')
    parser.add_argument('--sheet-id', default=os.getenv('GEO_SHEET_ID'),
                        help='Google Sheets spreadsheet ID (or set GEO_SHEET_ID env var)')
    parser.add_argument('--input-tab', default=DEFAULT_INPUT_TAB,
                        help=f'Input tab name (default: "{DEFAULT_INPUT_TAB}")')
    parser.add_argument('--output-tab', default=DEFAULT_OUTPUT_TAB,
                        help=f'Output tab name (default: "{DEFAULT_OUTPUT_TAB}")')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'Queries per batch (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--model', default=DEFAULT_MODEL,
                        help=f'OpenAI model (default: {DEFAULT_MODEL})')
    parser.add_argument('--token', default=DEFAULT_TOKEN_PATH,
                        help=f'Path to Google Sheets OAuth token (default: {DEFAULT_TOKEN_PATH})')
    parser.add_argument('--dry-run', action='store_true', help='Analyze without writing to sheet')
    args = parser.parse_args()

    if not args.sheet_id:
        print("ERROR: --sheet-id is required (or set GEO_SHEET_ID env var)", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("GEO Conflict Analyzer")
    print("=" * 60)

    print("\nLoading credentials...")
    openai_client = load_openai_client()
    sheets_service = load_sheets_service(args.token)
    prompt = load_prompt()
    print("  OpenAI client loaded")
    print("  Google Sheets service loaded")
    print("  Prompt loaded")

    print(f"\nReading up to {args.batch_size} pending queries from '{args.input_tab}'...")
    queries = read_pending_queries(sheets_service, args.sheet_id, args.input_tab, args.batch_size)

    if not queries:
        print("No pending queries found (Column I = 'Waiting').")
        return

    print(f"  Found {len(queries)} pending queries")

    payload = build_payload(queries)
    print(f"  Across {len(payload['geo_targets'])} unique accounts")

    print(f"\nCalling OpenAI ({args.model})...")
    response_text = call_openai(openai_client, args.model, prompt, payload)

    results = parse_response(response_text)
    pass_count = sum(1 for r in results if r[2] == 'PASS')
    fail_count = sum(1 for r in results if r[2] == 'FAIL')
    high_count = sum(1 for r in results if len(r) > 4 and r[4] == 'HIGH')
    medium_count = sum(1 for r in results if len(r) > 4 and r[4] == 'MEDIUM')
    low_count = sum(1 for r in results if len(r) > 4 and r[4] == 'LOW')

    print(f"  Parsed {len(results)} results — PASS={pass_count}, FAIL={fail_count}")
    print(f"  Confidence: HIGH={high_count}, MEDIUM={medium_count}, LOW={low_count}")
    if low_count > 0:
        print(f"  [!] {low_count} LOW confidence results — consider manual review")

    print(f"\nWriting to '{args.output_tab}'...")
    write_results(sheets_service, args.sheet_id, args.output_tab, results, args.dry_run)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
