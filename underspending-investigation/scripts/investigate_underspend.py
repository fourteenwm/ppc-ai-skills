#!/usr/bin/env python3
"""Underspend Investigation.

Investigates why a Google Ads account is underspending and prints the evidence
needed for a root-cause diagnosis: 7-day campaign spend vs. budget, impression
share analysis with threshold-based interpretation, and month-to-date pacing.

Read-only by design: the script queries the account and prints findings.
It never writes to Google Ads.

Usage:
    # Investigate by customer ID
    python investigate_underspend.py --cid 1234567890

    # Investigate by account name (resolved via ./accounts.md, or by walking
    # the MCC in google-ads.yaml when no accounts.md exists)
    python investigate_underspend.py "Acme Plumbing - Search"

    # Custom registry / credentials locations
    python investigate_underspend.py "Acme Plumbing" --accounts /path/to/accounts.md --config google-ads.yaml

    # Pace against the true contracted monthly budget instead of the
    # daily-budget estimate
    python investigate_underspend.py --cid 1234567890 --monthly-budget 5000

Output sections:
    1. Campaign spend analysis (last 7 days) — per-campaign budget,
       utilization %, bidding strategy, performance
    2. Impression share analysis — Search IS, Budget Lost IS, Rank Lost IS,
       with a threshold-based root-cause readout per campaign
    3. Month-to-date pacing — MTD spend vs. expected spend at today's
       day-of-month, variance %

Prerequisites:
    - google-ads.yaml at project root (see the google-ads-api-setup skill)
    - pip install google-ads pyyaml
    - Optional: accounts.md at project root for name-to-CID resolution

accounts.md format:
    ### CID: 123-456-7890
    - Account Name (first line is used as display name)
    - Alias (optional additional names under same CID)

    ### CID: 234-567-8901
    - Another Account Name
"""

import argparse
import calendar
import io
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def parse_accounts_file(accounts_path: Path) -> list[tuple[str, list[str]]]:
    """Parse accounts.md to extract CIDs and their associated account names.

    Returns:
        List of (cid_without_dashes, [names]) tuples. The first name under a
        CID is its display name; any further lines are aliases for matching.
    """
    content = accounts_path.read_text(encoding="utf-8")

    # Pattern to match CID headers: ### CID: 123-456-7890
    cid_pattern = re.compile(r"### CID: (\d{3}-\d{3}-\d{4})")

    # Pattern to match account names (lines starting with "- ")
    account_pattern = re.compile(r"^- (.+)$")

    accounts = []
    current_cid = None
    current_names = []

    for line in content.split("\n"):
        cid_match = cid_pattern.search(line)
        if cid_match:
            if current_cid and current_names:
                accounts.append((current_cid.replace("-", ""), current_names))
            current_cid = cid_match.group(1)
            current_names = []
            continue

        account_match = account_pattern.match(line)
        if account_match and current_cid:
            current_names.append(account_match.group(1))

    if current_cid and current_names:
        accounts.append((current_cid.replace("-", ""), current_names))

    return accounts


def get_login_customer_id(config_path: str) -> str:
    """Read login_customer_id (the MCC) from google-ads.yaml, if present."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        value = data.get('login_customer_id', '')
        return str(value).replace('-', '') if value else ''
    except Exception:
        return ''


def get_mcc_accounts(ads_client: GoogleAdsClient, login_customer_id: str) -> list[tuple[str, str]]:
    """Walk the MCC's customer_client resource to get all active accounts.

    Returns:
        List of (cid_without_dashes, descriptive_name) tuples
    """
    ga_service = ads_client.get_service("GoogleAdsService")
    query = """
        SELECT
            customer_client.client_customer,
            customer_client.descriptive_name,
            customer_client.id,
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
            cid = str(row.customer_client.id)
            name = row.customer_client.descriptive_name or f"Account {cid}"
            accounts.append((cid, name))
    except GoogleAdsException as ex:
        error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
        print(f"Warning: MCC traversal failed: {error_msg}")

    return accounts


def resolve_account_name(account_name, accounts_path, ads_client, config_path):
    """Resolve an account name to a customer ID.

    Tries the local accounts.md registry first. If no registry file exists,
    falls back to walking the MCC (customer_client) using the
    login_customer_id from google-ads.yaml.

    Returns:
        (customer_id, display_name) tuple, or None if no match found.
    """
    candidates = []
    query = account_name.lower()

    accounts_file = Path(accounts_path)
    if accounts_file.exists():
        for cid, names in parse_accounts_file(accounts_file):
            for name in names:
                if query in name.lower() or name.lower() in query:
                    candidates.append((cid, names[0]))
                    break
    else:
        login_cid = get_login_customer_id(config_path)
        if not login_cid:
            print(f"No accounts file at {accounts_path} and no login_customer_id in config.")
            print("Cannot resolve account names - provide --cid instead.")
            return None
        print(f"[No accounts file at {accounts_path} — searching the MCC for a name match]")
        for cid, name in get_mcc_accounts(ads_client, login_cid):
            if query in name.lower() or name.lower() in query:
                candidates.append((cid, name))

    if not candidates:
        return None

    if len(candidates) > 1:
        print(f"Account name '{account_name}' matched {len(candidates)} accounts:")
        for cid, name in candidates:
            print(f"  {cid}  {name}")
        print("Re-run with --cid to disambiguate.")
        sys.exit(1)

    return candidates[0]


def run_investigation(customer_id, account_name, ads_client, monthly_budget=None):
    """Run the standardized underspend investigation."""

    ga_service = ads_client.get_service("GoogleAdsService")

    print("=" * 100)
    print("UNDERSPEND INVESTIGATION")
    print("=" * 100)
    print(f"Account: {account_name}")
    print(f"Customer ID: {customer_id}")
    print(f"Investigation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get current month info
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    days_in_month = calendar.monthrange(current_year, current_month)[1]
    days_elapsed = now.day

    # ============================================================================
    # STEP 1: CAMPAIGN SPEND ANALYSIS (Last 7 Days)
    # ============================================================================
    print("STEP 1: CAMPAIGN SPEND ANALYSIS (Last 7 Days)")
    print("=" * 100)
    print()

    # Query for campaign budget and spend info
    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign.bidding_strategy_type,
            campaign_budget.amount_micros,
            campaign_budget.explicitly_shared,
            metrics.cost_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.conversions,
            metrics.conversions_value
        FROM campaign
        WHERE segments.date DURING LAST_7_DAYS
        ORDER BY campaign.name
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)

        campaigns_data = {}
        for row in response:
            campaign_id = row.campaign.id
            campaign_name = row.campaign.name
            status = row.campaign.status.name
            channel_type = row.campaign.advertising_channel_type.name
            bidding_strategy = row.campaign.bidding_strategy_type.name

            # Budget info
            budget_micros = row.campaign_budget.amount_micros
            is_shared = row.campaign_budget.explicitly_shared

            # Performance metrics
            cost_micros = row.metrics.cost_micros
            impressions = row.metrics.impressions
            clicks = row.metrics.clicks
            conversions = row.metrics.conversions
            conv_value = row.metrics.conversions_value

            if campaign_id not in campaigns_data:
                campaigns_data[campaign_id] = {
                    'name': campaign_name,
                    'status': status,
                    'channel_type': channel_type,
                    'bidding_strategy': bidding_strategy,
                    'budget_micros': budget_micros,
                    'is_shared': is_shared,
                    'total_cost_micros': 0,
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'total_conversions': 0,
                    'total_conv_value': 0
                }

            campaigns_data[campaign_id]['total_cost_micros'] += cost_micros
            campaigns_data[campaign_id]['total_impressions'] += impressions
            campaigns_data[campaign_id]['total_clicks'] += clicks
            campaigns_data[campaign_id]['total_conversions'] += conversions
            campaigns_data[campaign_id]['total_conv_value'] += conv_value

        print(f"Found {len(campaigns_data)} campaign(s)")
        print()

        total_spend_7day = 0
        total_budget_7day = 0

        for campaign_id, data in sorted(campaigns_data.items(),
                                        key=lambda x: x[1]['total_cost_micros'],
                                        reverse=True):
            daily_budget = data['budget_micros'] / 1_000_000
            budget_7day = daily_budget * 7
            spend_7day = data['total_cost_micros'] / 1_000_000
            utilization_pct = (spend_7day / budget_7day * 100) if budget_7day > 0 else 0

            total_spend_7day += spend_7day
            total_budget_7day += budget_7day

            budget_type = "SHARED" if data['is_shared'] else "INDIVIDUAL"

            # Only show campaigns with spend > $0
            if spend_7day > 0:
                print(f"Campaign: {data['name']}")
                print(f"  Status: {data['status']}")
                print(f"  Type: {data['channel_type']}")
                print(f"  Bidding: {data['bidding_strategy']}")
                print(f"  Budget Type: {budget_type}")
                print(f"  Daily Budget: ${daily_budget:,.2f}")
                print(f"  7-Day Budget: ${budget_7day:,.2f}")
                print(f"  7-Day Spend: ${spend_7day:,.2f}")
                print(f"  Utilization: {utilization_pct:.1f}%")
                print(f"  Impressions: {data['total_impressions']:,}")
                print(f"  Clicks: {data['total_clicks']:,}")
                if data['total_conversions'] > 0:
                    cpa = spend_7day / data['total_conversions']
                    print(f"  Conversions: {data['total_conversions']:.1f} (CPA: ${cpa:.2f})")
                if data['total_conv_value'] > 0:
                    roas = data['total_conv_value'] / spend_7day if spend_7day > 0 else 0
                    print(f"  Conv Value: ${data['total_conv_value']:.2f} (ROAS: {roas:.2f}x)")
                print()

        overall_utilization = (total_spend_7day / total_budget_7day * 100) if total_budget_7day > 0 else 0

        print("-" * 100)
        print(f"OVERALL 7-DAY SUMMARY:")
        print(f"  Total 7-Day Budget: ${total_budget_7day:,.2f}")
        print(f"  Total 7-Day Spend: ${total_spend_7day:,.2f}")
        print(f"  Overall Utilization: {overall_utilization:.1f}%")
        print("-" * 100)
        print()

    except Exception as e:
        print(f"Error querying campaigns: {e}")
        import traceback
        traceback.print_exc()
        return

    # ============================================================================
    # STEP 2: IMPRESSION SHARE ANALYSIS
    # ============================================================================
    print("STEP 2: IMPRESSION SHARE ANALYSIS (Last 7 Days)")
    print("=" * 100)
    print()

    # Query for impression share metrics
    is_query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.advertising_channel_type,
            metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share,
            metrics.impressions
        FROM campaign
        WHERE segments.date DURING LAST_7_DAYS
        AND campaign.advertising_channel_type IN ('SEARCH', 'PERFORMANCE_MAX')
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=is_query)

        impression_share_data = {}
        for row in response:
            campaign_id = row.campaign.id
            campaign_name = row.campaign.name
            channel_type = row.campaign.advertising_channel_type.name

            if campaign_id not in impression_share_data:
                impression_share_data[campaign_id] = {
                    'name': campaign_name,
                    'channel_type': channel_type,
                    'search_is': 0,
                    'budget_lost_is': 0,
                    'rank_lost_is': 0,
                    'total_impressions': 0,
                    'data_points': 0
                }

            # The API returns impression share metrics as fractions (0-1);
            # convert to percentages so the thresholds below read naturally.
            if hasattr(row.metrics, 'search_impression_share'):
                impression_share_data[campaign_id]['search_is'] += row.metrics.search_impression_share * 100
            if hasattr(row.metrics, 'search_budget_lost_impression_share'):
                impression_share_data[campaign_id]['budget_lost_is'] += row.metrics.search_budget_lost_impression_share * 100
            if hasattr(row.metrics, 'search_rank_lost_impression_share'):
                impression_share_data[campaign_id]['rank_lost_is'] += row.metrics.search_rank_lost_impression_share * 100
            impression_share_data[campaign_id]['total_impressions'] += row.metrics.impressions
            impression_share_data[campaign_id]['data_points'] += 1

        if not impression_share_data:
            print("No Search or Performance Max campaigns found.")
            print()
        else:
            all_budget_lost = []
            all_rank_lost = []
            all_search_is = []

            for campaign_id, data in impression_share_data.items():
                # Average the impression share metrics
                num_days = data['data_points'] if data['data_points'] > 0 else 1
                search_is = data['search_is'] / num_days
                budget_lost_is = data['budget_lost_is'] / num_days
                rank_lost_is = data['rank_lost_is'] / num_days

                # Only show campaigns with impressions
                if data['total_impressions'] > 0:
                    print(f"Campaign: {data['name']}")
                    print(f"  Type: {data['channel_type']}")
                    print(f"  Search Impression Share: {search_is:.2f}%")
                    print(f"  Budget Lost IS: {budget_lost_is:.2f}%")
                    print(f"  Rank Lost IS: {rank_lost_is:.2f}%")
                    print(f"  Total Impressions (7-day): {data['total_impressions']:,}")

                    # Pmax does not expose meaningful Search IS metrics, so it
                    # is excluded from the Search decision tree and averages.
                    if data['channel_type'] != 'PERFORMANCE_MAX':
                        all_search_is.append(search_is)
                        all_budget_lost.append(budget_lost_is)
                        all_rank_lost.append(rank_lost_is)

                    # Diagnose root cause
                    print(f"\n  ROOT CAUSE ANALYSIS:")
                    if data['channel_type'] == 'PERFORMANCE_MAX':
                        print(f"    [i] PERFORMANCE MAX - Search IS metrics are not meaningful for Pmax")
                        print(f"    -> Diagnose via budget utilization % and performance vs. goal (STEP 1)")
                    elif budget_lost_is > 30:
                        print(f"    [!] SEVERE BUDGET CONSTRAINT (Budget Lost IS > 30%)")
                        print(f"    -> Recommendation: Increase budget significantly")
                    elif budget_lost_is > 10:
                        print(f"    [!] MODERATE BUDGET CONSTRAINT (Budget Lost IS 10-30%)")
                        print(f"    -> Recommendation: Consider budget increase")
                    elif budget_lost_is < 10 and rank_lost_is > 50:
                        print(f"    [!] SEVERE BID/QUALITY ISSUES (Rank Lost IS > 50%)")
                        print(f"    -> Recommendation: Increase bids or improve quality score")
                        print(f"    -> Smart bidding wants to bid higher but is capped by budget")
                    elif budget_lost_is < 10 and rank_lost_is > 30:
                        print(f"    [!] MODERATE BID/QUALITY ISSUES (Rank Lost IS 30-50%)")
                        print(f"    -> Recommendation: Review bids and ad quality")
                    elif search_is > 80 and budget_lost_is < 10 and rank_lost_is < 10:
                        print(f"    [OK] LOW DEMAND / HIGH CAPTURE RATE")
                        print(f"    -> Account is capturing most available impressions")
                        print(f"    -> Underspending is normal for this search volume")
                    else:
                        print(f"    [?] MIXED FACTORS")
                        print(f"    -> Review targeting, ad schedules, and campaign settings")

                    print()

            # Overall summary (Search campaigns only)
            if all_search_is:
                avg_search_is = sum(all_search_is) / len(all_search_is)
                avg_budget_lost = sum(all_budget_lost) / len(all_budget_lost)
                avg_rank_lost = sum(all_rank_lost) / len(all_rank_lost)

                print("-" * 100)
                print("OVERALL IMPRESSION SHARE SUMMARY (Search campaigns):")
                print(f"  Average Search IS: {avg_search_is:.2f}%")
                print(f"  Average Budget Lost IS: {avg_budget_lost:.2f}%")
                print(f"  Average Rank Lost IS: {avg_rank_lost:.2f}%")
                print("-" * 100)
                print()

    except Exception as e:
        print(f"Error querying impression share: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================================
    # STEP 3: MONTH-TO-DATE PACING ANALYSIS
    # ============================================================================
    print("STEP 3: MONTH-TO-DATE PACING ANALYSIS")
    print("=" * 100)
    print()

    mtd_query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign_budget.amount_micros,
            metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING THIS_MONTH
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=mtd_query)

        mtd_campaigns = {}
        for row in response:
            campaign_id = row.campaign.id
            campaign_name = row.campaign.name
            budget_micros = row.campaign_budget.amount_micros
            cost_micros = row.metrics.cost_micros

            if campaign_id not in mtd_campaigns:
                mtd_campaigns[campaign_id] = {
                    'name': campaign_name,
                    'budget_micros': budget_micros,
                    'total_cost_micros': 0
                }

            mtd_campaigns[campaign_id]['total_cost_micros'] += cost_micros

        total_mtd_spend = 0
        estimated_monthly_budget = 0

        for campaign_id, data in mtd_campaigns.items():
            daily_budget = data['budget_micros'] / 1_000_000
            estimated_monthly_budget += daily_budget * days_in_month
            total_mtd_spend += data['total_cost_micros'] / 1_000_000

        if monthly_budget is not None:
            total_monthly_budget = monthly_budget
            print("[Monthly budget supplied via --monthly-budget]")
        else:
            total_monthly_budget = estimated_monthly_budget
            print("[Monthly budget estimated from current daily budgets x days in month]")
            print("[If your contracted monthly budget differs, re-run with --monthly-budget]")
        print()

        total_expected_spend = (total_monthly_budget / days_in_month) * days_elapsed
        total_variance = total_mtd_spend - total_expected_spend
        total_variance_pct = (total_variance / total_expected_spend * 100) if total_expected_spend > 0 else 0

        pct_through_month = days_elapsed / days_in_month * 100
        pct_spent = (total_mtd_spend / total_monthly_budget * 100) if total_monthly_budget > 0 else 0

        print(f"Month: {now.strftime('%B %Y')}")
        print(f"Days Elapsed: {days_elapsed} / {days_in_month}")
        print()
        print(f"Total Monthly Budget: ${total_monthly_budget:,.2f}")
        print(f"MTD Spend: ${total_mtd_spend:,.2f}")
        print(f"Expected Spend (Day {days_elapsed}): ${total_expected_spend:,.2f}")
        print(f"% Through Month: {pct_through_month:.2f}%")
        print(f"% of Budget Spent: {pct_spent:.2f}%")
        print(f"Variance: ${total_variance:+,.2f} ({total_variance_pct:+.2f}%)")
        print()

        if total_variance_pct < 0:
            print(f"STATUS: UNDERSPENDING by {abs(total_variance_pct):.2f}%")
        elif total_variance_pct > 0:
            print(f"STATUS: OVERSPENDING by {total_variance_pct:.2f}%")
        else:
            print(f"STATUS: ON PACE")

        print()

    except Exception as e:
        print(f"Error querying MTD data: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 100)
    print("Investigation complete. Review findings above.")
    print("=" * 100)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Underspend investigation for any Google Ads account',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Investigate by customer ID
  python investigate_underspend.py --cid 1234567890

  # Investigate by account name (resolved via ./accounts.md, or the MCC)
  python investigate_underspend.py "Acme Plumbing - Search"

  # Pace against the contracted monthly budget
  python investigate_underspend.py --cid 1234567890 --monthly-budget 5000
        """
    )

    parser.add_argument('account_name', nargs='?',
                        help='Account name to investigate (resolved via accounts.md or the MCC)')
    parser.add_argument('--cid', '--customer-id', dest='customer_id',
                        help='Customer ID, digits or 123-456-7890 form (skips name resolution)')
    parser.add_argument('--accounts', default='accounts.md',
                        help='Path to accounts.md registry for name resolution (default: ./accounts.md)')
    parser.add_argument('--config', default='google-ads.yaml',
                        help='Path to google-ads.yaml credentials file (default: ./google-ads.yaml)')
    parser.add_argument('--monthly-budget', type=float, default=None,
                        help='Contracted monthly budget in account currency for pacing math '
                             '(default: estimate from current daily budgets)')

    args = parser.parse_args()

    # Validate arguments
    if not args.account_name and not args.customer_id:
        parser.error("Must provide either account_name or --cid")

    # Load Google Ads client
    ads_client = GoogleAdsClient.load_from_storage(args.config)

    # Get customer ID
    customer_id = args.customer_id.replace('-', '') if args.customer_id else None
    account_name = args.account_name or "Unknown"

    if not customer_id:
        print(f"Resolving customer ID for: {args.account_name}")
        resolved = resolve_account_name(args.account_name, args.accounts, ads_client, args.config)

        if not resolved:
            print(f"Error: Could not find customer ID for '{args.account_name}'")
            print("Provide the customer ID directly with --cid")
            sys.exit(1)

        customer_id, account_name = resolved
        print(f"Found customer ID: {customer_id} ({account_name})")
        print()

    # Run investigation
    run_investigation(customer_id, account_name, ads_client, monthly_budget=args.monthly_budget)


if __name__ == "__main__":
    main()
