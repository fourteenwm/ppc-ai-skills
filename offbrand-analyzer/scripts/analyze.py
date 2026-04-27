#!/usr/bin/env python3
"""
Off-Brand Analyzer

Analyzes search queries for categorization using OpenAI GPT-4o.
Categories: high intent, low intent, informational, off-brand

Reads from "Have Cost" tab and writes results to "Have Cost Result".

Usage:
    python analyze.py                    # Single batch (50 rows)
    python analyze.py --batch-size 100   # Custom batch size
    python analyze.py --dry-run          # No writes to sheet
    python analyze.py --run-all          # Run until all pending queries processed
    python analyze.py --run-all --chain-geo  # Run all, then trigger GEO analyzer
    python analyze.py --with-qa          # Full pipeline + QA score (no auto-retry)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from openai import OpenAI

# Configuration
# Set to your Google Sheet ID for the SQR pipeline.
SPREADSHEET_ID = "YOUR_SHEET_ID"
INPUT_TAB = "Have Cost"
OUTPUT_TAB = "Have Cost Result"
DEFAULT_BATCH_SIZE = 50
MODEL = "gpt-4o"

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent

# Credential paths (standard project-root locations — override via env vars if needed)
SHEETS_TOKEN_PATH = Path(os.getenv("SHEETS_TOKEN_PATH", "./token.json"))
PROMPT_PATH = SKILL_DIR / "prompt.md"
OFFBRAND_KEYWORDS_PATH = SKILL_DIR / "offbrand-keywords.txt"


def load_openai_client() -> OpenAI:
    """Load OpenAI client from environment or .env file."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not set. Add it to a .env file or export it as an environment variable."
        )
    return OpenAI(api_key=api_key)


def load_sheets_service():
    """Load Google Sheets API service."""
    if not SHEETS_TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"Sheets token not found at {SHEETS_TOKEN_PATH.absolute()}\n"
            "Set up OAuth credentials first — see the google-ads-api-setup skill "
            "for the walkthrough (the same token.json can be reused with the Sheets scope)."
        )

    creds = Credentials.from_authorized_user_file(
        str(SHEETS_TOKEN_PATH),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(SHEETS_TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


def load_prompt() -> str:
    """Load the GPT prompt from prompt.md."""
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file not found at {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding='utf-8')


def load_offbrand_keywords() -> list[str]:
    """Load off-brand keywords from file."""
    if not OFFBRAND_KEYWORDS_PATH.exists():
        raise FileNotFoundError(f"Off-brand keywords not found at {OFFBRAND_KEYWORDS_PATH}")

    content = OFFBRAND_KEYWORDS_PATH.read_text(encoding='utf-8')
    keywords = [line.strip() for line in content.splitlines() if line.strip()]
    return keywords


def read_pending_queries(service, limit: int) -> list[dict[str, Any]]:
    """
    Read queries from 'Have Cost' where Column I = 'Waiting'.

    Returns list of dicts: [{CID, Account, Query, Brand_Names, row_number}, ...]
    """
    # Read all data from the tab
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{INPUT_TAB}'!A:I"
    ).execute()

    values = result.get('values', [])
    if not values:
        return []

    # First row is headers
    rows = values[1:]

    # Column indices:
    # A=0: CID
    # B=1: Account
    # C=2: Query
    # H=7: Brand Names
    # I=8: Completed?
    pending_queries = []

    for i, row in enumerate(rows):
        # Ensure row has enough columns
        if len(row) < 9:
            row.extend([''] * (9 - len(row)))

        cid = row[0] if len(row) > 0 else ''
        account = row[1] if len(row) > 1 else ''
        query = row[2] if len(row) > 2 else ''
        brand_names = row[7] if len(row) > 7 else ''  # Column H (0-indexed = 7)
        status = row[8] if len(row) > 8 else ''       # Column I (0-indexed = 8)

        # Filter for "Waiting" status and non-empty required fields
        if status.strip().lower() == 'waiting' and cid and query:
            pending_queries.append({
                'CID': cid,
                'Account': account,
                'Query': query,
                'Brand_Names': brand_names,
                'row_number': i + 2  # +2 for header row and 1-indexing
            })

        if len(pending_queries) >= limit:
            break

    return pending_queries


def build_payload(queries: list[dict], offbrand_keywords: list[str]) -> dict:
    """Build the JSON payload for OpenAI API."""
    # Group brand names by CID
    brand_names = {}
    query_list = []

    for q in queries:
        cid = q['CID']
        brands = q['Brand_Names']

        if cid not in brand_names and brands:
            brand_names[cid] = brands

        query_list.append({
            'CID': cid,
            'Query': q['Query']
        })

    return {
        'queries': query_list,
        'brand_names': brand_names,
        'off_brand_keywords': offbrand_keywords
    }


def call_openai(client: OpenAI, prompt: str, payload: dict) -> str:
    """Call OpenAI API with the prompt and payload."""
    user_message = f"Here is the JSON to evaluate:\n\n{json.dumps(payload, indent=2)}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.1,  # Low temperature for consistent rule-following
        max_tokens=4000
    )

    return response.choices[0].message.content


def parse_response(response_text: str) -> list[list[str]]:
    """Parse the CSV-formatted response into rows."""
    results = []

    # Pattern: ["CID","Query","Category"]
    pattern = r'\["([^"]+)","([^"]+)","([^"]+)"\]'
    matches = re.findall(pattern, response_text)

    for match in matches:
        cid, query, category = match
        # Normalize category to lowercase
        category = category.lower().strip()
        results.append([cid, query, category])

    return results


def write_results(service, results: list[list[str]], dry_run: bool = False):
    """Append results to 'Have Cost Result' tab."""
    if not results:
        print("No results to write.")
        return

    if dry_run:
        print(f"\n[DRY RUN] Would write {len(results)} rows to '{OUTPUT_TAB}':")
        for row in results[:10]:
            print(f"  {row}")
        if len(results) > 10:
            print(f"  ... and {len(results) - 10} more rows")
        return

    # Append to sheet (A:C for 3 columns)
    body = {'values': results}

    result = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{OUTPUT_TAB}'!A:C",
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

    updates = result.get('updates', {})
    print(f"Wrote {updates.get('updatedRows', 0)} rows to '{OUTPUT_TAB}'")


def run_single_batch(openai_client, sheets_service, prompt, offbrand_keywords, batch_size, dry_run):
    """
    Run a single batch of off-brand analysis.

    Returns: (queries_processed, category_counts) or (0, {}) if no pending queries
    """
    # Read pending queries
    queries = read_pending_queries(sheets_service, batch_size)

    if not queries:
        return 0, {}

    print(f"  Found {len(queries)} pending queries")

    # Build payload
    payload = build_payload(queries, offbrand_keywords)
    unique_cids = len(payload['brand_names'])
    print(f"  Across {unique_cids} unique accounts with brand names")

    # Call OpenAI
    print(f"\nCalling OpenAI ({MODEL})...")
    response_text = call_openai(openai_client, prompt, payload)

    # Parse response
    results = parse_response(response_text)
    print(f"  Parsed {len(results)} results")

    # Count categories
    categories = {}
    for r in results:
        cat = r[2]
        categories[cat] = categories.get(cat, 0) + 1

    print("\n  Category breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")

    # Write results
    print(f"\nWriting to '{OUTPUT_TAB}'...")
    write_results(sheets_service, results, dry_run)

    return len(queries), categories


def run_geo_analyzer():
    """Run the GEO Conflict Analyzer until complete."""
    geo_script = PROJECT_ROOT / ".claude" / "skills" / "geo-conflict-analyzer" / "scripts" / "analyze.py"

    if not geo_script.exists():
        print(f"\nERROR: GEO Conflict Analyzer not found at {geo_script}")
        return False

    print("\n" + "=" * 60)
    print("STAGE 2: GEO Conflict Analyzer")
    print("=" * 60)

    batch_num = 0
    total_processed = 0

    while True:
        batch_num += 1
        print(f"\n--- GEO Batch {batch_num} ---")

        result = subprocess.run(
            [sys.executable, str(geo_script), "--batch-size", "50"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Check if no pending queries found (Stage 2 complete)
        if "No pending queries" in result.stdout or "No queries found" in result.stdout:
            print("\n" + "=" * 60)
            print("STAGE 2 COMPLETE: All GEO conflicts analyzed")
            print("=" * 60)
            return True

        # Check for errors
        if result.returncode != 0:
            print(f"\nERROR: GEO Analyzer failed with return code {result.returncode}")
            return False

        # Extract rows written from output
        if "Wrote" in result.stdout:
            total_processed += 50  # Approximate

    return True


def run_with_qa_gate(openai_client, sheets_service, prompt, offbrand_keywords,
                     batch_size: int, threshold: float = 95.0, dry_run: bool = False):
    """
    Run the full pipeline with QA gate validation (single run, no retry).

    Workflow:
    1. Run Step 1 (Off-Brand Analyzer) - processes all pending queries
    2. Run Step 2 (GEO Conflict Analyzer) - processes all pending GEO queries
    3. Run Step 3 (QA Gate) - validates results and reports score

    NO clearing of tabs, NO auto-retry. Just runs once and reports the QA score.
    """
    from qa_gate import run_qa_gate

    print("\n" + "=" * 70)
    print("FULL PIPELINE WITH QA SCORE")
    print("=" * 70)
    print(f"QA Threshold: {threshold}%")
    print("Mode: Single run (no auto-retry)")

    # Step 1: Run Off-Brand Analysis
    print("\n" + "=" * 60)
    print("STAGE 1: Off-Brand Analyzer")
    print("=" * 60)

    batch_num = 0
    total_processed = 0
    total_categories = {}

    while True:
        batch_num += 1
        print(f"\n--- Batch {batch_num} ---")

        processed, categories = run_single_batch(
            openai_client, sheets_service, prompt, offbrand_keywords,
            batch_size, dry_run
        )

        if processed == 0:
            print("No pending queries found.")
            break

        total_processed += processed
        for cat, count in categories.items():
            total_categories[cat] = total_categories.get(cat, 0) + count

    print(f"\nStage 1 complete: {total_processed} queries processed")

    # Step 2: Run GEO Analysis
    if not dry_run:
        run_geo_analyzer()
    else:
        print("\n[DRY RUN] Would run GEO Conflict Analyzer")

    # Step 3: Run QA Gate (score only, no retry)
    print("\n" + "=" * 60)
    print("STAGE 3: QA Score Report")
    print("=" * 60)

    if dry_run:
        print("\n[DRY RUN] Would run QA gate validation")
        print("Exiting dry run mode.")
        return True

    qa_result = run_qa_gate(threshold=threshold, verbose=True)

    # Report results
    print("\n" + "=" * 70)
    if qa_result["passed"]:
        print("QA RESULT: PASSED")
    else:
        print("QA RESULT: BELOW THRESHOLD (review recommended)")
    print("=" * 70)
    print(f"\nOff-Brand Precision:  {qa_result.get('off_brand', {}).get('precision', 0):.1f}%")
    print(f"GEO Success Rate:     {qa_result.get('geo', {}).get('success_rate', 0):.1f}%")
    print(f"Combined Rate:        {qa_result['combined_rate']:.1f}%")
    print(f"Threshold:            {threshold}%")

    # Always return True - we completed the run, user can review the score
    return True


def main():
    parser = argparse.ArgumentParser(description='Analyze search queries for off-brand detection')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'Number of queries to process (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--dry-run', action='store_true',
                        help='Analyze without writing to sheet')
    parser.add_argument('--run-all', action='store_true',
                        help='Run batches until all pending queries are processed')
    parser.add_argument('--chain-geo', action='store_true',
                        help='After Stage 1 completes, automatically run GEO Conflict Analyzer')
    parser.add_argument('--with-qa', action='store_true',
                        help='Run full pipeline (Step 1 + Step 2) then report QA score. No auto-retry.')
    parser.add_argument('--qa-threshold', type=float, default=95.0,
                        help='QA pass threshold percentage (default: 95)')
    args = parser.parse_args()

    print("=" * 60)
    print("Off-Brand Analyzer (Stage 1)")
    print("=" * 60)

    # Load credentials and services
    print("\nLoading credentials...")
    openai_client = load_openai_client()
    sheets_service = load_sheets_service()
    prompt = load_prompt()
    offbrand_keywords = load_offbrand_keywords()
    print("  OpenAI client loaded")
    print("  Google Sheets service loaded")
    print("  Prompt loaded")
    print(f"  Off-brand keywords loaded ({len(offbrand_keywords)} terms)")

    # If --with-qa is set, run the full pipeline with QA gate
    if args.with_qa:
        success = run_with_qa_gate(
            openai_client, sheets_service, prompt, offbrand_keywords,
            batch_size=args.batch_size,
            threshold=args.qa_threshold,
            dry_run=args.dry_run
        )
        sys.exit(0 if success else 1)

    if args.run_all:
        # Run batches until no pending queries remain
        batch_num = 0
        total_processed = 0
        total_categories = {}

        while True:
            batch_num += 1
            print(f"\n--- Batch {batch_num} ---")
            print(f"Reading up to {args.batch_size} pending queries from '{INPUT_TAB}'...")

            processed, categories = run_single_batch(
                openai_client, sheets_service, prompt, offbrand_keywords,
                args.batch_size, args.dry_run
            )

            if processed == 0:
                print("No pending queries found (Column I = 'Waiting').")
                break

            total_processed += processed
            for cat, count in categories.items():
                total_categories[cat] = total_categories.get(cat, 0) + count

            print(f"\n  Running total: {total_processed} queries processed")

        # Summary
        print("\n" + "=" * 60)
        print("STAGE 1 COMPLETE")
        print("=" * 60)
        print(f"\nTotal queries processed: {total_processed}")
        print(f"Total batches: {batch_num - 1}")
        if total_categories:
            print("\nOverall category breakdown:")
            for cat, count in sorted(total_categories.items()):
                pct = (count / total_processed * 100) if total_processed > 0 else 0
                print(f"  {cat}: {count} ({pct:.1f}%)")

        # Chain to GEO analyzer if requested
        if args.chain_geo:
            run_geo_analyzer()

    else:
        # Single batch mode
        print(f"\nReading up to {args.batch_size} pending queries from '{INPUT_TAB}'...")

        processed, categories = run_single_batch(
            openai_client, sheets_service, prompt, offbrand_keywords,
            args.batch_size, args.dry_run
        )

        if processed == 0:
            print("No pending queries found (Column I = 'Waiting').")

            # If chain-geo is set and Stage 1 is already complete, run Stage 2
            if args.chain_geo:
                run_geo_analyzer()
            return

        print("\n" + "=" * 60)
        print("Done!")
        print("=" * 60)


if __name__ == '__main__':
    main()
