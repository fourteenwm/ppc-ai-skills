#!/usr/bin/env python3
"""42-Point Google Ads Account Diagnostic

Like a mechanic's multi-point inspection, but for Google Ads accounts.
42 checks on a standard run, each GREEN/YELLOW/RED. One overall verdict.

The 42 = the original 40 core checks + checks 43-44 (PMAX video
enhancements + Demand Gen ad-level asset automation, all verticals). The
local-service preset adds checks 41-42 (call/location extensions) for a
44-check run.

Output: console report + CSV (always); optionally writes a color-coded
'Inspection' tab into an existing Google Sheet with --sheet-id.

Usage:
    python run_diagnostic.py --cid 1234567890
    python run_diagnostic.py --cid 1234567890 --name "Example Account"
    python run_diagnostic.py --cid 1234567890 --vertical local-service
    python run_diagnostic.py --cid 1234567890 --days 60 --pacing-threshold 5
    python run_diagnostic.py --cid 1234567890 --sheet-id YOUR_SHEET_ID

Requires:
    - google-ads.yaml in the skill folder (one level above scripts/) —
      see the google-ads-api-setup skill in this repo
    - pip install google-ads pyyaml
    - optional, for --sheet-id: pip install gspread google-auth
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import argparse
import calendar as cal_mod
import csv
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

try:
    from google.ads.googleads.client import GoogleAdsClient
except ImportError:
    print("Missing dependency: google-ads. Run: pip install google-ads")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent                      # the skill folder
CREDENTIALS_PATH = ROOT_DIR / 'google-ads.yaml'   # Google Ads API credentials
OUTPUT_DIR = ROOT_DIR / 'data'                    # CSV reports land here

# ── Vertical calibration ──────────────────────────────────────────
# The check engine is vertical-agnostic; thresholds come from a named preset
# so the same checks score correctly on lead-gen portfolios (property
# management and similar) vs. small phone-driven local-service accounts
# (auto repair, home services, etc.). Pick with --vertical.

VERTICAL_PRESETS = {
    'property-management': {
        'pacing_threshold': 8,
        'seasonal_severity': 'RED',          # check 21
        'geo_exclusion_severity': 'RED',     # check 29 (zero exclusions)
        'neg_green_bar': 20,                 # check 35 GREEN when avg >=
        'neg_yellow_bar': 10,                # check 35 YELLOW when avg >=
        'st_high_spend_floor': 100,          # check 13 ($ per zero-conv term)
        'kw_high_spend_floor': 200,          # check 15 ($ per zero-conv keyword)
        'check_call_location_ext': False,    # checks 41-42 (local-service only)
    },
    'local-service': {
        'pacing_threshold': 10,              # typical local-service tolerance is +/-10%
        'seasonal_severity': 'YELLOW',       # local services run intentional seasonal copy
        'geo_exclusion_severity': 'YELLOW',  # radius-targeted businesses legitimately have none
        'neg_green_bar': 10,
        'neg_yellow_bar': 5,
        'st_high_spend_floor': 50,
        'kw_high_spend_floor': 100,
        'check_call_location_ext': True,
    },
}

# ── Data Classes ──────────────────────────────────────────────────

@dataclass
class CheckResult:
    number: int
    category: str
    name: str
    status: str          # GREEN, YELLOW, RED, N/A
    finding: str
    dollar_impact: float = 0.0
    action: str = ''
    auto_red: bool = False

@dataclass
class InspectionReport:
    account_name: str
    cid: str
    checks: list = field(default_factory=list)
    overall: str = ''
    green: int = 0
    yellow: int = 0
    red: int = 0
    na: int = 0
    auto_red_trigger: str = ''
    est_waste: float = 0.0
    run_date: str = ''

# ── API Helpers ───────────────────────────────────────────────────

def get_client():
    if not CREDENTIALS_PATH.exists():
        raise SystemExit(
            f"ERROR: google-ads.yaml not found at {CREDENTIALS_PATH}\n"
            "  Set up Google Ads API credentials first — see the\n"
            "  google-ads-api-setup skill in this repo."
        )
    return GoogleAdsClient.load_from_storage(str(CREDENTIALS_PATH))

def gaql(client, cid, query):
    """Run GAQL query, return list of result rows (raw protobuf)."""
    svc = client.get_service('GoogleAdsService')
    try:
        return list(svc.search(customer_id=cid, query=query))
    except Exception as e:
        print(f"  GAQL error: {e}")
        return []

def date_range(days):
    end = datetime.now() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def micros(val):
    return val / 1_000_000 if val else 0

# ── Data Fetching ─────────────────────────────────────────────────

def fetch_all_data(client, cid, days, cfg):
    """Run all GAQL queries and return raw data dict."""
    d = {}
    ds, de = date_range(days)
    ds90, _ = date_range(90)
    now = datetime.now()

    print("  Fetching conversion actions...")
    d['conv_actions'] = gaql(client, cid,
        "SELECT conversion_action.id, conversion_action.name, "
        "conversion_action.type, conversion_action.status, "
        "conversion_action.category, "
        "conversion_action.include_in_conversions_metric "
        "FROM conversion_action "
        "WHERE conversion_action.status != 'REMOVED'")

    print("  Fetching conversion dates...")
    # NOTE: intentionally NOT filtered to campaign.status='ENABLED'. Feeds
    # check #2 (conversion-tag recency) = account-level tag health. PM accounts
    # cycle campaigns (end dates / monthly rebuilds), so an enabled-only filter
    # would falsely flag an action as stale when its source campaign was just
    # paused. Keep account-wide. (All entity-level fetches ARE enabled-scoped.)
    d['conv_dates'] = gaql(client, cid,
        f"SELECT segments.conversion_action_name, segments.date, "
        f"metrics.conversions "
        f"FROM campaign "
        f"WHERE segments.date BETWEEN '{ds90}' AND '{de}' "
        f"AND metrics.conversions > 0")

    print("  Fetching campaigns...")
    d['campaigns'] = gaql(client, cid,
        "SELECT campaign.id, campaign.name, campaign.status, "
        "campaign.advertising_channel_type, "
        "campaign_budget.amount_micros, "
        "campaign.geo_target_type_setting.positive_geo_target_type, "
        "campaign.network_settings.target_search_network, "
        "campaign.network_settings.target_content_network, "
        "campaign.network_settings.target_partner_search_network "
        "FROM campaign WHERE campaign.status = 'ENABLED'")

    print("  Fetching campaign metrics (MTD)...")
    mtd_start = now.replace(day=1).strftime('%Y-%m-%d')
    mtd_end = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    if mtd_start <= mtd_end:
        d['campaign_mtd'] = gaql(client, cid,
            f"SELECT campaign.id, campaign.name, metrics.cost_micros, "
            f"metrics.conversions, metrics.conversions_value "
            f"FROM campaign WHERE campaign.status = 'ENABLED' "
            f"AND segments.date BETWEEN '{mtd_start}' AND '{mtd_end}'")
    else:
        d['campaign_mtd'] = []

    print("  Fetching account metrics...")
    d['account_metrics'] = gaql(client, cid,
        f"SELECT metrics.cost_micros, metrics.conversions, "
        f"metrics.conversions_value, metrics.clicks, metrics.impressions "
        f"FROM customer WHERE segments.date BETWEEN '{ds}' AND '{de}'")

    print("  Fetching impression share...")
    d['impression_share'] = gaql(client, cid,
        f"SELECT campaign.id, campaign.name, "
        f"campaign.advertising_channel_type, "
        f"metrics.search_impression_share, "
        f"metrics.search_budget_lost_impression_share, "
        f"metrics.search_rank_lost_impression_share, "
        f"metrics.cost_micros "
        f"FROM campaign "
        f"WHERE campaign.status = 'ENABLED' "
        f"AND campaign.advertising_channel_type = 'SEARCH' "
        f"AND segments.date BETWEEN '{ds}' AND '{de}'")

    print("  Fetching keywords...")
    d['keywords'] = gaql(client, cid,
        f"SELECT ad_group_criterion.keyword.text, "
        f"ad_group_criterion.keyword.match_type, "
        f"ad_group_criterion.quality_info.quality_score, "
        f"metrics.impressions, metrics.cost_micros, metrics.conversions "
        f"FROM keyword_view "
        f"WHERE campaign.status = 'ENABLED' "
        f"AND ad_group.status = 'ENABLED' "
        f"AND ad_group_criterion.status = 'ENABLED' "
        f"AND segments.date BETWEEN '{ds}' AND '{de}'")

    print("  Fetching search terms...")
    d['search_terms'] = gaql(client, cid,
        f"SELECT search_term_view.search_term, "
        f"metrics.cost_micros, metrics.conversions, metrics.clicks "
        f"FROM search_term_view "
        f"WHERE segments.date BETWEEN '{ds}' AND '{de}' "
        f"AND campaign.status = 'ENABLED' "
        f"AND ad_group.status = 'ENABLED'")

    print("  Fetching ads...")
    d['ads'] = gaql(client, cid,
        "SELECT ad_group_ad.ad.id, ad_group_ad.ad.type, "
        "ad_group_ad.ad.final_urls, "
        "ad_group_ad.policy_summary.approval_status, "
        "ad_group_ad.status, "
        "ad_group_ad.ad.responsive_search_ad.headlines, "
        "ad_group_ad.ad.responsive_search_ad.descriptions, "
        "campaign.name, campaign.status, "
        "ad_group.status "
        "FROM ad_group_ad "
        "WHERE campaign.status = 'ENABLED' "
        "AND ad_group.status = 'ENABLED' "
        "AND ad_group_ad.status = 'ENABLED'")

    print("  Fetching asset performance...")
    d['assets'] = gaql(client, cid,
        f"SELECT asset.type, "
        f"ad_group_ad_asset_view.performance_label, "
        f"ad_group_ad_asset_view.field_type "
        f"FROM ad_group_ad_asset_view "
        f"WHERE campaign.status = 'ENABLED' "
        f"AND ad_group.status = 'ENABLED' "
        f"AND ad_group_ad.status = 'ENABLED' "
        f"AND segments.date BETWEEN '{ds}' AND '{de}'")

    print("  Fetching negative keywords...")
    d['negatives'] = gaql(client, cid,
        "SELECT campaign_criterion.keyword.text, "
        "campaign_criterion.keyword.match_type, "
        "campaign.id, campaign.name "
        "FROM campaign_criterion "
        "WHERE campaign_criterion.type = 'KEYWORD' "
        "AND campaign_criterion.negative = TRUE "
        "AND campaign.status = 'ENABLED'")

    print("  Fetching PMAX asset groups...")
    d['pmax_asset_groups'] = gaql(client, cid,
        "SELECT asset_group.id, asset_group.name, "
        "asset_group.status, campaign.id, campaign.name "
        "FROM asset_group "
        "WHERE campaign.status = 'ENABLED' "
        "AND campaign.advertising_channel_type = 'PERFORMANCE_MAX' "
        "AND asset_group.status = 'ENABLED'")

    print("  Fetching extensions...")
    d['extensions'] = gaql(client, cid,
        "SELECT asset.type, customer_asset.status "
        "FROM customer_asset "
        "WHERE customer_asset.status = 'ENABLED'")

    print("  Fetching placements...")
    d['placements'] = gaql(client, cid,
        f"SELECT detail_placement_view.placement, "
        f"detail_placement_view.placement_type, "
        f"metrics.cost_micros, metrics.impressions "
        f"FROM detail_placement_view "
        f"WHERE segments.date BETWEEN '{ds}' AND '{de}' "
        f"AND campaign.status = 'ENABLED' "
        f"AND ad_group.status = 'ENABLED'")

    print("  Fetching asset automation settings...")
    d['asset_automation'] = gaql(client, cid,
        "SELECT campaign.id, campaign.name, "
        "campaign.advertising_channel_type, "
        "campaign.asset_automation_settings "
        "FROM campaign WHERE campaign.status = 'ENABLED'")

    # PMAX URL expansion is checked via asset_automation_settings
    # (FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION), no separate query needed

    print("  Fetching DGen ad automation settings...")
    # DGen asset automation lives at the AD level
    # (ad_group_ad.ad_group_ad_asset_automation_settings), unlike PMax where
    # it's campaign-level — a campaign-scoped scan can't see it. Ended-but-
    # ENABLED campaigns are dropped (not actionable); API v23 renamed
    # campaign.end_date -> campaign.end_date_time, so filter client-side
    # rather than in GAQL. Feeds check 44.
    today = now.strftime('%Y-%m-%d')
    dgen_rows = gaql(client, cid,
        "SELECT ad_group_ad.ad.id, ad_group_ad.ad.type, "
        "ad_group_ad.ad_group_ad_asset_automation_settings, "
        "campaign.name, campaign.end_date_time "
        "FROM ad_group_ad "
        "WHERE campaign.advertising_channel_type = 'DEMAND_GEN' "
        "AND campaign.status = 'ENABLED' "
        "AND ad_group.status = 'ENABLED' "
        "AND ad_group_ad.status = 'ENABLED'")
    d['dgen_ads'] = [r for r in dgen_rows
                     if not r.campaign.end_date_time
                     or str(r.campaign.end_date_time)[:10] >= today]

    print("  Fetching recommendation subscriptions...")
    d['rec_subscriptions'] = gaql(client, cid,
        "SELECT recommendation_subscription.type, "
        "recommendation_subscription.status "
        "FROM recommendation_subscription")

    print("  Fetching brand safety suitability...")
    d['brand_safety'] = gaql(client, cid,
        "SELECT customer.video_brand_safety_suitability "
        "FROM customer")

    print("  Fetching geo exclusions...")
    d['geo_exclusions'] = gaql(client, cid,
        "SELECT campaign.id, campaign.name, "
        "campaign_criterion.location.geo_target_constant "
        "FROM campaign_criterion "
        "WHERE campaign_criterion.negative = TRUE "
        "AND campaign.status = 'ENABLED'")

    # Call/location extension links — only fetched for local-service checks 41-42.
    # field_type captures the EXTENSION role of the asset link (CALL, LOCATION),
    # which is more reliable than asset.type for "is this extension serving",
    # and catches campaign-level links the customer_asset query (39-40) misses.
    if cfg.get('check_call_location_ext'):
        print("  Fetching call/location extension links...")
        d['campaign_asset_fieldtypes'] = gaql(client, cid,
            "SELECT campaign_asset.field_type, campaign_asset.status, "
            "campaign.status "  # required in SELECT when filtered in WHERE
            "FROM campaign_asset "
            "WHERE campaign_asset.status = 'ENABLED' "
            "AND campaign.status = 'ENABLED'")
        d['customer_asset_fieldtypes'] = gaql(client, cid,
            "SELECT customer_asset.field_type, customer_asset.status "
            "FROM customer_asset "
            "WHERE customer_asset.status = 'ENABLED'")

    return d

# ── Check Functions ───────────────────────────────────────────────
# Each returns a list of CheckResult objects.

IGNORED_CONV_TYPES = {
    'STORE_VISITS', 'GOOGLE_HOSTED', 'ANDROID_INSTALLS_ALL_OTHER_APPS',
    'ANDROID_IN_APP_ACTION', 'IOS_IN_APP_ACTION', 'IOS_FIRST_OPEN',
}

def checks_conversion(data, cfg):
    results = []
    # Parse conversion actions
    actions = []
    for r in data.get('conv_actions', []):
        ca = r.conversion_action
        ctype = ca.type_.name
        if ctype in IGNORED_CONV_TYPES:
            continue
        primary = ca.include_in_conversions_metric
        actions.append({
            'name': ca.name, 'type': ctype,
            'primary': primary, 'id': ca.id
        })

    primary_actions = [a for a in actions if a['primary']]

    # Check 1: Primary conversion actions exist
    if len(primary_actions) >= 1:
        results.append(CheckResult(1, 'Conversion Tracking',
            'Primary conversion actions exist', 'GREEN',
            f"{len(primary_actions)} primary action(s) configured"))
    elif len(actions) >= 1:
        results.append(CheckResult(1, 'Conversion Tracking',
            'Primary conversion actions exist', 'YELLOW',
            f"{len(actions)} actions exist but none set as primary",
            action='Set at least one conversion as primary'))
    else:
        results.append(CheckResult(1, 'Conversion Tracking',
            'Primary conversion actions exist', 'RED',
            'No conversion actions found', auto_red=True,
            action='Set up conversion tracking immediately'))

    # Parse last conversion dates
    last_dates = {}
    for r in data.get('conv_dates', []):
        name = r.segments.conversion_action_name
        d = r.segments.date
        if name not in last_dates or d > last_dates[name]:
            last_dates[name] = d

    # Check 2: Primary actions firing recently
    if primary_actions:
        now = datetime.now()
        stale = []
        warning = []
        healthy = []
        for a in primary_actions:
            ld = last_dates.get(a['name'])
            if ld:
                days_since = (now - datetime.strptime(ld, '%Y-%m-%d')).days
                if days_since > 30:
                    stale.append((a['name'], days_since))
                elif days_since > 14:
                    warning.append((a['name'], days_since))
                else:
                    healthy.append(a['name'])
            else:
                stale.append((a['name'], 90))

        if stale:
            worst = max(stale, key=lambda x: x[1])
            results.append(CheckResult(2, 'Conversion Tracking',
                'Primary actions firing recently', 'RED',
                f"{worst[0]}: {worst[1]}d since last conversion",
                action='Verify conversion tag is firing on website'))
        elif warning:
            worst = max(warning, key=lambda x: x[1])
            results.append(CheckResult(2, 'Conversion Tracking',
                'Primary actions firing recently', 'YELLOW',
                f"{worst[0]}: {worst[1]}d since last conversion",
                action='Monitor — approaching stale threshold'))
        else:
            results.append(CheckResult(2, 'Conversion Tracking',
                'Primary actions firing recently', 'GREEN',
                f"All {len(healthy)} primary actions fired within 14 days"))
    else:
        results.append(CheckResult(2, 'Conversion Tracking',
            'Primary actions firing recently', 'N/A',
            'No primary actions to evaluate'))

    # Check 3: No orphaned/duplicate conversion actions
    names = [a['name'] for a in actions]
    dupes = [n for n in set(names) if names.count(n) > 1]
    non_primary_count = len(actions) - len(primary_actions)
    if not dupes and non_primary_count <= len(primary_actions) + 2:
        results.append(CheckResult(3, 'Conversion Tracking',
            'No orphaned/duplicate actions', 'GREEN',
            f"{len(actions)} total actions, all distinct"))
    elif dupes:
        results.append(CheckResult(3, 'Conversion Tracking',
            'No orphaned/duplicate actions', 'YELLOW',
            f"Potential duplicates: {', '.join(dupes[:3])}",
            action='Review and consolidate duplicate conversion actions'))
    else:
        results.append(CheckResult(3, 'Conversion Tracking',
            'No orphaned/duplicate actions', 'GREEN',
            f"{len(actions)} total actions"))

    return results


def checks_pacing(data, cfg):
    results = []
    now = datetime.now()
    day = now.day
    dim = cal_mod.monthrange(now.year, now.month)[1]
    pct_through = day / dim

    # Calculate MTD spend and daily budgets
    mtd_spend = sum(micros(r.metrics.cost_micros) for r in data.get('campaign_mtd', []))
    daily_budgets = {}
    for r in data.get('campaigns', []):
        cid = r.campaign.id
        budget = micros(r.campaign_budget.amount_micros) if r.campaign_budget.amount_micros else 0
        daily_budgets[cid] = budget
    total_daily_budget = sum(daily_budgets.values())
    monthly_budget = total_daily_budget * dim

    # Check 4: Account is spending
    last7_spend = mtd_spend  # approximate
    if total_daily_budget > 0 and mtd_spend > 0:
        results.append(CheckResult(4, 'Budget & Pacing',
            'Account is spending', 'GREEN',
            f"${mtd_spend:,.0f} MTD spend, ${total_daily_budget:,.0f}/day budget"))
    elif total_daily_budget > 0 and mtd_spend == 0:
        results.append(CheckResult(4, 'Budget & Pacing',
            'Account is spending', 'RED',
            f"$0 spend with ${total_daily_budget:,.0f}/day budget",
            dollar_impact=total_daily_budget * 30, auto_red=True,
            action='Investigate why account is not spending'))
    else:
        results.append(CheckResult(4, 'Budget & Pacing',
            'Account is spending', 'N/A',
            'No budget data available'))

    # Check 5: MTD pacing within tolerance
    thresh = cfg.get('pacing_threshold', 8)
    if monthly_budget > 0 and day > 1:
        expected = monthly_budget * pct_through
        variance_pct = ((expected - mtd_spend) / expected) * 100 if expected > 0 else 0
        abs_var = abs(variance_pct)
        direction = 'underspent' if variance_pct > 0 else 'overspent'

        if abs_var <= thresh:
            results.append(CheckResult(5, 'Budget & Pacing',
                'MTD pacing within tolerance', 'GREEN',
                f"{variance_pct:+.1f}% {direction} (threshold: +/-{thresh}%)"))
        elif abs_var <= 15:
            gap = (abs_var / 100) * monthly_budget
            results.append(CheckResult(5, 'Budget & Pacing',
                'MTD pacing within tolerance', 'YELLOW',
                f"{variance_pct:+.1f}% {direction} (threshold: +/-{thresh}%)",
                dollar_impact=gap,
                action=f'Review daily budgets — ${gap:,.0f}/mo gap'))
        else:
            gap = (abs_var / 100) * monthly_budget
            results.append(CheckResult(5, 'Budget & Pacing',
                'MTD pacing within tolerance', 'RED',
                f"{variance_pct:+.1f}% {direction} (threshold: +/-{thresh}%)",
                dollar_impact=gap,
                action=f'Immediate action needed — ${gap:,.0f}/mo gap'))
    else:
        results.append(CheckResult(5, 'Budget & Pacing',
            'MTD pacing within tolerance', 'N/A',
            'Insufficient data (day 1 or no budget)'))

    # Check 6: Projected EOM spend
    if monthly_budget > 0 and day > 1 and mtd_spend > 0:
        daily_avg = mtd_spend / (day - 1) if day > 1 else mtd_spend
        projected = daily_avg * dim
        proj_pct = (projected / monthly_budget) * 100

        if 90 <= proj_pct <= 110:
            results.append(CheckResult(6, 'Budget & Pacing',
                'Projected EOM spend on target', 'GREEN',
                f"Projected ${projected:,.0f} of ${monthly_budget:,.0f} ({proj_pct:.0f}%)"))
        elif 80 <= proj_pct < 90 or 110 < proj_pct <= 120:
            gap = abs(projected - monthly_budget)
            results.append(CheckResult(6, 'Budget & Pacing',
                'Projected EOM spend on target', 'YELLOW',
                f"Projected ${projected:,.0f} of ${monthly_budget:,.0f} ({proj_pct:.0f}%)",
                dollar_impact=gap,
                action='Adjust daily budgets to align with monthly target'))
        else:
            gap = abs(projected - monthly_budget)
            results.append(CheckResult(6, 'Budget & Pacing',
                'Projected EOM spend on target', 'RED',
                f"Projected ${projected:,.0f} of ${monthly_budget:,.0f} ({proj_pct:.0f}%)",
                dollar_impact=gap,
                action='Significant budget misalignment — investigate delivery'))
    else:
        results.append(CheckResult(6, 'Budget & Pacing',
            'Projected EOM spend on target', 'N/A',
            'Insufficient data for projection'))

    return results


def checks_impression_share(data, cfg):
    results = []
    rows = data.get('impression_share', [])
    if not rows:
        return [
            CheckResult(7, 'Impression Share', 'Search IS adequate', 'N/A', 'No Search campaigns'),
            CheckResult(8, 'Impression Share', 'Budget Lost IS controlled', 'N/A', 'No Search campaigns'),
            CheckResult(9, 'Impression Share', 'Rank Lost IS manageable', 'N/A', 'No Search campaigns'),
        ]

    # Aggregate weighted by spend
    total_cost = 0
    w_is = 0; w_blis = 0; w_rlis = 0
    for r in rows:
        cost = micros(r.metrics.cost_micros)
        sis = r.metrics.search_impression_share or 0
        blis = r.metrics.search_budget_lost_impression_share or 0
        rlis = r.metrics.search_rank_lost_impression_share or 0
        total_cost += cost
        w_is += sis * cost
        w_blis += blis * cost
        w_rlis += rlis * cost

    if total_cost > 0:
        avg_is = (w_is / total_cost) * 100
        avg_blis = (w_blis / total_cost) * 100
        avg_rlis = (w_rlis / total_cost) * 100
    else:
        avg_is = avg_blis = avg_rlis = 0

    # Check 7: Search IS
    if avg_is > 60:
        results.append(CheckResult(7, 'Impression Share',
            'Search IS adequate', 'GREEN', f"{avg_is:.0f}% Search IS"))
    elif avg_is > 30:
        results.append(CheckResult(7, 'Impression Share',
            'Search IS adequate', 'YELLOW', f"{avg_is:.0f}% Search IS",
            action='Review bid strategy and budget allocation'))
    else:
        results.append(CheckResult(7, 'Impression Share',
            'Search IS adequate', 'RED', f"{avg_is:.0f}% Search IS",
            action='Significant impression loss — investigate root cause'))

    # Check 8: Budget Lost IS
    if avg_blis < 10:
        results.append(CheckResult(8, 'Impression Share',
            'Budget Lost IS controlled', 'GREEN', f"{avg_blis:.0f}% Budget Lost IS"))
    elif avg_blis < 25:
        opp = total_cost * (avg_blis / 100)
        results.append(CheckResult(8, 'Impression Share',
            'Budget Lost IS controlled', 'YELLOW',
            f"{avg_blis:.0f}% Budget Lost IS",
            dollar_impact=opp,
            action=f'~${opp:,.0f}/mo opportunity lost to budget caps'))
    else:
        opp = total_cost * (avg_blis / 100)
        results.append(CheckResult(8, 'Impression Share',
            'Budget Lost IS controlled', 'RED',
            f"{avg_blis:.0f}% Budget Lost IS",
            dollar_impact=opp,
            action=f'${opp:,.0f}/mo lost — budget severely constraining delivery'))

    # Check 9: Rank Lost IS
    if avg_rlis < 40:
        results.append(CheckResult(9, 'Impression Share',
            'Rank Lost IS manageable', 'GREEN', f"{avg_rlis:.0f}% Rank Lost IS"))
    elif avg_rlis < 60:
        results.append(CheckResult(9, 'Impression Share',
            'Rank Lost IS manageable', 'YELLOW', f"{avg_rlis:.0f}% Rank Lost IS",
            action='Review ad relevance, landing pages, and bid strategy'))
    else:
        results.append(CheckResult(9, 'Impression Share',
            'Rank Lost IS manageable', 'RED', f"{avg_rlis:.0f}% Rank Lost IS",
            action='Quality issues significantly limiting visibility'))

    return results


def checks_quality_score(data, cfg):
    results = []
    kws = data.get('keywords', [])
    qs_list = []
    for r in kws:
        qs = r.ad_group_criterion.quality_info.quality_score
        if qs and qs > 0:
            qs_list.append(qs)

    if not qs_list:
        return [
            CheckResult(10, 'Quality Score', 'Average QS healthy', 'N/A', 'No QS data available'),
            CheckResult(11, 'Quality Score', 'Low-QS concentration acceptable', 'N/A', 'No QS data'),
        ]

    avg_qs = sum(qs_list) / len(qs_list)
    below5 = sum(1 for q in qs_list if q < 5)
    below5_pct = (below5 / len(qs_list)) * 100

    # Check 10: Average QS
    if avg_qs >= 6:
        results.append(CheckResult(10, 'Quality Score',
            'Average QS healthy', 'GREEN', f"Avg QS: {avg_qs:.1f} ({len(qs_list)} keywords)"))
    elif avg_qs >= 4:
        results.append(CheckResult(10, 'Quality Score',
            'Average QS healthy', 'YELLOW', f"Avg QS: {avg_qs:.1f} ({len(qs_list)} keywords)",
            action='Review ad relevance and landing page experience'))
    else:
        results.append(CheckResult(10, 'Quality Score',
            'Average QS healthy', 'RED', f"Avg QS: {avg_qs:.1f} ({len(qs_list)} keywords)",
            action='Significant quality issues — review ads and landing pages'))

    # Check 11: Low-QS concentration
    if below5_pct < 15:
        results.append(CheckResult(11, 'Quality Score',
            'Low-QS concentration acceptable', 'GREEN',
            f"{below5_pct:.0f}% of keywords below QS 5 ({below5}/{len(qs_list)})"))
    elif below5_pct < 30:
        results.append(CheckResult(11, 'Quality Score',
            'Low-QS concentration acceptable', 'YELLOW',
            f"{below5_pct:.0f}% of keywords below QS 5 ({below5}/{len(qs_list)})",
            action='Review and improve low-QS keywords'))
    else:
        results.append(CheckResult(11, 'Quality Score',
            'Low-QS concentration acceptable', 'RED',
            f"{below5_pct:.0f}% of keywords below QS 5 ({below5}/{len(qs_list)})",
            action='Systemic quality issues — major keyword/ad/LP overhaul needed'))

    return results


def checks_search_terms(data, cfg):
    results = []
    terms = data.get('search_terms', [])
    if not terms:
        return [
            CheckResult(12, 'Search Terms', 'Zero-conv search term waste controlled', 'N/A', 'No search term data'),
            CheckResult(13, 'Search Terms', 'No high-spend zero-conv terms', 'N/A', 'No search term data'),
        ]

    st_floor = cfg.get('st_high_spend_floor', 100)
    total_spend = 0
    zero_conv_spend = 0
    high_spend_zero = []

    for r in terms:
        cost = micros(r.metrics.cost_micros)
        convs = r.metrics.conversions
        total_spend += cost
        if convs == 0 and cost > 0:
            zero_conv_spend += cost
            if cost >= st_floor:
                high_spend_zero.append((r.search_term_view.search_term, cost))

    waste_pct = (zero_conv_spend / total_spend * 100) if total_spend > 0 else 0

    # Check 12: Waste percentage
    if waste_pct < 5:
        results.append(CheckResult(12, 'Search Terms',
            'Zero-conv search term waste controlled', 'GREEN',
            f"{waste_pct:.1f}% waste (${zero_conv_spend:,.0f} of ${total_spend:,.0f})"))
    elif waste_pct < 15:
        results.append(CheckResult(12, 'Search Terms',
            'Zero-conv search term waste controlled', 'YELLOW',
            f"{waste_pct:.1f}% waste (${zero_conv_spend:,.0f} of ${total_spend:,.0f})",
            dollar_impact=zero_conv_spend,
            action='Add negative keywords for top zero-conversion terms'))
    else:
        results.append(CheckResult(12, 'Search Terms',
            'Zero-conv search term waste controlled', 'RED',
            f"{waste_pct:.1f}% waste (${zero_conv_spend:,.0f} of ${total_spend:,.0f})",
            dollar_impact=zero_conv_spend,
            action='Critical waste — immediate negative keyword review needed'))

    # Check 13: High-spend zero-conv terms
    high_spend_zero.sort(key=lambda x: -x[1])
    if not high_spend_zero:
        results.append(CheckResult(13, 'Search Terms',
            'No high-spend zero-conv terms', 'GREEN',
            f'No search terms with >${st_floor:,.0f} spend and 0 conversions'))
    elif len(high_spend_zero) <= 2:
        top = high_spend_zero[0]
        results.append(CheckResult(13, 'Search Terms',
            'No high-spend zero-conv terms', 'YELLOW',
            f"{len(high_spend_zero)} terms >${st_floor:,.0f}: \"{top[0]}\" (${top[1]:,.0f})",
            dollar_impact=sum(x[1] for x in high_spend_zero),
            action='Add as negatives or review match types'))
    else:
        total_wasted = sum(x[1] for x in high_spend_zero)
        results.append(CheckResult(13, 'Search Terms',
            'No high-spend zero-conv terms', 'RED',
            f"{len(high_spend_zero)} terms >${st_floor:,.0f} spend, 0 conv (${total_wasted:,.0f} total)",
            dollar_impact=total_wasted,
            action='Urgent — add negatives for top wasting terms'))

    return results


def checks_keywords(data, cfg):
    results = []
    kw_floor = cfg.get('kw_high_spend_floor', 200)
    kws = data.get('keywords', [])
    has_search = any(
        r.campaign.advertising_channel_type.name == 'SEARCH'
        for r in data.get('campaigns', [])
    )
    if not kws or not has_search:
        return [
            CheckResult(14, 'Keyword Health', 'Keywords are serving', 'N/A', 'No Search campaigns'),
            CheckResult(15, 'Keyword Health', 'No high-spend zero-conv keywords', 'N/A', 'No Search campaigns'),
            CheckResult(16, 'Keyword Health', 'Match type distribution intentional', 'N/A', 'No Search campaigns'),
        ]

    total_kw = len(kws)
    serving = sum(1 for r in kws if r.metrics.impressions > 0)
    serving_pct = (serving / total_kw * 100) if total_kw > 0 else 0

    # Check 14: Keywords serving
    if serving_pct > 90:
        results.append(CheckResult(14, 'Keyword Health',
            'Keywords are serving', 'GREEN',
            f"{serving_pct:.0f}% serving ({serving}/{total_kw})"))
    elif serving_pct > 75:
        results.append(CheckResult(14, 'Keyword Health',
            'Keywords are serving', 'YELLOW',
            f"{serving_pct:.0f}% serving ({serving}/{total_kw})",
            action='Review non-serving keywords — pause or adjust'))
    else:
        results.append(CheckResult(14, 'Keyword Health',
            'Keywords are serving', 'RED',
            f"{serving_pct:.0f}% serving ({serving}/{total_kw})",
            action='Majority of keywords not serving — review targeting'))

    # Check 15: High-spend zero-conv keywords
    high_spend = []
    for r in kws:
        cost = micros(r.metrics.cost_micros)
        if cost >= kw_floor and r.metrics.conversions == 0:
            high_spend.append((r.ad_group_criterion.keyword.text, cost))

    if not high_spend:
        results.append(CheckResult(15, 'Keyword Health',
            'No high-spend zero-conv keywords', 'GREEN',
            f'No keywords with >${kw_floor:,.0f} spend and 0 conversions'))
    elif len(high_spend) <= 2:
        top = max(high_spend, key=lambda x: x[1])
        results.append(CheckResult(15, 'Keyword Health',
            'No high-spend zero-conv keywords', 'YELLOW',
            f"{len(high_spend)} keywords >${kw_floor:,.0f}, 0 conv: \"{top[0]}\" (${top[1]:,.0f})",
            dollar_impact=sum(x[1] for x in high_spend),
            action='Review bid strategy or pause'))
    else:
        total = sum(x[1] for x in high_spend)
        results.append(CheckResult(15, 'Keyword Health',
            'No high-spend zero-conv keywords', 'RED',
            f"{len(high_spend)} keywords >${kw_floor:,.0f}, 0 conv (${total:,.0f} total)",
            dollar_impact=total,
            action='Significant keyword waste — review and restructure'))

    # Check 16: Match type distribution
    match_types = defaultdict(int)
    for r in kws:
        mt = r.ad_group_criterion.keyword.match_type.name
        match_types[mt] += 1

    broad = match_types.get('BROAD', 0)
    total_mt = sum(match_types.values())
    broad_pct = (broad / total_mt * 100) if total_mt > 0 else 0
    neg_count = len(data.get('negatives', []))
    dist_str = ', '.join(f"{k}: {v}" for k, v in sorted(match_types.items()))

    if broad_pct < 50 or (broad_pct >= 50 and neg_count >= 10):
        results.append(CheckResult(16, 'Keyword Health',
            'Match type distribution intentional', 'GREEN',
            f"{dist_str}"))
    elif broad_pct < 80:
        results.append(CheckResult(16, 'Keyword Health',
            'Match type distribution intentional', 'YELLOW',
            f"{broad_pct:.0f}% broad match ({dist_str})",
            action='Consider adding more exact/phrase or adding negatives'))
    else:
        results.append(CheckResult(16, 'Keyword Health',
            'Match type distribution intentional', 'RED',
            f"{broad_pct:.0f}% broad match with only {neg_count} negatives",
            action='All broad match with minimal negatives — high waste risk'))

    return results


def checks_creative(data, cfg):
    results = []
    ads = data.get('ads', [])
    enabled_ads = [r for r in ads if r.ad_group_ad.status.name == 'ENABLED']

    if not enabled_ads:
        return [CheckResult(n, 'Creative & Ads', f'Check {n}', 'N/A', 'No enabled ads')
                for n in range(17, 23)]

    # Check 17: Disapprovals
    disapproved = [r for r in enabled_ads
                   if r.ad_group_ad.policy_summary.approval_status.name == 'DISAPPROVED']
    total_ads = len(enabled_ads)
    dis_count = len(disapproved)

    if dis_count == 0:
        results.append(CheckResult(17, 'Creative & Ads',
            'No disapproved ads', 'GREEN',
            f"0 disapproved out of {total_ads} enabled ads"))
    elif dis_count <= 2:
        results.append(CheckResult(17, 'Creative & Ads',
            'No disapproved ads', 'YELLOW',
            f"{dis_count} disapproved out of {total_ads} enabled ads",
            action='Review and fix disapproved ads'))
    else:
        auto = dis_count > total_ads * 0.75
        results.append(CheckResult(17, 'Creative & Ads',
            'No disapproved ads', 'RED',
            f"{dis_count} disapproved out of {total_ads} enabled ads",
            auto_red=auto,
            action='Multiple ad disapprovals — review policy compliance'))

    # Check 18: DKI detection
    has_dki = False
    for r in enabled_ads:
        ad = r.ad_group_ad.ad
        if hasattr(ad, 'responsive_search_ad') and ad.responsive_search_ad:
            rsa = ad.responsive_search_ad
            for h in rsa.headlines:
                if '{keyword' in h.text.lower() or '{KeyWord' in h.text:
                    has_dki = True; break
            if not has_dki:
                for d in rsa.descriptions:
                    if '{keyword' in d.text.lower() or '{KeyWord' in d.text:
                        has_dki = True; break
        if has_dki:
            break

    if not has_dki:
        results.append(CheckResult(18, 'Creative & Ads',
            'No DKI in use', 'GREEN', 'No Dynamic Keyword Insertion found'))
    else:
        results.append(CheckResult(18, 'Creative & Ads',
            'No DKI in use', 'RED',
            'DKI detected in ad copy — trademark risk',
            action='Remove {KeyWord} insertion from ads'))

    # Check 19: Auto-created assets — query asset_automation_settings
    auto_asset_campaigns = []
    for r in data.get('asset_automation', []):
        camp = r.campaign
        # Check for TEXT_ASSET_AUTOMATION on non-PMAX campaigns (PMAX checked separately in 30-32)
        if camp.advertising_channel_type.name == 'PERFORMANCE_MAX':
            continue
        # Default is OPTED_IN if not explicitly set
        has_opted_in = True  # assume default
        for setting in camp.asset_automation_settings:
            if setting.asset_automation_type.name == 'TEXT_ASSET_AUTOMATION':
                if setting.asset_automation_status.name == 'OPTED_OUT':
                    has_opted_in = False
                break
        else:
            # No TEXT_ASSET_AUTOMATION setting found — default is OPTED_IN
            has_opted_in = True
        if has_opted_in:
            auto_asset_campaigns.append(camp.name)

    if not auto_asset_campaigns:
        results.append(CheckResult(19, 'Creative & Ads',
            'Auto-created assets disabled', 'GREEN',
            'Text asset automation OFF on all non-PMAX campaigns'))
    else:
        results.append(CheckResult(19, 'Creative & Ads',
            'Auto-created assets disabled', 'RED',
            f'{len(auto_asset_campaigns)} campaign(s) have auto-created text assets ON',
            action='Disable text asset automation in campaign settings'))

    # Check 20: URL validation (simplified — check for empty final_urls)
    broken_urls = 0
    for r in enabled_ads:
        urls = list(r.ad_group_ad.ad.final_urls)
        if not urls or urls[0] == '':
            broken_urls += 1

    if broken_urls == 0:
        results.append(CheckResult(20, 'Creative & Ads',
            'Destination URLs valid', 'GREEN',
            f'All {total_ads} ads have destination URLs'))
    elif broken_urls <= 2:
        results.append(CheckResult(20, 'Creative & Ads',
            'Destination URLs valid', 'YELLOW',
            f'{broken_urls} ads with missing/empty URLs',
            action='Fix missing destination URLs'))
    else:
        results.append(CheckResult(20, 'Creative & Ads',
            'Destination URLs valid', 'RED',
            f'{broken_urls} ads with missing/empty URLs',
            action='Multiple ads with broken URLs — fix immediately'))

    # Check 21: Seasonal content (simplified — look for date-specific words)
    seasonal_patterns = [
        r'\b(spring|summer|fall|winter|autumn)\s+(sale|special|offer|promo)',
        r'\b(holiday|christmas|thanksgiving|valentine|easter|memorial day)',
        r'\b(black friday|cyber monday|new year)',
        r'\b(2024|2023|2022)\b',  # outdated years
    ]
    seasonal_found = False
    for r in enabled_ads:
        ad = r.ad_group_ad.ad
        if hasattr(ad, 'responsive_search_ad') and ad.responsive_search_ad:
            for h in ad.responsive_search_ad.headlines:
                for pat in seasonal_patterns:
                    if re.search(pat, h.text, re.IGNORECASE):
                        seasonal_found = True; break
                if seasonal_found: break
            if not seasonal_found:
                for d in ad.responsive_search_ad.descriptions:
                    for pat in seasonal_patterns:
                        if re.search(pat, d.text, re.IGNORECASE):
                            seasonal_found = True; break
                    if seasonal_found: break
        if seasonal_found: break

    if not seasonal_found:
        results.append(CheckResult(21, 'Creative & Ads',
            'No outdated seasonal copy', 'GREEN',
            'No seasonal/dated references found'))
    else:
        results.append(CheckResult(21, 'Creative & Ads',
            'No outdated seasonal copy', cfg.get('seasonal_severity', 'RED'),
            'Outdated seasonal or year-specific content found',
            action='Remove/update seasonal references in ad copy'))

    # Check 22: Auto-applied recommendations — query recommendation_subscription
    APPROVED_REC_TYPES = {'OPTIMIZE_AD_ROTATION'}
    HIGH_RISK_REC_TYPES = {
        'KEYWORD', 'RAISE_TARGET_CPA_BID_TOO_LOW', 'LOWER_TARGET_ROAS',
        'RESPONSIVE_SEARCH_AD', 'USE_BROAD_MATCH_KEYWORD', 'RAISE_TARGET_CPA',
        'FORECASTING_SET_TARGET_CPA', 'FORECASTING_SET_TARGET_ROAS',
    }
    enabled_recs = []
    high_risk_recs = []
    for r in data.get('rec_subscriptions', []):
        sub = r.recommendation_subscription
        rec_type = sub.type.name if sub.type else 'UNKNOWN'
        status = sub.status.name if sub.status else 'UNKNOWN'
        if status == 'ENABLED' and rec_type not in APPROVED_REC_TYPES:
            enabled_recs.append(rec_type)
            if rec_type in HIGH_RISK_REC_TYPES:
                high_risk_recs.append(rec_type)

    if not enabled_recs:
        results.append(CheckResult(22, 'Creative & Ads',
            'Auto-applied recommendations disabled', 'GREEN',
            'No auto-apply recommendations enabled (or only approved types)'))
    elif high_risk_recs:
        results.append(CheckResult(22, 'Creative & Ads',
            'Auto-applied recommendations disabled', 'RED',
            f'{len(high_risk_recs)} high-risk auto-apply: {", ".join(high_risk_recs[:3])}',
            action='Disable auto-apply for bid/keyword/ad types immediately'))
    else:
        results.append(CheckResult(22, 'Creative & Ads',
            'Auto-applied recommendations disabled', 'YELLOW',
            f'{len(enabled_recs)} auto-apply types enabled: {", ".join(enabled_recs[:3])}',
            action='Review auto-apply settings — consider disabling'))

    return results


def checks_assets(data, cfg):
    results = []
    assets = data.get('assets', [])

    if not assets:
        return [
            CheckResult(23, 'RSA Assets', 'Assets have performance data', 'N/A', 'No asset data'),
            CheckResult(24, 'RSA Assets', 'LOW-rated assets controlled', 'N/A', 'No asset data'),
            CheckResult(25, 'RSA Assets', 'BEST-rated assets exist', 'N/A', 'No asset data'),
        ]

    # Filter to headline/description assets only
    rsa_assets = [r for r in assets
                  if r.ad_group_ad_asset_view.field_type.name in ('HEADLINE', 'DESCRIPTION')]

    if not rsa_assets:
        return [
            CheckResult(23, 'RSA Assets', 'Assets have performance data', 'N/A', 'No RSA assets'),
            CheckResult(24, 'RSA Assets', 'LOW-rated assets controlled', 'N/A', 'No RSA assets'),
            CheckResult(25, 'RSA Assets', 'BEST-rated assets exist', 'N/A', 'No RSA assets'),
        ]

    labels = defaultdict(int)
    for r in rsa_assets:
        label = r.ad_group_ad_asset_view.performance_label.name
        labels[label] += 1

    total = len(rsa_assets)
    best = labels.get('BEST', 0)
    good = labels.get('GOOD', 0)
    low = labels.get('LOW', 0)
    learning = labels.get('LEARNING', 0) + labels.get('UNSPECIFIED', 0)
    rated = total - learning

    # Check 23: Performance data
    rated_pct = (rated / total * 100) if total > 0 else 0
    if rated_pct > 75:
        results.append(CheckResult(23, 'RSA Assets',
            'Assets have performance data', 'GREEN',
            f"{rated_pct:.0f}% have labels ({rated}/{total})"))
    elif rated_pct > 50:
        results.append(CheckResult(23, 'RSA Assets',
            'Assets have performance data', 'YELLOW',
            f"{rated_pct:.0f}% have labels ({rated}/{total})",
            action='Allow more time for assets to accumulate data'))
    else:
        results.append(CheckResult(23, 'RSA Assets',
            'Assets have performance data', 'RED',
            f"{rated_pct:.0f}% have labels ({rated}/{total})",
            action='Most assets lack data — check volume or ad rotation'))

    # Check 24: LOW assets
    low_pct = (low / total * 100) if total > 0 else 0
    if low_pct < 15:
        results.append(CheckResult(24, 'RSA Assets',
            'LOW-rated assets controlled', 'GREEN',
            f"{low_pct:.0f}% LOW ({low}/{total})"))
    elif low_pct < 30:
        results.append(CheckResult(24, 'RSA Assets',
            'LOW-rated assets controlled', 'YELLOW',
            f"{low_pct:.0f}% LOW ({low}/{total})",
            action='Replace LOW-performing assets with new variations'))
    else:
        results.append(CheckResult(24, 'RSA Assets',
            'LOW-rated assets controlled', 'RED',
            f"{low_pct:.0f}% LOW ({low}/{total})",
            action='Many underperforming assets — major refresh needed'))

    # Check 25: BEST assets exist
    hl_assets = [r for r in rsa_assets if r.ad_group_ad_asset_view.field_type.name == 'HEADLINE']
    desc_assets = [r for r in rsa_assets if r.ad_group_ad_asset_view.field_type.name == 'DESCRIPTION']
    best_hl = any(r.ad_group_ad_asset_view.performance_label.name == 'BEST' for r in hl_assets)
    best_desc = any(r.ad_group_ad_asset_view.performance_label.name == 'BEST' for r in desc_assets)

    if best_hl and best_desc:
        results.append(CheckResult(25, 'RSA Assets',
            'BEST-rated assets exist', 'GREEN',
            f"BEST headlines and descriptions found ({best} total BEST)"))
    elif best_hl or best_desc:
        results.append(CheckResult(25, 'RSA Assets',
            'BEST-rated assets exist', 'YELLOW',
            f"BEST in {'headlines' if best_hl else 'descriptions'} only",
            action='Improve the other asset type to achieve BEST rating'))
    else:
        results.append(CheckResult(25, 'RSA Assets',
            'BEST-rated assets exist', 'RED',
            'No BEST-rated assets found',
            action='Review top performers and create stronger variations'))

    return results


def checks_settings(data, cfg):
    results = []
    campaigns = data.get('campaigns', [])

    if not campaigns:
        return [CheckResult(n, 'Account Settings', f'Check {n}', 'N/A', 'No campaigns')
                for n in range(26, 30)]

    # Check 26: Location targeting
    bad_geo = []
    for r in campaigns:
        geo = r.campaign.geo_target_type_setting.positive_geo_target_type.name
        if geo == 'PRESENCE_OR_INTEREST':
            bad_geo.append(r.campaign.name)

    if not bad_geo:
        results.append(CheckResult(26, 'Account Settings',
            'Location targeting set correctly', 'GREEN',
            'All campaigns use PRESENCE only'))
    else:
        results.append(CheckResult(26, 'Account Settings',
            'Location targeting set correctly', 'RED',
            f"{len(bad_geo)} campaign(s) use PRESENCE_OR_INTEREST",
            action='Change to PRESENCE only to avoid irrelevant traffic'))

    # Check 27: Content suitability — query customer.video_brand_safety_suitability
    brand_safety_rows = data.get('brand_safety', [])
    if brand_safety_rows:
        suitability = brand_safety_rows[0].customer.video_brand_safety_suitability.name
        if suitability in ('LIMITED_INVENTORY', 'STANDARD_INVENTORY'):
            results.append(CheckResult(27, 'Account Settings',
                'Content suitability configured', 'GREEN',
                f'Set to {suitability}'))
        elif suitability == 'EXPANDED_INVENTORY':
            results.append(CheckResult(27, 'Account Settings',
                'Content suitability configured', 'RED',
                'Set to EXPANDED_INVENTORY (least restrictive)',
                action='Change to LIMITED_INVENTORY or STANDARD_INVENTORY'))
        else:
            results.append(CheckResult(27, 'Account Settings',
                'Content suitability configured', 'YELLOW',
                f'Set to {suitability} — review appropriateness',
                action='Consider setting to LIMITED_INVENTORY for brand safety'))
    else:
        results.append(CheckResult(27, 'Account Settings',
            'Content suitability configured', 'N/A',
            'Could not query brand safety setting'))

    # Check 28: Auto-applied recommendations (account-level, same data as check 22)
    APPROVED_REC_TYPES_28 = {'OPTIMIZE_AD_ROTATION'}
    enabled_recs_28 = []
    for r in data.get('rec_subscriptions', []):
        sub = r.recommendation_subscription
        rec_type = sub.type.name if sub.type else 'UNKNOWN'
        status = sub.status.name if sub.status else 'UNKNOWN'
        if status == 'ENABLED' and rec_type not in APPROVED_REC_TYPES_28:
            enabled_recs_28.append(rec_type)

    if not enabled_recs_28:
        results.append(CheckResult(28, 'Account Settings',
            'Auto-applied recommendations off', 'GREEN',
            'No risky auto-apply types enabled'))
    else:
        results.append(CheckResult(28, 'Account Settings',
            'Auto-applied recommendations off', 'RED',
            f'{len(enabled_recs_28)} auto-apply types enabled',
            action='Disable all auto-apply in Recommendations settings'))

    # Check 29: Geographic exclusions — query campaign_criterion negatives
    geo_exclusions = data.get('geo_exclusions', [])
    campaigns_with_exclusions = set()
    for r in geo_exclusions:
        campaigns_with_exclusions.add(r.campaign.id)

    if campaigns_with_exclusions:
        results.append(CheckResult(29, 'Account Settings',
            'Geographic exclusions present', 'GREEN',
            f'{len(geo_exclusions)} exclusion(s) across {len(campaigns_with_exclusions)} campaign(s)'))
    else:
        results.append(CheckResult(29, 'Account Settings',
            'Geographic exclusions present', cfg.get('geo_exclusion_severity', 'RED'),
            'Zero geographic exclusions on any campaign',
            action='Add location exclusions for irrelevant areas'))

    return results


def checks_pmax(data, cfg):
    results = []
    pmax_campaigns = [r for r in data.get('campaigns', [])
                      if r.campaign.advertising_channel_type.name == 'PERFORMANCE_MAX']

    if not pmax_campaigns:
        return [CheckResult(n, 'PMAX Config', f'Check {n}', 'N/A', 'No PMAX campaigns')
                for n in range(30, 35)]

    # Parse PMAX asset automation settings from API data
    pmax_automation = {}
    for r in data.get('asset_automation', []):
        camp = r.campaign
        if camp.advertising_channel_type.name != 'PERFORMANCE_MAX':
            continue
        settings = {}
        # Defaults: all OPTED_IN if not explicitly set
        for atype in ('TEXT_ASSET_AUTOMATION', 'GENERATE_IMAGE_EXTRACTION',
                      'GENERATE_IMAGE_ENHANCEMENT', 'GENERATE_ENHANCED_YOUTUBE_VIDEOS',
                      'FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION'):
            settings[atype] = 'OPTED_IN'
        for setting in camp.asset_automation_settings:
            tname = setting.asset_automation_type.name
            settings[tname] = setting.asset_automation_status.name
        pmax_automation[camp.name] = settings

    # Check 30: Text asset automation
    text_on = [n for n, s in pmax_automation.items() if s.get('TEXT_ASSET_AUTOMATION') == 'OPTED_IN']
    if not text_on:
        results.append(CheckResult(30, 'PMAX Config',
            'Text asset automation disabled', 'GREEN',
            f'OFF on all {len(pmax_automation)} PMAX campaign(s)'))
    else:
        results.append(CheckResult(30, 'PMAX Config',
            'Text asset automation disabled', 'RED',
            f'ON in {len(text_on)} PMAX campaign(s): {", ".join(text_on[:2])}',
            action='Disable text asset automation in PMAX settings'))

    # Check 31: Image asset automation (extraction + enhancement)
    image_on = []
    for name, s in pmax_automation.items():
        if s.get('GENERATE_IMAGE_EXTRACTION') == 'OPTED_IN' or \
           s.get('GENERATE_IMAGE_ENHANCEMENT') == 'OPTED_IN':
            image_on.append(name)
    if not image_on:
        results.append(CheckResult(31, 'PMAX Config',
            'Image asset automation disabled', 'GREEN',
            f'OFF on all {len(pmax_automation)} PMAX campaign(s)'))
    else:
        results.append(CheckResult(31, 'PMAX Config',
            'Image asset automation disabled', 'RED',
            f'ON in {len(image_on)} PMAX campaign(s): {", ".join(image_on[:2])}',
            action='Disable image extraction/enhancement in PMAX settings'))

    # Check 32: Final URL expansion — via asset_automation_settings
    url_exp_on = []
    for name, s in pmax_automation.items():
        # Default is OPTED_IN if not explicitly set
        status = s.get('FINAL_URL_EXPANSION_TEXT_ASSET_AUTOMATION', 'OPTED_IN')
        if status == 'OPTED_IN':
            url_exp_on.append(name)
    if not url_exp_on:
        results.append(CheckResult(32, 'PMAX Config',
            'Final URL expansion disabled', 'GREEN',
            f'OFF on all {len(pmax_automation)} PMAX campaign(s)'))
    else:
        results.append(CheckResult(32, 'PMAX Config',
            'Final URL expansion disabled', 'RED',
            f'ON in {len(url_exp_on)} PMAX campaign(s): {", ".join(url_exp_on[:2])}',
            action='Disable Final URL expansion in PMAX settings'))

    # Check 33: Search themes
    asset_groups = data.get('pmax_asset_groups', [])
    if asset_groups:
        results.append(CheckResult(33, 'PMAX Config',
            'Search themes present', 'GREEN',
            f"{len(asset_groups)} asset group(s) found — verify themes in UI",
            action='Check that each asset group has search themes'))
    else:
        results.append(CheckResult(33, 'PMAX Config',
            'Search themes present', 'RED',
            'No asset groups found in PMAX campaigns',
            action='Create asset groups with search themes'))

    # Check 34: Audience signals
    if asset_groups:
        results.append(CheckResult(34, 'PMAX Config',
            'Audience signals present', 'GREEN',
            f"{len(asset_groups)} asset group(s) — verify signals in UI",
            action='Check audience signals in each asset group'))
    else:
        results.append(CheckResult(34, 'PMAX Config',
            'Audience signals present', 'RED',
            'No asset groups found',
            action='Add audience signals to PMAX asset groups'))

    return results


def checks_negatives(data, cfg):
    results = []
    negs = data.get('negatives', [])
    campaigns = data.get('campaigns', [])
    search_campaigns = [r for r in campaigns
                        if r.campaign.advertising_channel_type.name == 'SEARCH']

    if not search_campaigns:
        return [
            CheckResult(35, 'Negative Keywords', 'Adequate negative coverage', 'N/A', 'No Search campaigns'),
            CheckResult(36, 'Negative Keywords', 'No negative keyword conflicts', 'N/A', 'No Search campaigns'),
        ]

    # Count negatives per campaign
    neg_per_campaign = defaultdict(int)
    for r in negs:
        neg_per_campaign[r.campaign.id] += 1

    total_search = len(search_campaigns)
    total_negs = sum(neg_per_campaign.values())
    avg = total_negs / total_search if total_search > 0 else 0
    neg_green = cfg.get('neg_green_bar', 20)
    neg_yellow = cfg.get('neg_yellow_bar', 10)

    # Check 35: Coverage
    if avg >= neg_green:
        results.append(CheckResult(35, 'Negative Keywords',
            'Adequate negative coverage', 'GREEN',
            f"Avg {avg:.0f} negatives/campaign ({total_negs} total)"))
    elif avg >= neg_yellow:
        results.append(CheckResult(35, 'Negative Keywords',
            'Adequate negative coverage', 'YELLOW',
            f"Avg {avg:.0f} negatives/campaign ({total_negs} total)",
            action='Add more negatives — run search term report'))
    else:
        results.append(CheckResult(35, 'Negative Keywords',
            'Adequate negative coverage', 'RED',
            f"Avg {avg:.0f} negatives/campaign ({total_negs} total)",
            action='Very low negative coverage — high waste risk'))

    # Check 36: Conflicts (simplified — compare neg keywords to active keywords)
    active_kws = set()
    for r in data.get('keywords', []):
        active_kws.add(r.ad_group_criterion.keyword.text.lower())

    neg_kws = set()
    for r in negs:
        neg_kws.add(r.campaign_criterion.keyword.text.lower())

    conflicts = active_kws & neg_kws
    if not conflicts:
        results.append(CheckResult(36, 'Negative Keywords',
            'No negative keyword conflicts', 'GREEN',
            f'0 conflicts found ({len(neg_kws)} negatives vs {len(active_kws)} keywords)'))
    elif len(conflicts) <= 3:
        results.append(CheckResult(36, 'Negative Keywords',
            'No negative keyword conflicts', 'YELLOW',
            f'{len(conflicts)} exact-match conflicts: {", ".join(list(conflicts)[:3])}',
            action='Remove conflicting negatives or pause keywords'))
    else:
        results.append(CheckResult(36, 'Negative Keywords',
            'No negative keyword conflicts', 'RED',
            f'{len(conflicts)} conflicts found',
            action='Multiple conflicts — negatives blocking active keywords'))

    return results


def checks_placements(data, cfg):
    results = []
    placements = data.get('placements', [])

    if not placements:
        return [
            CheckResult(37, 'Placement Safety', 'No suspicious placements', 'N/A', 'No placement data'),
            CheckResult(38, 'Placement Safety', 'No brand-unsafe placements', 'N/A', 'No placement data'),
        ]

    # Suspicious TLDs and domains
    bad_tlds = {'.ru', '.cn', '.xyz', '.tk', '.pw', '.cc', '.ws', '.buzz', '.top'}
    spam_patterns = ['click', 'traffic', 'anonymous', 'proxy', 'free-', 'cheap-']
    yt_bad_patterns = ['kids', 'toys', 'cartoon', 'nursery', 'xxx', 'adult', 'gambling']

    suspicious = []
    yt_unsafe = []

    for r in placements:
        p = r.detail_placement_view.placement
        ptype = r.detail_placement_view.placement_type.name

        # Check suspicious domains
        if ptype == 'WEBSITE':
            for tld in bad_tlds:
                if p.endswith(tld):
                    suspicious.append(p); break
            else:
                for pat in spam_patterns:
                    if pat in p.lower():
                        suspicious.append(p); break

        # Check YouTube
        if ptype in ('YOUTUBE_VIDEO', 'YOUTUBE_CHANNEL'):
            for pat in yt_bad_patterns:
                if pat in p.lower():
                    yt_unsafe.append(p); break

    # Check 37: Suspicious domains
    if not suspicious:
        results.append(CheckResult(37, 'Placement Safety',
            'No suspicious placements', 'GREEN',
            f'0 flagged out of {len(placements)} placements'))
    elif len(suspicious) <= 5:
        results.append(CheckResult(37, 'Placement Safety',
            'No suspicious placements', 'YELLOW',
            f'{len(suspicious)} suspicious: {", ".join(suspicious[:3])}',
            action='Review and exclude flagged placements'))
    else:
        results.append(CheckResult(37, 'Placement Safety',
            'No suspicious placements', 'RED',
            f'{len(suspicious)} suspicious placements found',
            action='Placement exclusion list needed — brand safety risk'))

    # Check 38: YouTube safety
    if not yt_unsafe:
        results.append(CheckResult(38, 'Placement Safety',
            'No brand-unsafe placements', 'GREEN',
            'No flagged YouTube placements'))
    elif len(yt_unsafe) <= 3:
        results.append(CheckResult(38, 'Placement Safety',
            'No brand-unsafe placements', 'YELLOW',
            f'{len(yt_unsafe)} flagged YouTube placements',
            action='Review and exclude inappropriate YouTube placements'))
    else:
        results.append(CheckResult(38, 'Placement Safety',
            'No brand-unsafe placements', 'RED',
            f'{len(yt_unsafe)} brand-unsafe YouTube placements',
            action='Immediate YouTube exclusion needed'))

    return results


def checks_extensions(data, cfg):
    results = []
    exts = data.get('extensions', [])

    ext_types = defaultdict(int)
    for r in exts:
        atype = r.asset.type_.name
        ext_types[atype] += 1

    sitelinks = ext_types.get('SITELINK', 0)
    callouts = ext_types.get('CALLOUT', 0)
    snippets = ext_types.get('STRUCTURED_SNIPPET', 0)
    images = ext_types.get('IMAGE', 0)

    # Check 39: Core extensions
    has_sitelinks = sitelinks >= 4
    has_callouts = callouts >= 4
    if has_sitelinks and has_callouts:
        results.append(CheckResult(39, 'Extensions',
            'Core extensions present', 'GREEN',
            f'{sitelinks} sitelinks, {callouts} callouts'))
    elif has_sitelinks or has_callouts:
        results.append(CheckResult(39, 'Extensions',
            'Core extensions present', 'YELLOW',
            f'{sitelinks} sitelinks, {callouts} callouts',
            action='Add missing extension type (need >=4 of each)'))
    else:
        results.append(CheckResult(39, 'Extensions',
            'Core extensions present', 'RED',
            f'{sitelinks} sitelinks, {callouts} callouts',
            action='Add sitelink and callout extensions'))

    # Check 40: Supplemental extensions
    has_snippets = snippets >= 1
    has_images = images >= 1
    if has_snippets and has_images:
        results.append(CheckResult(40, 'Extensions',
            'Supplemental extensions present', 'GREEN',
            f'{snippets} structured snippets, {images} images'))
    elif has_snippets or has_images:
        results.append(CheckResult(40, 'Extensions',
            'Supplemental extensions present', 'YELLOW',
            f'{snippets} snippets, {images} images',
            action='Add missing supplemental extensions'))
    else:
        results.append(CheckResult(40, 'Extensions',
            'Supplemental extensions present', 'RED',
            'No structured snippets or image extensions',
            action='Add structured snippets and image extensions'))

    return results


def checks_call_location(data, cfg):
    """Checks 41-42 — call & location extensions. Local-service only.

    Phone-driven local businesses (auto repair, etc.) depend on click-to-call
    and Google Business Profile location extensions; core checks 39-40 only cover
    sitelinks/callouts/snippets/images. Gated behind the local-service preset so
    property-management runs stay at the core checks with no extra queries.
    """
    if not cfg.get('check_call_location_ext'):
        return []

    def count_field_type(ft):
        n = 0
        for r in data.get('campaign_asset_fieldtypes', []):
            if r.campaign_asset.field_type.name == ft:
                n += 1
        for r in data.get('customer_asset_fieldtypes', []):
            if r.customer_asset.field_type.name == ft:
                n += 1
        return n

    results = []

    # Check 41: Call extensions present
    call_n = count_field_type('CALL')
    if call_n >= 1:
        results.append(CheckResult(41, 'Local Service',
            'Call extensions present', 'GREEN',
            f'{call_n} call extension link(s) serving'))
    else:
        results.append(CheckResult(41, 'Local Service',
            'Call extensions present', 'RED',
            'No call extensions — critical for phone-driven local service',
            action='Add call extensions (or call assets) to enabled campaigns'))

    # Check 42: Location extensions present
    # Soft YELLOW (not RED) on absence: location assets sourced via a linked
    # Business Profile can be configured in ways the field_type scan may miss,
    # so flag for verification rather than fail outright.
    loc_n = count_field_type('LOCATION')
    if loc_n >= 1:
        results.append(CheckResult(42, 'Local Service',
            'Location extensions present', 'GREEN',
            f'{loc_n} location extension link(s) serving'))
    else:
        results.append(CheckResult(42, 'Local Service',
            'Location extensions present', 'YELLOW',
            'No location extensions detected — verify Business Profile linkage',
            action='Link Google Business Profile for location extensions'))

    return results


# DGen ad-level asset automation: applicable settings + Google-side default
# per ad type (mirrors fix_dgen_ad_automation.py's AD_TYPE_SETTINGS; carousel
# and product ads have no automation settings). A setting absent from the API
# response sits at its default — LANDING_PAGE_PREVIEW is the one type that
# defaults OFF, everything else defaults ON.
DGEN_AD_TYPE_SETTINGS = {
    'DEMAND_GEN_MULTI_ASSET_AD': {
        'GENERATE_DESIGN_VERSIONS_FOR_IMAGES': 'OPTED_IN',
        'GENERATE_VIDEOS_FROM_OTHER_ASSETS': 'OPTED_IN',
    },
    'DEMAND_GEN_VIDEO_RESPONSIVE_AD': {
        'GENERATE_VERTICAL_YOUTUBE_VIDEOS': 'OPTED_IN',
        'GENERATE_SHORTER_YOUTUBE_VIDEOS': 'OPTED_IN',
        'GENERATE_LANDING_PAGE_PREVIEW': 'OPTED_OUT',
    },
}


def checks_dgen_video(data, cfg):
    """Checks 43-44 — video & DGen automation (added 2026-07-09).

    43: PMAX video enhancement automation (GENERATE_ENHANCED_YOUTUBE_VIDEOS).
        Campaign-level — parsed from the same asset_automation fetch as
        checks 30-32, which always pulled this type but never read it.
    44: DGen ad-level asset automation. DGen automation lives on the AD
        (ad_group_ad.ad_group_ad_asset_automation_settings), not the
        campaign, so checks 19/30-32 structurally can't see it.
    """
    results = []

    # Check 43: PMAX video enhancements
    pmax_video_on = []
    pmax_seen = 0
    for r in data.get('asset_automation', []):
        camp = r.campaign
        if camp.advertising_channel_type.name != 'PERFORMANCE_MAX':
            continue
        pmax_seen += 1
        status = 'OPTED_IN'  # Google default when not explicitly set
        for setting in camp.asset_automation_settings:
            if setting.asset_automation_type.name == 'GENERATE_ENHANCED_YOUTUBE_VIDEOS':
                status = setting.asset_automation_status.name
                break
        if status == 'OPTED_IN':
            pmax_video_on.append(camp.name)

    if pmax_seen == 0:
        results.append(CheckResult(43, 'Video & DGen Automation',
            'PMAX video enhancements disabled', 'N/A', 'No PMAX campaigns'))
    elif pmax_video_on:
        results.append(CheckResult(43, 'Video & DGen Automation',
            'PMAX video enhancements disabled', 'RED',
            f'ON in {len(pmax_video_on)} PMAX campaign(s): {", ".join(pmax_video_on[:2])}',
            action='Disable video enhancements (enhanced YouTube videos) in PMAX settings'))
    else:
        results.append(CheckResult(43, 'Video & DGen Automation',
            'PMAX video enhancements disabled', 'GREEN',
            f'OFF on all {pmax_seen} PMAX campaign(s)'))

    # Check 44: DGen ad-level automation
    dgen_campaigns = [r for r in data.get('campaigns', [])
                      if r.campaign.advertising_channel_type.name == 'DEMAND_GEN']
    if not dgen_campaigns:
        results.append(CheckResult(44, 'Video & DGen Automation',
            'DGen ad-level automation disabled', 'N/A', 'No DGen campaigns'))
        return results

    inspectable = 0
    flagged_ads = 0
    flagged_settings = 0
    flagged_campaigns = set()
    for r in data.get('dgen_ads', []):
        ad_type = r.ad_group_ad.ad.type.name
        defaults = DGEN_AD_TYPE_SETTINGS.get(ad_type)
        if not defaults:
            continue  # carousel/product ads have no automation settings
        inspectable += 1
        current = dict(defaults)
        for setting in r.ad_group_ad.ad_group_ad_asset_automation_settings:
            tname = setting.asset_automation_type.name
            if tname in current:
                current[tname] = setting.asset_automation_status.name
        on = [t for t, s in current.items() if s == 'OPTED_IN']
        if on:
            flagged_ads += 1
            flagged_settings += len(on)
            flagged_campaigns.add(r.campaign.name)

    if inspectable == 0:
        results.append(CheckResult(44, 'Video & DGen Automation',
            'DGen ad-level automation disabled', 'N/A',
            f'{len(dgen_campaigns)} DGen campaign(s) but no enabled multi-asset/video ads'))
    elif flagged_ads:
        camps = ', '.join(sorted(flagged_campaigns)[:2])
        results.append(CheckResult(44, 'Video & DGen Automation',
            'DGen ad-level automation disabled', 'RED',
            f'{flagged_settings} automation setting(s) ON across {flagged_ads}/{inspectable} DGen ad(s) ({camps})',
            action='Disable DGen ad-level asset automation (see the dgen-automation-disable skill — dry-run first)'))
    else:
        results.append(CheckResult(44, 'Video & DGen Automation',
            'DGen ad-level automation disabled', 'GREEN',
            f'All automation OFF across {inspectable} DGen ad(s)'))

    return results


# ── Scoring ───────────────────────────────────────────────────────

def score(checks):
    """Calculate overall R/Y/G from check results."""
    green = sum(1 for c in checks if c.status == 'GREEN')
    yellow = sum(1 for c in checks if c.status == 'YELLOW')
    red = sum(1 for c in checks if c.status == 'RED')
    na = sum(1 for c in checks if c.status == 'N/A')

    # Auto-Red triggers
    auto_red_trigger = ''
    for c in checks:
        if c.auto_red:
            auto_red_trigger = f"Auto-RED: {c.name} — {c.finding}"
            break

    if auto_red_trigger:
        overall = 'RED'
    elif red >= 3:
        overall = 'RED'
    elif red >= 1 or yellow >= 6:
        overall = 'YELLOW'
    else:
        overall = 'GREEN'

    est_waste = sum(c.dollar_impact for c in checks if c.dollar_impact > 0)

    return overall, green, yellow, red, na, auto_red_trigger, est_waste


# ── Output Writers ────────────────────────────────────────────────

def write_csv(report):
    """Write the inspection report to a CSV under the skill's data/ folder."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M')
    path = OUTPUT_DIR / f"diagnostic-{report.cid}-{stamp}.csv"
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['#', 'Category', 'Check', 'Status', 'Finding',
                    'Dollar Impact', 'Action'])
        for c in report.checks:
            w.writerow([c.number, c.category, c.name, c.status, c.finding,
                        f'{c.dollar_impact:.0f}' if c.dollar_impact > 0 else '',
                        c.action])
        w.writerow([])
        w.writerow(['OVERALL', report.overall,
                    f'{report.green} Green / {report.yellow} Yellow / '
                    f'{report.red} Red / {report.na} N/A',
                    '', f'Estimated waste: ${report.est_waste:,.0f}/mo', '',
                    report.run_date])
    return path


def write_to_sheet(report, sheet_id):
    """Write the color-coded 'Inspection' tab into an existing Google Sheet.

    Auth is gspread's service-account flow (service_account.json in
    ~/.config/gspread/ by default). Create a Google Cloud service account
    with the Sheets API enabled, download its JSON key to that path, and
    share the target sheet with the service account's client_email as an
    editor. See: https://docs.gspread.org/en/latest/oauth2.html
    """
    try:
        import gspread
    except ImportError:
        print("WARNING: gspread not installed — skipping Sheets upload. "
              "Run: pip install gspread google-auth")
        return None

    client = gspread.service_account()
    sh = client.open_by_key(sheet_id)

    # ── Inspection tab ──
    try:
        ws = sh.worksheet('Inspection')
        ws.clear()
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet('Inspection', rows=50, cols=8)

    # Header banner
    banner = [
        [f'{len(report.checks)}-POINT GOOGLE ADS INSPECTION', '', '', '', '', '', '', ''],
        [f'Account: {report.account_name}', f'CID: {report.cid}',
         f'Overall: {report.overall}',
         f'{report.green} Green', f'{report.yellow} Yellow',
         f'{report.red} Red', f'{report.na} N/A',
         f'Run: {report.run_date}'],
        ['#', 'Category', 'Check', 'Status', 'Finding', 'Dollar Impact', 'Action', ''],
    ]

    rows = []
    for c in report.checks:
        dollar = f'${c.dollar_impact:,.0f}' if c.dollar_impact > 0 else ''
        rows.append([c.number, c.category, c.name, c.status,
                      c.finding, dollar, c.action, ''])

    all_rows = banner + rows
    ws.update(all_rows, value_input_option='USER_ENTERED')

    # Color coding
    GREEN_BG = {'red': 0.718, 'green': 0.882, 'blue': 0.804}   # #b7e1cd
    YELLOW_BG = {'red': 0.988, 'green': 0.910, 'blue': 0.698}  # #fce8b2
    RED_BG = {'red': 0.957, 'green': 0.780, 'blue': 0.765}     # #f4c7c3
    GRAY_BG = {'red': 0.953, 'green': 0.953, 'blue': 0.953}    # #f3f3f3
    WHITE = {'red': 1, 'green': 1, 'blue': 1}
    DARK = {'red': 0.2, 'green': 0.2, 'blue': 0.2}
    BOLD = {'bold': True}

    color_map = {'GREEN': GREEN_BG, 'YELLOW': YELLOW_BG, 'RED': RED_BG, 'N/A': GRAY_BG}

    # Overall banner color
    overall_bg = color_map.get(report.overall, WHITE)

    requests = []

    # Format header row
    requests.append({
        'repeatCell': {
            'range': {'sheetId': ws.id, 'startRowIndex': 0, 'endRowIndex': 1,
                      'startColumnIndex': 0, 'endColumnIndex': 8},
            'cell': {'userEnteredFormat': {
                'textFormat': {'bold': True, 'fontSize': 14},
                'backgroundColor': {'red': 0.15, 'green': 0.15, 'blue': 0.15},
                'textFormat': {'bold': True, 'fontSize': 14,
                               'foregroundColor': WHITE},
            }},
            'fields': 'userEnteredFormat(textFormat,backgroundColor)'
        }
    })

    # Overall status color on row 2
    requests.append({
        'repeatCell': {
            'range': {'sheetId': ws.id, 'startRowIndex': 1, 'endRowIndex': 2,
                      'startColumnIndex': 0, 'endColumnIndex': 8},
            'cell': {'userEnteredFormat': {
                'backgroundColor': overall_bg,
                'textFormat': {'bold': True, 'fontSize': 11}
            }},
            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
        }
    })

    # Column headers row 3
    requests.append({
        'repeatCell': {
            'range': {'sheetId': ws.id, 'startRowIndex': 2, 'endRowIndex': 3,
                      'startColumnIndex': 0, 'endColumnIndex': 8},
            'cell': {'userEnteredFormat': {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
            }},
            'fields': 'userEnteredFormat(textFormat,backgroundColor)'
        }
    })

    # Color each check row's Status cell (column D, index 3)
    for i, c in enumerate(report.checks):
        row_idx = i + 3  # offset for banner + headers
        bg = color_map.get(c.status, WHITE)
        requests.append({
            'repeatCell': {
                'range': {'sheetId': ws.id, 'startRowIndex': row_idx, 'endRowIndex': row_idx + 1,
                          'startColumnIndex': 3, 'endColumnIndex': 4},
                'cell': {'userEnteredFormat': {
                    'backgroundColor': bg,
                    'textFormat': {'bold': c.status in ('RED', 'YELLOW')},
                }},
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'
            }
        })

    # Auto-resize columns
    requests.append({
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': ws.id,
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': 8,
            }
        }
    })

    # Freeze header rows
    requests.append({
        'updateSheetProperties': {
            'properties': {
                'sheetId': ws.id,
                'gridProperties': {'frozenRowCount': 3}
            },
            'fields': 'gridProperties.frozenRowCount'
        }
    })

    sh.batch_update({'requests': requests})

    # Delete default Sheet1 if it exists
    try:
        default = sh.worksheet('Sheet1')
        sh.del_worksheet(default)
    except (gspread.exceptions.WorksheetNotFound, Exception):
        pass

    return sh.url


# ── Console Output ────────────────────────────────────────────────

def print_report(report):
    """Print inspection results to console."""
    print(f"\n{'='*70}")
    print(f"  {len(report.checks)}-POINT GOOGLE ADS INSPECTION")
    print(f"{'='*70}")
    print(f"  Account: {report.account_name}")
    print(f"  CID:     {report.cid}")
    print(f"  Date:    {report.run_date}")
    print(f"{'='*70}")

    status_icon = {'GREEN': '+', 'YELLOW': '!', 'RED': 'X', 'N/A': '-'}

    current_cat = ''
    for c in report.checks:
        if c.category != current_cat:
            current_cat = c.category
            print(f"\n  --- {current_cat.upper()} ---")

        icon = status_icon.get(c.status, '?')
        dollar = f" (${c.dollar_impact:,.0f})" if c.dollar_impact > 0 else ''
        print(f"  [{icon}] {c.number:2d}. {c.name}")
        print(f"       {c.status}: {c.finding}{dollar}")
        if c.action:
            print(f"       -> {c.action}")

    print(f"\n{'='*70}")
    print(f"  OVERALL: {report.overall}")
    print(f"  {report.green} Green | {report.yellow} Yellow | {report.red} Red | {report.na} N/A")
    if report.auto_red_trigger:
        print(f"  ** {report.auto_red_trigger}")
    if report.est_waste > 0:
        print(f"  Estimated waste: ${report.est_waste:,.0f}/mo")
    print(f"{'='*70}\n")


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='42-Point Google Ads Account Diagnostic')
    parser.add_argument('--cid', required=True, help='Customer ID (no dashes)')
    parser.add_argument('--name', default='', help='Account name (display only)')
    parser.add_argument('--days', type=int, default=30, help='Lookback days (default: 30)')
    parser.add_argument('--pacing-threshold', type=int, default=None,
                        help='Pacing tolerance %% (overrides the vertical preset)')
    parser.add_argument('--vertical', choices=sorted(VERTICAL_PRESETS.keys()),
                        default='property-management',
                        help='Calibration preset (default: property-management)')
    parser.add_argument('--sheet-id', default='',
                        help='Optional: existing Google Sheet ID to write the '
                             'color-coded Inspection tab into (requires gspread '
                             'service-account auth)')
    args = parser.parse_args()

    cid = args.cid.replace('-', '')

    vertical = args.vertical
    cfg = dict(VERTICAL_PRESETS[vertical])
    if args.pacing_threshold is not None:
        cfg['pacing_threshold'] = args.pacing_threshold

    print(f"\nDIAGNOSTIC: {args.name or cid}")
    print(f"  Vertical: {vertical}")
    print(f"{'='*50}")

    # Get account name if not provided
    client = get_client()
    account_name = args.name
    if not account_name:
        rows = gaql(client, cid, "SELECT customer.descriptive_name FROM customer LIMIT 1")
        if rows:
            account_name = rows[0].customer.descriptive_name
        else:
            account_name = f"Account {cid}"

    print(f"  Account: {account_name}")
    print(f"  CID: {cid}")
    print(f"  Lookback: {args.days} days")
    print(f"  Pacing threshold: +/-{cfg['pacing_threshold']}%\n")

    # Fetch all data
    print("Fetching data...")
    t0 = time.time()
    data = fetch_all_data(client, cid, args.days, cfg)
    fetch_time = time.time() - t0
    print(f"  Data fetched in {fetch_time:.1f}s\n")

    # Run all checks (40 core + gated/appended extras)
    print("Running inspection...")
    checks_all = []
    checks_all.extend(checks_conversion(data, cfg))
    checks_all.extend(checks_pacing(data, cfg))
    checks_all.extend(checks_impression_share(data, cfg))
    checks_all.extend(checks_quality_score(data, cfg))
    checks_all.extend(checks_search_terms(data, cfg))
    checks_all.extend(checks_keywords(data, cfg))
    checks_all.extend(checks_creative(data, cfg))
    checks_all.extend(checks_assets(data, cfg))
    checks_all.extend(checks_settings(data, cfg))
    checks_all.extend(checks_pmax(data, cfg))
    checks_all.extend(checks_negatives(data, cfg))
    checks_all.extend(checks_placements(data, cfg))
    checks_all.extend(checks_extensions(data, cfg))
    checks_all.extend(checks_call_location(data, cfg))  # 41-42, local-service only
    checks_all.extend(checks_dgen_video(data, cfg))     # 43-44, video & DGen automation

    # Score
    overall, green, yellow, red, na, auto_red, est_waste = score(checks_all)

    report = InspectionReport(
        account_name=account_name,
        cid=cid,
        checks=checks_all,
        overall=overall,
        green=green,
        yellow=yellow,
        red=red,
        na=na,
        auto_red_trigger=auto_red,
        est_waste=est_waste,
        run_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
    )

    # Output
    print_report(report)

    csv_path = write_csv(report)
    print(f"  CSV report: {csv_path}")

    if args.sheet_id:
        print("\nWriting to Google Sheet...")
        url = write_to_sheet(report, args.sheet_id)
        if url:
            print(f"  Sheet URL: {url}")


if __name__ == '__main__':
    main()
