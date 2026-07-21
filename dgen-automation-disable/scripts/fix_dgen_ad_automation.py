#!/usr/bin/env python3
"""Fix Demand Gen Ad-Level Asset Automation Settings.

Opts out of all automatically created asset settings for Demand Gen ads.
Two-step mutation safety: dry-run generates a deterministic approval code,
re-run with the code to execute.

IMPORTANT: DGen automation operates at the AD level (not campaign level
like PMax). Settings live on `ad_group_ad.ad_group_ad_asset_automation_settings`.

Settings set to OPTED_OUT:
  - GENERATE_DESIGN_VERSIONS_FOR_IMAGES   (adds design elements to images)
  - GENERATE_VIDEOS_FROM_OTHER_ASSETS     (generates videos from images/text)
  - GENERATE_VERTICAL_YOUTUBE_VIDEOS      (converts horizontal to vertical)
  - GENERATE_SHORTER_YOUTUBE_VIDEOS       (shortens videos)
  - GENERATE_LANDING_PAGE_PREVIEW         (default OFF, kept OFF)

Usage:
    # Step 1 — Dry-run preview (prints approval code)
    python fix_dgen_ad_automation.py --cid 1234567890
    python fix_dgen_ad_automation.py --cids "1234567890,2345678901"
    python fix_dgen_ad_automation.py --all

    # Step 2 — Execute with approval code
    python fix_dgen_ad_automation.py --cid 1234567890 APPROVE-XXXXXXXX

    # Post-execute verification (re-queries and confirms OPTED_OUT)
    python fix_dgen_ad_automation.py --cid 1234567890 APPROVE-XXXXXXXX --verify

    # With Google Sheet mutation log (optional, opt-in)
    python fix_dgen_ad_automation.py --cid 1234567890 APPROVE-XXXXXXXX \
        --log-sheet-id YOUR_LOG_SHEET_ID

Prerequisites:
    - google-ads.yaml at project root (Google Ads API credentials)
    - pip install google-ads google-auth google-api-python-client pyyaml

Safety:
    - Dry-run is the default (no approval code = no mutations)
    - Approval code is a SHA-256 hash of the pending work. Same work -> same code.
      If ads change between dry-run and execute, the code changes and execution
      is refused.
    - All mutations logged locally to ./logs/mutations_log.jsonl
    - Optional Google Sheet logging via --log-sheet-id

Critical implementation note — REPLACEMENT BEHAVIOR:
    When updating `ad_group_ad_asset_automation_settings`, you must specify
    ALL applicable settings for the ad type. If you only specify one setting,
    others reset to defaults (OPTED_IN). This script always sets every
    applicable setting for each ad type.
"""

import argparse
import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ---------------------------------------------------------------------------
# DGen settings taxonomy
# ---------------------------------------------------------------------------

DGEN_ASSET_AUTOMATION_TYPES = {
    "GENERATE_DESIGN_VERSIONS_FOR_IMAGES": "Image design versions (adds design elements)",
    "GENERATE_VIDEOS_FROM_OTHER_ASSETS": "Video generation (from images/text)",
    "GENERATE_VERTICAL_YOUTUBE_VIDEOS": "Vertical video conversion",
    "GENERATE_SHORTER_YOUTUBE_VIDEOS": "Video shortening",
    "GENERATE_LANDING_PAGE_PREVIEW": "Landing page screenshot in ads",
}

AD_TYPE_SETTINGS = {
    "DEMAND_GEN_MULTI_ASSET_AD": [
        "GENERATE_DESIGN_VERSIONS_FOR_IMAGES",
        "GENERATE_VIDEOS_FROM_OTHER_ASSETS",
    ],
    "DEMAND_GEN_VIDEO_RESPONSIVE_AD": [
        "GENERATE_VERTICAL_YOUTUBE_VIDEOS",
        "GENERATE_SHORTER_YOUTUBE_VIDEOS",
        "GENERATE_LANDING_PAGE_PREVIEW",
    ],
    "DEMAND_GEN_CAROUSEL_AD": [],  # No automation settings
    "DEMAND_GEN_PRODUCT_AD": [],   # No automation settings
}


# ---------------------------------------------------------------------------
# Inline two-step approval (mutation-safety pattern) — deterministic approval codes
# ---------------------------------------------------------------------------

def compute_approval_code(all_changes) -> str:
    """Compute deterministic APPROVAL code from the hash of pending mutations.

    Same pending work -> same code. If ads change between dry-run and execute,
    the code changes, so stale approvals fail safely.
    """
    key_parts = []
    for change_set in all_changes:
        cid = change_set['account']['cid']
        for ad in change_set['ads']:
            ad_id = ad['ad_id']
            settings = ','.join(sorted(ad['settings_to_fix']))
            key_parts.append(f"{cid}|{ad_id}|{settings}")
    key = '\n'.join(sorted(key_parts))
    digest = hashlib.sha256(key.encode('utf-8')).hexdigest()[:8].upper()
    return f"APPROVE-{digest}"


# ---------------------------------------------------------------------------
# Local JSONL mutation logger (no external dependencies)
# ---------------------------------------------------------------------------

class LocalMutationLogger:
    """Simple append-only JSONL log of all mutations this script performs."""

    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_log = self.log_dir / "mutations_log.jsonl"

    def log(self, approval_code, account_cid, account_name, action_type, details, success, error=None):
        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "approval_code": approval_code,
            "account_cid": account_cid,
            "account_name": account_name,
            "action_type": action_type,
            "details": details,
            "success": success,
            "error": error,
        }
        with open(self.jsonl_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')


def log_mutation_to_sheet(
    sheet_id: str,
    config_path: str,
    account_name,
    cid,
    action_type,
    details,
    success,
    error,
    approval_code,
):
    """Log a mutation to a central Google Sheet (optional)."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        import yaml

        if not os.path.exists(config_path):
            print(f"  Warning: Google Sheet logging skipped — {config_path} not found.")
            return False

        with open(config_path, 'r', encoding='utf-8') as f:
            ads_config = yaml.safe_load(f)

        creds = Credentials(
            token=None,
            refresh_token=ads_config.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=ads_config.get('client_id'),
            client_secret=ads_config.get('client_secret'),
            scopes=['https://www.googleapis.com/auth/spreadsheets'],
        )
        creds.refresh(Request())

        service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

        row = [[
            datetime.now(timezone.utc).isoformat(),
            account_name,
            cid,
            action_type,
            details,
            'YES' if success else 'NO',
            error or '',
            approval_code,
        ]]

        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range='A:H',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': row},
        ).execute()

        return True

    except Exception as e:
        print(f"  Warning: Could not log to Google Sheet: {e}")
        return False


# ---------------------------------------------------------------------------
# Account discovery
# ---------------------------------------------------------------------------

def get_mcc_accounts(client, login_customer_id):
    """Walk the MCC for enabled non-manager accounts."""
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT
            customer_client.id,
            customer_client.descriptive_name,
            customer_client.status,
            customer_client.manager
        FROM customer_client
        WHERE customer_client.status = 'ENABLED'
          AND customer_client.manager = FALSE
    """
    accounts = []
    try:
        response = ga_service.search(customer_id=login_customer_id, query=query)
        for row in response:
            accounts.append({
                'cid': str(row.customer_client.id),
                'name': row.customer_client.descriptive_name or f"Account {row.customer_client.id}",
            })
    except GoogleAdsException as ex:
        msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
        print(f"ERROR walking MCC: {msg}")
        sys.exit(1)
    return accounts


# ---------------------------------------------------------------------------
# Query & mutation
# ---------------------------------------------------------------------------

def get_dgen_ads_needing_fix(client, customer_id):
    """Get DGen ads that need asset automation settings fixed.

    Only includes ads from campaigns that are:
    - ENABLED status
    - Not ended (end_date >= today, or no end date set)
    """
    ga_service = client.get_service("GoogleAdsService")
    today = datetime.now().strftime('%Y-%m-%d')

    query = f"""
        SELECT
            ad_group_ad.resource_name,
            ad_group_ad.ad.id,
            ad_group_ad.ad.type,
            ad_group_ad.ad_group_ad_asset_automation_settings,
            campaign.name,
            ad_group.name
        FROM ad_group_ad
        WHERE campaign.advertising_channel_type = 'DEMAND_GEN'
            AND campaign.status = 'ENABLED'
            AND ad_group_ad.status = 'ENABLED'
            AND campaign.end_date_time >= '{today}'
        ORDER BY campaign.name, ad_group.name
    """

    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)
        ads = []
        for batch in response:
            for row in batch.results:
                ad_type = row.ad_group_ad.ad.type.name
                applicable_types = AD_TYPE_SETTINGS.get(ad_type, [])
                if not applicable_types:
                    continue

                current_settings = {atype: "OPTED_IN" for atype in applicable_types}
                for setting in row.ad_group_ad.ad_group_ad_asset_automation_settings:
                    type_name = setting.asset_automation_type.name
                    status_name = setting.asset_automation_status.name
                    if type_name in applicable_types:
                        current_settings[type_name] = status_name

                settings_to_fix = [t for t, s in current_settings.items() if s != "OPTED_OUT"]

                if settings_to_fix:
                    ads.append({
                        'resource_name': row.ad_group_ad.resource_name,
                        'ad_id': row.ad_group_ad.ad.id,
                        'ad_type': ad_type,
                        'campaign_name': row.campaign.name,
                        'ad_group_name': row.ad_group.name,
                        'current_settings': current_settings,
                        'settings_to_fix': settings_to_fix,
                        'applicable_types': applicable_types,
                    })
        return ads

    except GoogleAdsException as ex:
        print(f"  ERROR querying account {customer_id}: {ex.failure.errors[0].message}")
        return None


def print_dry_run_report(account_name, customer_id, ads):
    """Print what would be changed (dry run)."""
    print("=" * 80)
    print(f"ACCOUNT: {account_name}")
    print(f"CID: {customer_id}")
    print("=" * 80)

    if not ads:
        print("  No DGen ads need fixing (all compliant or no DGen campaigns)")
        print()
        return 0

    total_changes = 0
    for ad in ads:
        print(f"\n  Campaign: {ad['campaign_name']}")
        print(f"  Ad Group: {ad['ad_group_name']}")
        print(f"  Ad Type: {ad['ad_type']}")
        print(f"  Settings to change ({len(ad['settings_to_fix'])}):")
        for automation_type in ad['settings_to_fix']:
            description = DGEN_ASSET_AUTOMATION_TYPES[automation_type]
            current = ad['current_settings'][automation_type]
            print(f"    - {description}: {current} -> OPTED_OUT")
            total_changes += 1
    print()
    return total_changes


def execute_fix(client, customer_id, ads):
    """Execute the mutation to fix asset automation settings."""
    if not ads:
        return True, 0

    ad_group_ad_service = client.get_service("AdGroupAdService")
    operations = []

    for ad in ads:
        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.update
        ad_group_ad.resource_name = ad['resource_name']

        # REPLACEMENT BEHAVIOR: must specify ALL applicable settings for this ad type.
        # Otherwise, unspecified settings reset to default (OPTED_IN).
        for automation_type in ad['applicable_types']:
            setting = client.get_type("AdGroupAdAssetAutomationSetting")
            setting.asset_automation_type = getattr(
                client.enums.AssetAutomationTypeEnum, automation_type
            )
            setting.asset_automation_status = client.enums.AssetAutomationStatusEnum.OPTED_OUT
            ad_group_ad.ad_group_ad_asset_automation_settings.append(setting)

        operation.update_mask.CopyFrom(
            field_mask_pb2.FieldMask(paths=["ad_group_ad_asset_automation_settings"])
        )
        operations.append(operation)

    try:
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=operations,
        )
        return True, len(response.results)
    except GoogleAdsException as ex:
        print(f"  ERROR executing mutation: {ex.failure.errors[0].message}")
        return False, 0


def run_verification_query(client, customer_id, account_name):
    """Post-execute: re-query to confirm all DGen ads are now OPTED_OUT."""
    print("\n" + "=" * 80)
    print(f"VERIFICATION: {account_name}")
    print("=" * 80)

    ga_service = client.get_service("GoogleAdsService")
    today = datetime.now().strftime('%Y-%m-%d')
    query = f"""
        SELECT
            ad_group_ad.resource_name,
            ad_group_ad.ad.type,
            ad_group_ad.ad_group_ad_asset_automation_settings,
            campaign.name
        FROM ad_group_ad
        WHERE campaign.advertising_channel_type = 'DEMAND_GEN'
            AND campaign.status = 'ENABLED'
            AND ad_group_ad.status = 'ENABLED'
            AND campaign.end_date_time >= '{today}'
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        compliant = 0
        non_compliant = 0

        for row in response:
            ad_type = row.ad_group_ad.ad.type.name
            applicable_types = AD_TYPE_SETTINGS.get(ad_type, [])
            if not applicable_types:
                continue

            current_settings = {atype: "OPTED_IN" for atype in applicable_types}
            for setting in row.ad_group_ad.ad_group_ad_asset_automation_settings:
                type_name = setting.asset_automation_type.name
                status_name = setting.asset_automation_status.name
                if type_name in applicable_types:
                    current_settings[type_name] = status_name

            is_compliant = all(s == "OPTED_OUT" for s in current_settings.values())
            if is_compliant:
                compliant += 1
            else:
                non_compliant += 1
                print(f"  Non-compliant: {row.campaign.name}")
                for atype, status in current_settings.items():
                    if status != "OPTED_OUT":
                        print(f"    - {atype}: {status}")

        total = compliant + non_compliant
        if total > 0:
            if non_compliant == 0:
                print(f"  All {compliant} DGen ads are now compliant")
            else:
                print(f"  {compliant}/{total} DGen ads are compliant ({non_compliant} still need fixing)")
        else:
            print("  No DGen ads found")

    except GoogleAdsException as ex:
        print(f"  ERROR running verification: {ex.failure.errors[0].message}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Fix DGen ad-level asset automation settings (set all to OPTED_OUT).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Step 1 — Dry-run:  python fix_dgen_ad_automation.py --cid 1234567890\n"
               "Step 2 — Execute:  python fix_dgen_ad_automation.py --cid 1234567890 APPROVE-XXXXXXXX",
    )

    account_group = parser.add_mutually_exclusive_group(required=True)
    account_group.add_argument('--cid', help='Single account CID')
    account_group.add_argument('--cids', help='Comma-separated list of CIDs')
    account_group.add_argument('--all', action='store_true',
                               help='All enabled accounts under MCC (from login_customer_id in google-ads.yaml)')

    parser.add_argument('approval_code', nargs='?', default=None,
                        help='APPROVE-XXXXXXXX code from dry-run (omit for dry-run preview)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Google Ads credentials YAML (default: ./google-ads.yaml)')
    parser.add_argument('--log-dir', default='logs',
                        help='Directory for mutation JSONL log (default: ./logs)')
    parser.add_argument('--log-sheet-id', default=None,
                        help='(Optional) Google Sheet ID for central mutation log')
    parser.add_argument('--verify', action='store_true',
                        help='After execute, re-query to confirm compliance')

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"ERROR: Google Ads credentials not found at {args.config}")
        print("See google-ads-api-setup skill for setup.")
        sys.exit(1)

    client = GoogleAdsClient.load_from_storage(args.config)

    # Resolve accounts
    if args.cid:
        accounts = [{'cid': args.cid, 'name': f"Account {args.cid}"}]
    elif args.cids:
        accounts = [{'cid': c.strip(), 'name': f"Account {c.strip()}"} for c in args.cids.split(',') if c.strip()]
    else:
        import yaml
        with open(args.config, 'r', encoding='utf-8') as f:
            ads_config = yaml.safe_load(f)
        login_cid = str(ads_config.get('login_customer_id', ''))
        if not login_cid:
            print("ERROR: --all requires login_customer_id in google-ads.yaml")
            sys.exit(1)
        print(f"Walking MCC {login_cid} for enabled accounts...")
        accounts = get_mcc_accounts(client, login_cid)
        print(f"Found {len(accounts)} account(s)\n")

    mode = "EXECUTE" if args.approval_code else "DRY RUN"
    print("\n" + "=" * 80)
    print(f"DGEN AD AUTOMATION FIX - {mode}")
    print("=" * 80)
    print(f"Accounts to process: {len(accounts)}")
    print("=" * 80 + "\n")

    # Collect changes
    all_changes = []
    for account in accounts:
        ads = get_dgen_ads_needing_fix(client, account['cid'])
        if ads is None:
            continue
        changes = print_dry_run_report(account['name'], account['cid'], ads)
        if ads:
            all_changes.append({
                'account': account,
                'ads': ads,
                'change_count': changes,
            })

    # Summary
    total_accounts = len(all_changes)
    total_ads = sum(len(c['ads']) for c in all_changes)
    total_changes = sum(c['change_count'] for c in all_changes)

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Accounts with changes needed: {total_accounts}")
    print(f"Ads to update: {total_ads}")
    print(f"Total settings to change: {total_changes}")
    print("=" * 80)

    if total_changes == 0:
        print("\nAll accounts are compliant - no changes needed!")
        return

    expected_code = compute_approval_code(all_changes)

    # Dry-run mode
    if args.approval_code is None:
        print()
        print("=" * 80)
        print(f"APPROVAL CODE: {expected_code}")
        print("=" * 80)
        print()
        print("To execute these mutations, re-run with the code above:")
        if args.cid:
            print(f"  python scripts/fix_dgen_ad_automation.py --cid {args.cid} {expected_code}")
        elif args.cids:
            print(f"  python scripts/fix_dgen_ad_automation.py --cids {args.cids} {expected_code}")
        else:
            print(f"  python scripts/fix_dgen_ad_automation.py --all {expected_code}")
        print()
        print("If ads change before you execute, the code will no longer match.")
        return

    # Execute mode — validate approval code
    if args.approval_code != expected_code:
        print()
        print("=" * 80)
        print("ERROR: Approval code mismatch.")
        print("=" * 80)
        print(f"  Provided: {args.approval_code}")
        print(f"  Expected: {expected_code}")
        print()
        print("The approval code is derived from the hash of pending mutations.")
        print("If ads changed since your dry-run, the code changes.")
        print("Re-run without an approval code to see current state and get a fresh code.")
        sys.exit(1)

    # Execute
    print(f"\nApproval code validated. Executing {total_changes} setting changes across {total_ads} ads...")

    mutation_logger = LocalMutationLogger(args.log_dir)
    success_count = 0
    fail_count = 0

    for change_set in all_changes:
        account = change_set['account']
        ads = change_set['ads']

        print(f"\n  Updating {account['name']} ({account['cid']})...", end=" ")
        success, updated = execute_fix(client, account['cid'], ads)

        settings_changed = [
            f"{ad['ad_type']}: {setting}"
            for ad in ads
            for setting in ad['settings_to_fix']
        ]
        details_dict = {
            "ads_updated": updated if success else 0,
            "settings_changed": settings_changed,
            "ad_types": list({ad['ad_type'] for ad in ads}),
        }
        details_summary = f"Disabled {len(settings_changed)} automation settings on {len(ads)} DGen ads"

        if success:
            print(f"{updated} ad(s) updated")
            success_count += updated
            mutation_logger.log(
                approval_code=args.approval_code,
                account_cid=account['cid'],
                account_name=account['name'],
                action_type="DISABLE_DGEN_AUTOMATION",
                details=details_dict,
                success=True,
            )
            if args.log_sheet_id:
                log_mutation_to_sheet(
                    sheet_id=args.log_sheet_id,
                    config_path=args.config,
                    account_name=account['name'],
                    cid=account['cid'],
                    action_type="DISABLE_DGEN_AUTOMATION",
                    details=details_summary,
                    success=True,
                    error=None,
                    approval_code=args.approval_code,
                )
        else:
            print("Failed")
            fail_count += len(ads)
            mutation_logger.log(
                approval_code=args.approval_code,
                account_cid=account['cid'],
                account_name=account['name'],
                action_type="DISABLE_DGEN_AUTOMATION",
                details=details_dict,
                success=False,
                error="Mutation failed",
            )
            if args.log_sheet_id:
                log_mutation_to_sheet(
                    sheet_id=args.log_sheet_id,
                    config_path=args.config,
                    account_name=account['name'],
                    cid=account['cid'],
                    action_type="DISABLE_DGEN_AUTOMATION",
                    details=details_summary,
                    success=False,
                    error="Mutation failed",
                    approval_code=args.approval_code,
                )

    print("\n" + "=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)
    print(f"Successfully updated: {success_count} ads")
    if fail_count:
        print(f"Failed: {fail_count} ads")
    print(f"\nLogged to: {mutation_logger.jsonl_log}")
    if args.log_sheet_id:
        print(f"Sheet log: https://docs.google.com/spreadsheets/d/{args.log_sheet_id}")
    print("=" * 80)

    # Verification
    if args.verify:
        if len(accounts) == 1:
            run_verification_query(client, accounts[0]['cid'], accounts[0]['name'])
        else:
            print("\nNote: --verify runs on single-account invocations only.")


if __name__ == "__main__":
    main()
