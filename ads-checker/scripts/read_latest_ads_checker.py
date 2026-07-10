#!/usr/bin/env python3
"""Read latest Ads Checker audit results for daily-briefing integration.

Reads the most recent audit rows from the audit sheet's Account History tab
and formats them for briefing display. This is a CACHED read — it never calls
the Google Ads API and never re-runs the audit; it only surfaces what
ads_checker_audit.py already wrote.

CACHED-OUTPUT CONTRACT (shared with ads_checker_audit.py):
    - Tab: 'Account History'
    - Date column: 'Audit Date', format %Y-%m-%d %H:%M, filtered to the last
      N hours (default 24)
    - Columns: 'Portfolio', 'CID', 'Account Name', 'Overall Severity', then
      'DKI Count', 'AI Assets Count', 'Broken URLs Count',
      'Disapprovals Count', 'Seasonal Count', 'URL Expansion Count',
      'Auto-Apply Count', 'Inappropriate Count', 'Spelling Count',
      'Irrelevance Count'
    Never change the tab name, date format, or headers in one script without
    the other — the briefing section silently goes blank on a mismatch.

Usage:
    # All issues from the last 24 hours
    python read_latest_ads_checker.py --sheet-id YOUR_SHEET_ID

    # Critical/High only (the daily-briefing invocation)
    python read_latest_ads_checker.py --sheet-id YOUR_SHEET_ID --critical-only

    # Specific portfolio (matched against the Portfolio column as written)
    python read_latest_ads_checker.py --sheet-id YOUR_SHEET_ID --portfolio north --critical-only

    # JSON output (for programmatic use)
    python read_latest_ads_checker.py --sheet-id YOUR_SHEET_ID --json

Prerequisites:
    - google-ads.yaml at project root (see the google-ads-api-setup skill) —
      its OAuth credentials are reused for the Sheets read
    - pip install gspread google-auth pyyaml
"""

import argparse
import sys
import io
import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.credentials import Credentials
import yaml

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Part of the cached-output contract — must match ads_checker_audit.py
ACCOUNT_HISTORY_TAB_NAME = "Account History"


def get_sheets_client(config_path: str):
    """Get authenticated Google Sheets client (OAuth reused from google-ads.yaml)."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    creds = Credentials(
        token=None,
        refresh_token=config.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=config.get('client_id'),
        client_secret=config.get('client_secret'),
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    return gspread.authorize(creds)


def get_latest_audit_results(sheet_id: str, config_path: str,
                             portfolio=None, critical_only=False, hours_back=24):
    """Read latest audit from Account History tab.

    Args:
        sheet_id: The audit Google Sheet ID
        config_path: Path to google-ads.yaml (for OAuth)
        portfolio: Filter by portfolio (as written in the Portfolio column —
            your registry's portfolio names, 'all', or 'custom' for --cid runs)
        critical_only: Only return CRITICAL/HIGH severity accounts
        hours_back: Only consider audits from last N hours (default 24)

    Returns:
        List of account dicts with issue data
    """
    sheets_client = get_sheets_client(config_path)
    spreadsheet = sheets_client.open_by_key(sheet_id)

    try:
        ws = spreadsheet.worksheet(ACCOUNT_HISTORY_TAB_NAME)
    except gspread.exceptions.WorksheetNotFound:
        return []

    all_data = ws.get_all_values()

    if len(all_data) < 2:  # No data (header only or empty)
        return []

    headers = all_data[0]

    # Find most recent audit date
    cutoff_time = datetime.now() - timedelta(hours=hours_back)

    accounts = []

    # Process rows (newest first if sorted by date)
    for row in all_data[1:]:
        row_dict = dict(zip(headers, row))

        # Parse audit date
        audit_date_str = row_dict.get('Audit Date', '')
        try:
            audit_date = datetime.strptime(audit_date_str, '%Y-%m-%d %H:%M')
        except ValueError:
            continue

        # Only include recent audits
        if audit_date < cutoff_time:
            continue

        # Filter by portfolio if specified
        if portfolio and row_dict.get('Portfolio') != portfolio:
            continue

        # Filter by severity if critical_only
        severity = row_dict.get('Overall Severity', 'OK')
        if critical_only and severity not in ['CRITICAL', 'HIGH']:
            continue

        # Parse issue counts
        account = {
            'audit_date': audit_date_str,
            'portfolio': row_dict.get('Portfolio', ''),
            'cid': row_dict.get('CID', ''),
            'account_name': row_dict.get('Account Name', ''),
            'severity': severity,
            'dki': int(row_dict.get('DKI Count', 0) or 0),
            'ai_assets': int(row_dict.get('AI Assets Count', 0) or 0),
            'broken_urls': int(row_dict.get('Broken URLs Count', 0) or 0),
            'disapprovals': int(row_dict.get('Disapprovals Count', 0) or 0),
            'seasonal': int(row_dict.get('Seasonal Count', 0) or 0),
            'url_expansion': int(row_dict.get('URL Expansion Count', 0) or 0),
            'auto_apply': int(row_dict.get('Auto-Apply Count', 0) or 0),
            'inappropriate': int(row_dict.get('Inappropriate Count', 0) or 0),
            'spelling': int(row_dict.get('Spelling Count', 0) or 0),
            'irrelevance': int(row_dict.get('Irrelevance Count', 0) or 0),
        }

        accounts.append(account)

    return accounts


def get_primary_issues(account):
    """Get the most significant issues for an account (for display).

    Returns string describing top 2-3 issues.
    """
    issues = []

    # Priority order: disapprovals, broken URLs, inappropriate, DKI, spelling, irrelevance
    if account['disapprovals'] > 0:
        issues.append(f"{account['disapprovals']} disapprovals")
    if account['broken_urls'] > 0:
        issues.append(f"{account['broken_urls']} broken URLs")
    if account['inappropriate'] > 0:
        issues.append(f"{account['inappropriate']} inappropriate")
    if account['dki'] > 0:
        issues.append(f"{account['dki']} DKI")
    if account['spelling'] > 0:
        issues.append(f"{account['spelling']} spelling")
    if account['irrelevance'] > 0:
        issues.append(f"{account['irrelevance']} irrelevance")
    if account['seasonal'] > 0:
        issues.append(f"{account['seasonal']} seasonal")
    if account['auto_apply'] > 0:
        issues.append(f"{account['auto_apply']} auto-apply")

    # Return top 3 issues
    return ', '.join(issues[:3]) if issues else 'No actionable issues'


def format_for_briefing(accounts):
    """Format accounts for daily briefing display.

    Returns formatted string ready for briefing output.
    """
    if not accounts:
        return "No creative issues detected in last 24 hours."

    critical = [a for a in accounts if a['severity'] == 'CRITICAL']
    high = [a for a in accounts if a['severity'] == 'HIGH']

    output = []

    if critical:
        output.append("CRITICAL CREATIVE (Fix Immediately):")
        for acc in critical[:10]:  # Top 10
            issues = get_primary_issues(acc)
            output.append(f"  🔴 {acc['account_name']}: {issues}")
        if len(critical) > 10:
            output.append(f"  ... and {len(critical) - 10} more CRITICAL accounts")

    if high:
        output.append("\nHIGH CREATIVE (Fix within 24h):")
        for acc in high[:10]:  # Top 10
            issues = get_primary_issues(acc)
            output.append(f"  🟠 {acc['account_name']}: {issues}")
        if len(high) > 10:
            output.append(f"  ... and {len(high) - 10} more HIGH accounts")

    if not critical and not high:
        return "No CRITICAL or HIGH creative issues in last 24 hours."

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description="Read latest Ads Checker audit results")
    parser.add_argument('--sheet-id', required=True,
                        help='The audit Google Sheet ID (same sheet ads_checker_audit.py writes)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml (default: ./google-ads.yaml)')
    parser.add_argument('--portfolio',
                        help="Filter by portfolio, matched against the Portfolio column "
                             "(your registry's portfolio names, 'all', or 'custom')")
    parser.add_argument('--critical-only', action='store_true',
                        help='Only show CRITICAL and HIGH severity')
    parser.add_argument('--hours-back', type=int, default=24,
                        help='Only consider audits from last N hours (default: 24)')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON instead of formatted text')

    args = parser.parse_args()

    # Get latest results
    accounts = get_latest_audit_results(
        sheet_id=args.sheet_id,
        config_path=args.config,
        portfolio=args.portfolio,
        critical_only=args.critical_only,
        hours_back=args.hours_back
    )

    if args.json:
        # JSON output for programmatic use
        print(json.dumps(accounts, indent=2))
    else:
        # Formatted output for briefing
        output = format_for_briefing(accounts)
        print(output)


if __name__ == "__main__":
    main()
