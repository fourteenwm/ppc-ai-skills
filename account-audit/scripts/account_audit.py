#!/usr/bin/env python3
"""
Google Ads Single-Account Audit v1.0

Comprehensive account health audit covering:
- Performance, pacing, and period-over-period comparison
- Conversion tracking health
- Keyword, search term, and asset performance
- Impression share diagnostics
- Creative compliance and negative keyword hygiene

Usage:
    python account_audit.py "Account Name"
    python account_audit.py --cid 1234567890
    python account_audit.py "Account Name" --days 30

Requires:
    - google-ads.yaml at project root (Google Ads API credentials)
    - accounts.md at project root (name-to-CID mapping)
    - pip install google-ads pandas matplotlib pyyaml numpy
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import argparse
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import base64

# Third-party imports
try:
    import yaml
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    from google.ads.googleads.client import GoogleAdsClient
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install google-ads pandas matplotlib pyyaml")
    sys.exit(1)

# Constants
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
CREDENTIALS_PATH = ROOT_DIR / 'google-ads.yaml'
ACCOUNTS_PATH = ROOT_DIR / 'accounts.md'
OUTPUT_DIR = ROOT_DIR / 'data' / 'audits'

# Report styling
PRIMARY_COLOR = '#1a73e8'
SECONDARY_COLOR = '#f5a623'
SUCCESS_COLOR = '#28a745'
WARNING_COLOR = '#ffc107'
DANGER_COLOR = '#dc3545'


def load_accounts():
    """Load account mappings from accounts.md.

    Expected format:
        ### CID: 123-456-7890
        - Account Name
        - Another Account Under Same CID

    Multiple accounts can share a CID. Dashes in CIDs are stripped.
    """
    accounts = {}
    if not ACCOUNTS_PATH.exists():
        return accounts

    with open(ACCOUNTS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    # Format is:
    # ### CID: XXX-XXX-XXXX
    # - Account Name

    current_cid = None
    for line in content.split('\n'):
        # Match CID line: ### CID: 123-456-7890
        cid_match = re.match(r'###\s*CID:\s*([\d\-]+)', line)
        if cid_match:
            # Convert CID format (remove dashes)
            current_cid = cid_match.group(1).replace('-', '')
            continue

        # Match account line: - Account Name
        account_match = re.match(r'-\s*(.+)', line)
        if account_match and current_cid:
            name = account_match.group(1).strip()
            if name:
                accounts[name.lower()] = {'name': name, 'cid': current_cid}

    return accounts


def resolve_account(account_input, cid=None):
    """Resolve account name to CID."""
    if cid:
        return cid, account_input or f"Account {cid}"

    accounts = load_accounts()
    account_lower = account_input.lower()

    # Exact match
    if account_lower in accounts:
        return accounts[account_lower]['cid'], accounts[account_lower]['name']

    # Partial match
    for key, val in accounts.items():
        if account_lower in key or key in account_lower:
            return val['cid'], val['name']

    print(f"Error: Account '{account_input}' not found in accounts.md")
    sys.exit(1)


def get_ads_client():
    """Get Google Ads API client."""
    return GoogleAdsClient.load_from_storage(str(CREDENTIALS_PATH))


def run_gaql(client, customer_id, query):
    """Execute GAQL query and return results as list of dicts."""
    ga_service = client.get_service("GoogleAdsService")
    results = []

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            row_dict = {}
            # Convert protobuf to dict
            for field in row._pb.DESCRIPTOR.fields:
                try:
                    value = getattr(row, field.name)
                    if hasattr(value, '_pb'):
                        # Nested message
                        for subfield in value._pb.DESCRIPTOR.fields:
                            try:
                                subvalue = getattr(value, subfield.name)
                                if hasattr(subvalue, 'value'):
                                    row_dict[f"{field.name}.{subfield.name}"] = subvalue.value
                                elif isinstance(subvalue, (int, float, str, bool)):
                                    row_dict[f"{field.name}.{subfield.name}"] = subvalue
                            except:
                                pass
                    elif hasattr(value, 'value'):
                        row_dict[field.name] = value.value
                    elif isinstance(value, (int, float, str, bool)):
                        row_dict[field.name] = value
                except:
                    pass
            if row_dict:
                results.append(row_dict)
    except Exception as e:
        print(f"  Query error: {e}")

    return results


def get_date_range(days):
    """Get date range string for GAQL."""
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=days-1)
    return f"'{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'"


class AccountAudit:
    """Comprehensive single-account audit."""

    def __init__(self, customer_id, account_name, days=30):
        self.customer_id = customer_id
        self.account_name = account_name
        self.days = days
        self.client = get_ads_client()
        self.data = {}
        self.insights = {}
        self.charts = {}

    def run(self):
        """Execute all audit sections."""
        print(f"\n{'='*60}")
        print(f"GOOGLE ADS ACCOUNT AUDIT v1.0")
        print(f"{'='*60}")
        print(f"Account: {self.account_name}")
        print(f"CID: {self.customer_id}")
        print(f"Period: {self.days} days")
        print(f"{'='*60}\n")

        # Run all sections
        self._section_1_overview()
        self._section_2_pacing()
        self._section_3_campaigns()
        self._section_4_keywords()
        self._section_5_search_terms()
        self._section_6_conversion_health()
        self._section_7_conversion_standards()
        self._section_8_bid_management()
        self._section_9_asset_performance()
        self._section_10_creative_compliance()
        self._section_11_pmax_settings()
        self._section_12_quality_score()
        self._section_13_negative_keywords()

        # Generate report
        self._generate_charts()
        report_path = self._generate_html_report()

        print(f"\n{'='*60}")
        print(f"AUDIT COMPLETE")
        print(f"{'='*60}")
        print(f"Report: {report_path}")
        print(f"Open: file://{report_path}")

        return report_path

    def _section_1_overview(self):
        """Section 1: Account Overview & Period Comparison."""
        print("Section 1: Account Overview...")

        date_range = get_date_range(self.days)
        prev_end = datetime.now() - timedelta(days=self.days+1)
        prev_start = prev_end - timedelta(days=self.days-1)
        prev_range = f"'{prev_start.strftime('%Y-%m-%d')}' AND '{prev_end.strftime('%Y-%m-%d')}'"

        # Current period
        query = f"""
            SELECT
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date BETWEEN {date_range}
        """
        current = run_gaql(self.client, self.customer_id, query)

        # Previous period
        query_prev = f"""
            SELECT
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date BETWEEN {prev_range}
        """
        previous = run_gaql(self.client, self.customer_id, query_prev)

        # Aggregate
        def aggregate(data):
            return {
                'cost': sum(r.get('metrics.cost_micros', 0) for r in data) / 1_000_000,
                'clicks': sum(r.get('metrics.clicks', 0) for r in data),
                'impressions': sum(r.get('metrics.impressions', 0) for r in data),
                'conversions': sum(r.get('metrics.conversions', 0) for r in data),
                'value': sum(r.get('metrics.conversions_value', 0) for r in data),
            }

        curr = aggregate(current)
        prev = aggregate(previous)

        # Calculate derived metrics
        curr['ctr'] = (curr['clicks'] / curr['impressions'] * 100) if curr['impressions'] > 0 else 0
        curr['cpa'] = curr['cost'] / curr['conversions'] if curr['conversions'] > 0 else 0
        curr['roas'] = curr['value'] / curr['cost'] if curr['cost'] > 0 else 0

        prev['ctr'] = (prev['clicks'] / prev['impressions'] * 100) if prev['impressions'] > 0 else 0
        prev['cpa'] = prev['cost'] / prev['conversions'] if prev['conversions'] > 0 else 0
        prev['roas'] = prev['value'] / prev['cost'] if prev['cost'] > 0 else 0

        # Calculate deltas
        def calc_delta(current, previous):
            if previous > 0:
                return ((current - previous) / previous) * 100
            return None

        self.insights['overview'] = {
            'current': curr,
            'previous': prev,
            'deltas': {
                'cost': calc_delta(curr['cost'], prev['cost']),
                'clicks': calc_delta(curr['clicks'], prev['clicks']),
                'impressions': calc_delta(curr['impressions'], prev['impressions']),
                'conversions': calc_delta(curr['conversions'], prev['conversions']),
                'value': calc_delta(curr['value'], prev['value']),
                'ctr': calc_delta(curr['ctr'], prev['ctr']),
                'cpa': calc_delta(curr['cpa'], prev['cpa']),
                'roas': calc_delta(curr['roas'], prev['roas']),
            }
        }

        print(f"  Spend: ${curr['cost']:,.2f} ({self._format_delta(self.insights['overview']['deltas']['cost'])})")
        print(f"  Conversions: {curr['conversions']:,.0f} ({self._format_delta(self.insights['overview']['deltas']['conversions'])})")

    def _section_2_pacing(self):
        """Section 2: Budget Pacing & Forecasting."""
        print("Section 2: Budget Pacing...")

        # Get daily data for forecasting
        date_range = get_date_range(self.days)
        query = f"""
            SELECT
                segments.date,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date BETWEEN {date_range}
        """
        daily = run_gaql(self.client, self.customer_id, query)

        # Aggregate by date
        daily_data = defaultdict(lambda: {'cost': 0, 'conversions': 0, 'value': 0})
        for row in daily:
            date = row.get('segments.date', '')
            daily_data[date]['cost'] += row.get('metrics.cost_micros', 0) / 1_000_000
            daily_data[date]['conversions'] += row.get('metrics.conversions', 0)
            daily_data[date]['value'] += row.get('metrics.conversions_value', 0)

        # Convert to sorted list
        daily_list = [{'date': k, **v} for k, v in sorted(daily_data.items())]
        self.data['daily'] = daily_list

        if daily_list:
            total_cost = sum(d['cost'] for d in daily_list)
            avg_daily = total_cost / len(daily_list) if daily_list else 0

            # Forecast
            now = datetime.now()
            days_in_month = 30  # Simplified
            days_remaining = max(1, days_in_month - now.day)

            self.insights['pacing'] = {
                'daily_avg': avg_daily,
                'total_spend': total_cost,
                'forecast_30d': avg_daily * 30,
                'forecast_month_remaining': avg_daily * days_remaining,
                'days_remaining': days_remaining,
            }

            print(f"  Daily Avg: ${avg_daily:,.2f}")
            print(f"  30-Day Forecast: ${avg_daily * 30:,.2f}")
        else:
            self.insights['pacing'] = {'daily_avg': 0, 'total_spend': 0, 'forecast_30d': 0}

    def _section_3_campaigns(self):
        """Section 3: Campaign Performance."""
        print("Section 3: Campaign Performance...")

        date_range = get_date_range(self.days)
        query = f"""
            SELECT
                campaign.name,
                campaign.status,
                campaign.bidding_strategy_type,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date BETWEEN {date_range}
                AND campaign.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
        """
        campaigns = run_gaql(self.client, self.customer_id, query)

        # Process campaigns
        campaign_data = []
        for row in campaigns:
            cost = row.get('metrics.cost_micros', 0) / 1_000_000
            value = row.get('metrics.conversions_value', 0)
            campaign_data.append({
                'name': row.get('campaign.name', 'Unknown'),
                'status': row.get('campaign.status', 'Unknown'),
                'bidding': row.get('campaign.bidding_strategy_type', 'Unknown'),
                'cost': cost,
                'clicks': row.get('metrics.clicks', 0),
                'impressions': row.get('metrics.impressions', 0),
                'conversions': row.get('metrics.conversions', 0),
                'value': value,
                'roas': value / cost if cost > 0 else 0,
            })

        self.data['campaigns'] = campaign_data
        self.insights['campaigns'] = {
            'count': len([c for c in campaign_data if c['cost'] > 0]),
            'total_cost': sum(c['cost'] for c in campaign_data),
        }

        print(f"  Active campaigns: {self.insights['campaigns']['count']}")

    def _section_4_keywords(self):
        """Section 4: Keyword Analysis."""
        print("Section 4: Keyword Analysis...")

        date_range = get_date_range(self.days)
        query = f"""
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                campaign.name,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.conversions,
                metrics.conversions_value
            FROM keyword_view
            WHERE segments.date BETWEEN {date_range}
                AND ad_group_criterion.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
            LIMIT 100
        """
        keywords = run_gaql(self.client, self.customer_id, query)

        # Calculate CPC and find issues
        keyword_data = []
        zero_conv_cost = 0
        zero_conv_count = 0

        for row in keywords:
            cost = row.get('metrics.cost_micros', 0) / 1_000_000
            clicks = row.get('metrics.clicks', 0)
            conversions = row.get('metrics.conversions', 0)
            cpc = cost / clicks if clicks > 0 else 0

            keyword_data.append({
                'keyword': row.get('ad_group_criterion.keyword.text', ''),
                'match_type': row.get('ad_group_criterion.keyword.match_type', ''),
                'campaign': row.get('campaign.name', ''),
                'cost': cost,
                'clicks': clicks,
                'impressions': row.get('metrics.impressions', 0),
                'conversions': conversions,
                'cpc': cpc,
            })

            if conversions == 0 and cost > 0:
                zero_conv_cost += cost
                zero_conv_count += 1

        self.data['keywords'] = keyword_data

        # Highest CPC
        if keyword_data:
            highest_cpc = max(keyword_data, key=lambda x: x['cpc'])
            self.insights['keywords'] = {
                'highest_cpc': highest_cpc['cpc'],
                'highest_cpc_keyword': highest_cpc['keyword'],
                'zero_conv_cost': zero_conv_cost,
                'zero_conv_count': zero_conv_count,
            }
            print(f"  Highest CPC: ${highest_cpc['cpc']:.2f} ({highest_cpc['keyword'][:30]})")
            print(f"  Zero-conv keywords: {zero_conv_count} (${zero_conv_cost:,.2f} wasted)")
        else:
            self.insights['keywords'] = {'highest_cpc': 0, 'zero_conv_cost': 0, 'zero_conv_count': 0}

    def _section_5_search_terms(self):
        """Section 5: Search Term Analysis."""
        print("Section 5: Search Term Analysis...")

        date_range = get_date_range(self.days)
        query = f"""
            SELECT
                search_term_view.search_term,
                campaign.name,
                metrics.cost_micros,
                metrics.clicks,
                metrics.conversions
            FROM search_term_view
            WHERE segments.date BETWEEN {date_range}
                AND metrics.cost_micros > 0
            ORDER BY metrics.cost_micros DESC
            LIMIT 100
        """
        search_terms = run_gaql(self.client, self.customer_id, query)

        # Find zero-conversion terms
        zero_conv_terms = []
        total_zero_cost = 0

        for row in search_terms:
            cost = row.get('metrics.cost_micros', 0) / 1_000_000
            conversions = row.get('metrics.conversions', 0)

            if conversions == 0 and cost > 0:
                zero_conv_terms.append({
                    'term': row.get('search_term_view.search_term', ''),
                    'campaign': row.get('campaign.name', ''),
                    'cost': cost,
                    'clicks': row.get('metrics.clicks', 0),
                })
                total_zero_cost += cost

        # Sort by cost
        zero_conv_terms.sort(key=lambda x: x['cost'], reverse=True)

        self.data['search_terms'] = zero_conv_terms[:10]
        self.insights['search_terms'] = {
            'zero_conv_count': len(zero_conv_terms),
            'zero_conv_cost': total_zero_cost,
        }

        print(f"  Zero-conv terms: {len(zero_conv_terms)} (${total_zero_cost:,.2f} wasted)")

    def _section_6_conversion_health(self):
        """Section 6: Conversion Tracking Health."""
        print("Section 6: Conversion Tracking Health...")

        # Get conversion actions
        query = """
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.type,
                conversion_action.status
            FROM conversion_action
            WHERE conversion_action.status != 'REMOVED'
        """
        conv_actions = run_gaql(self.client, self.customer_id, query)

        # Get recent conversion performance
        date_range = get_date_range(90)
        query_perf = f"""
            SELECT
                segments.conversion_action_name,
                segments.date,
                metrics.conversions
            FROM campaign
            WHERE segments.date BETWEEN {date_range}
                AND metrics.conversions > 0
        """
        conv_perf = run_gaql(self.client, self.customer_id, query_perf)

        # Find last conversion date per action
        last_dates = {}
        for row in conv_perf:
            action = row.get('segments.conversion_action_name', '')
            date = row.get('segments.date', '')
            if action and date:
                if action not in last_dates or date > last_dates[action]:
                    last_dates[action] = date

        # Categorize health
        today = datetime.now().date()
        healthy = []
        warning = []
        stale = []
        no_data = []

        for action in conv_actions:
            name = action.get('conversion_action.name', '')
            if name in last_dates:
                last_date = datetime.strptime(last_dates[name], '%Y-%m-%d').date()
                days_ago = (today - last_date).days

                if days_ago <= 14:
                    healthy.append(name)
                elif days_ago <= 30:
                    warning.append({'name': name, 'days': days_ago})
                else:
                    stale.append({'name': name, 'days': days_ago})
            else:
                no_data.append(name)

        self.insights['conversion_health'] = {
            'total': len(conv_actions),
            'healthy': len(healthy),
            'warning': warning,
            'stale': stale,
            'no_data': no_data,
        }

        print(f"  Total actions: {len(conv_actions)}")
        print(f"  Healthy: {len(healthy)}, Warning: {len(warning)}, Stale: {len(stale)}, No data: {len(no_data)}")

    def _section_7_conversion_standards(self):
        """Section 7: PM Conversion Standardization."""
        print("Section 7: Conversion Standards (PM)...")

        # PM Standard conversions
        pm_standards = ['Apply Now', 'Contact', 'Schedule a Tour', 'Virtual Tour']

        query = """
            SELECT
                conversion_action.name,
                conversion_action.type,
                conversion_action.category
            FROM conversion_action
            WHERE conversion_action.status = 'ENABLED'
        """
        conv_actions = run_gaql(self.client, self.customer_id, query)

        # Check which standards are present
        existing_names = [a.get('conversion_action.name', '') for a in conv_actions]

        present = []
        missing = []

        for std in pm_standards:
            if any(std.lower() in name.lower() for name in existing_names):
                present.append(std)
            else:
                missing.append(std)

        self.insights['conversion_standards'] = {
            'present': present,
            'missing': missing,
            'all_present': len(missing) == 0,
        }

        print(f"  PM Standards: {len(present)}/4 present")
        if missing:
            print(f"  Missing: {', '.join(missing)}")

    def _section_8_bid_management(self):
        """Section 8: Bid Management & Impression Share."""
        print("Section 8: Bid Management...")

        date_range = get_date_range(self.days)
        query = f"""
            SELECT
                campaign.name,
                campaign.bidding_strategy_type,
                metrics.search_impression_share,
                metrics.search_budget_lost_impression_share,
                metrics.search_rank_lost_impression_share
            FROM campaign
            WHERE segments.date BETWEEN {date_range}
                AND campaign.advertising_channel_type = 'SEARCH'
                AND campaign.status = 'ENABLED'
        """
        campaigns = run_gaql(self.client, self.customer_id, query)

        # Aggregate IS metrics
        is_data = []
        for row in campaigns:
            search_is = row.get('metrics.search_impression_share', 0)
            budget_lost = row.get('metrics.search_budget_lost_impression_share', 0)
            rank_lost = row.get('metrics.search_rank_lost_impression_share', 0)

            if search_is or budget_lost or rank_lost:
                is_data.append({
                    'campaign': row.get('campaign.name', ''),
                    'bidding': row.get('campaign.bidding_strategy_type', ''),
                    'search_is': search_is * 100 if search_is else 0,
                    'budget_lost': budget_lost * 100 if budget_lost else 0,
                    'rank_lost': rank_lost * 100 if rank_lost else 0,
                })

        self.data['impression_share'] = is_data

        # Diagnose
        if is_data:
            avg_is = sum(d['search_is'] for d in is_data) / len(is_data)
            avg_budget_lost = sum(d['budget_lost'] for d in is_data) / len(is_data)
            avg_rank_lost = sum(d['rank_lost'] for d in is_data) / len(is_data)

            # Diagnosis logic
            if avg_budget_lost > 30:
                diagnosis = "Budget constraint - consider budget increase"
            elif avg_rank_lost > 60 and avg_budget_lost < 10:
                diagnosis = "Quality/relevance issues - review ad relevance"
            elif avg_is > 80:
                diagnosis = "Good coverage - capturing most available demand"
            else:
                diagnosis = "Mixed constraint - monitor performance"

            self.insights['bid_management'] = {
                'avg_search_is': avg_is,
                'avg_budget_lost': avg_budget_lost,
                'avg_rank_lost': avg_rank_lost,
                'diagnosis': diagnosis,
            }

            print(f"  Avg Search IS: {avg_is:.1f}%")
            print(f"  Diagnosis: {diagnosis}")
        else:
            self.insights['bid_management'] = {'diagnosis': 'No Search campaigns found'}

    def _section_9_asset_performance(self):
        """Section 9: Ad/Asset Performance."""
        print("Section 9: Asset Performance...")

        date_range = get_date_range(self.days)
        query = f"""
            SELECT
                asset.text_asset.text,
                ad_group_ad_asset_view.performance_label,
                campaign.name
            FROM ad_group_ad_asset_view
            WHERE segments.date BETWEEN {date_range}
        """
        assets = run_gaql(self.client, self.customer_id, query)

        # Count by performance label (2=GOOD, 3=BEST, 6=LOW)
        best = []
        good = []
        low = []

        for row in assets:
            label = row.get('ad_group_ad_asset_view.performance_label', 0)
            text = row.get('asset.text_asset.text', '')
            campaign = row.get('campaign.name', '')

            if label in [3, 4]:  # BEST or EXCELLENT
                best.append({'text': text, 'campaign': campaign})
            elif label == 2:  # GOOD
                good.append({'text': text, 'campaign': campaign})
            elif label == 6:  # LOW
                low.append({'text': text, 'campaign': campaign})

        self.insights['assets'] = {
            'best': len(best),
            'good': len(good),
            'low': len(low),
            'best_list': best[:5],
            'low_list': low[:5],
        }

        print(f"  BEST: {len(best)}, GOOD: {len(good)}, LOW: {len(low)}")

    def _section_10_creative_compliance(self):
        """Section 10: Creative Compliance (Ads Checker Integration)."""
        print("Section 10: Creative Compliance...")

        # Run existing ads checker logic inline (simplified)
        # In production, could call ads_checker_audit.py

        date_range = get_date_range(self.days)

        # Check for DKI
        query_ads = f"""
            SELECT
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.policy_summary.approval_status,
                campaign.name
            FROM ad_group_ad
            WHERE ad_group_ad.status = 'ENABLED'
        """
        ads = run_gaql(self.client, self.customer_id, query_ads)

        dki_count = 0
        disapproved = 0

        for row in ads:
            # Check for DKI pattern
            headlines = str(row.get('ad_group_ad.ad.responsive_search_ad.headlines', ''))
            descriptions = str(row.get('ad_group_ad.ad.responsive_search_ad.descriptions', ''))

            if '{keyword:' in headlines.lower() or '{keyword:' in descriptions.lower():
                dki_count += 1

            # Check approval status
            if row.get('ad_group_ad.policy_summary.approval_status') == 'DISAPPROVED':
                disapproved += 1

        # Check for Google AI assets
        query_ai = """
            SELECT
                asset.id,
                asset.source
            FROM asset
            WHERE asset.source = 'AUTOMATICALLY_CREATED'
        """
        ai_assets = run_gaql(self.client, self.customer_id, query_ai)

        self.insights['creative'] = {
            'dki_count': dki_count,
            'disapproved': disapproved,
            'ai_assets': len(ai_assets),
            'issues': dki_count + disapproved + (1 if ai_assets else 0),
        }

        if dki_count > 0:
            print(f"  DKI found: {dki_count} ads")
        if disapproved > 0:
            print(f"  Disapproved: {disapproved} ads")
        if ai_assets:
            print(f"  AI assets: {len(ai_assets)}")
        if self.insights['creative']['issues'] == 0:
            print(f"  No issues found")

    def _section_11_pmax_settings(self):
        """Section 11: PMAX Asset Automation Settings."""
        print("Section 11: PMAX Settings...")

        query = """
            SELECT
                campaign.name,
                campaign.advertising_channel_type
            FROM campaign
            WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
                AND campaign.status = 'ENABLED'
        """
        pmax_campaigns = run_gaql(self.client, self.customer_id, query)

        self.insights['pmax'] = {
            'campaign_count': len(pmax_campaigns),
            'note': 'Run audit_pmax_asset_automation.py for detailed settings check'
        }

        print(f"  PMAX campaigns: {len(pmax_campaigns)}")
        if pmax_campaigns:
            print(f"  Note: Run standalone PMAX audit for detailed settings")

    def _section_12_quality_score(self):
        """Section 12: Quality Score Distribution."""
        print("Section 12: Quality Score...")

        query = """
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.quality_info.quality_score,
                ad_group_criterion.quality_info.creative_quality_score,
                ad_group_criterion.quality_info.post_click_quality_score,
                ad_group_criterion.quality_info.search_predicted_ctr
            FROM keyword_view
            WHERE ad_group_criterion.status = 'ENABLED'
                AND ad_group_criterion.quality_info.quality_score IS NOT NULL
        """
        keywords = run_gaql(self.client, self.customer_id, query)

        # Distribution
        qs_dist = defaultdict(int)
        low_qs = []

        for row in keywords:
            qs = row.get('ad_group_criterion.quality_info.quality_score', 0)
            if qs:
                qs_dist[qs] += 1
                if qs < 5:
                    low_qs.append({
                        'keyword': row.get('ad_group_criterion.keyword.text', ''),
                        'qs': qs,
                    })

        self.data['quality_score'] = dict(qs_dist)
        self.insights['quality_score'] = {
            'distribution': dict(qs_dist),
            'low_qs_count': len(low_qs),
            'low_qs_list': low_qs[:10],
            'total_with_qs': sum(qs_dist.values()),
        }

        print(f"  Keywords with QS: {self.insights['quality_score']['total_with_qs']}")
        print(f"  Low QS (<5): {len(low_qs)}")

    def _section_13_negative_keywords(self):
        """Section 13: Negative Keywords Coverage."""
        print("Section 13: Negative Keywords...")

        query = """
            SELECT
                campaign.name,
                campaign_criterion.keyword.text,
                campaign_criterion.keyword.match_type
            FROM campaign_criterion
            WHERE campaign_criterion.type = 'KEYWORD'
                AND campaign_criterion.negative = TRUE
        """
        negatives = run_gaql(self.client, self.customer_id, query)

        # Count per campaign
        neg_by_campaign = defaultdict(int)
        for row in negatives:
            campaign = row.get('campaign.name', 'Unknown')
            neg_by_campaign[campaign] += 1

        # Find campaigns with low negatives (<10)
        low_neg_campaigns = [c for c, count in neg_by_campaign.items() if count < 10]

        self.insights['negative_keywords'] = {
            'total': len(negatives),
            'campaigns_with_negatives': len(neg_by_campaign),
            'low_negative_campaigns': low_neg_campaigns,
            'avg_per_campaign': len(negatives) / max(1, len(neg_by_campaign)),
        }

        print(f"  Total negatives: {len(negatives)}")
        print(f"  Campaigns with <10 negatives: {len(low_neg_campaigns)}")

    def _format_delta(self, value):
        """Format delta value with arrow."""
        if value is None:
            return '-'
        arrow = '↑' if value >= 0 else '↓'
        color = SUCCESS_COLOR if value >= 0 else DANGER_COLOR
        return f"{arrow} {abs(value):.1f}%"

    def _generate_charts(self):
        """Generate matplotlib charts."""
        print("\nGenerating charts...")

        # Daily trend chart
        if self.data.get('daily'):
            try:
                fig, ax = plt.subplots(figsize=(10, 4))
                dates = [d['date'] for d in self.data['daily']]
                costs = [d['cost'] for d in self.data['daily']]
                convs = [d['conversions'] for d in self.data['daily']]

                ax.bar(dates, costs, color=PRIMARY_COLOR, alpha=0.7, label='Cost')
                ax2 = ax.twinx()
                ax2.plot(dates, convs, color=SECONDARY_COLOR, linewidth=2, marker='o', markersize=4, label='Conversions')

                ax.set_xlabel('Date')
                ax.set_ylabel('Cost ($)', color=PRIMARY_COLOR)
                ax2.set_ylabel('Conversions', color=SECONDARY_COLOR)
                ax.set_title('Daily Performance')

                plt.xticks(rotation=45)
                plt.tight_layout()

                # Save to buffer
                import io
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100, facecolor='white')
                buf.seek(0)
                self.charts['daily'] = base64.b64encode(buf.read()).decode()
                plt.close()
                print("  - Daily trend chart")
            except Exception as e:
                print(f"  - Daily chart failed: {e}")

        # Campaign spend chart
        if self.data.get('campaigns'):
            try:
                top_campaigns = sorted(self.data['campaigns'], key=lambda x: x['cost'], reverse=True)[:10]
                if top_campaigns:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    names = [c['name'][:25] for c in top_campaigns]
                    costs = [c['cost'] for c in top_campaigns]

                    bars = ax.barh(names, costs, color=PRIMARY_COLOR)
                    ax.set_xlabel('Cost ($)')
                    ax.set_title('Top Campaigns by Spend')
                    ax.invert_yaxis()

                    for bar, val in zip(bars, costs):
                        ax.text(bar.get_width() + max(costs) * 0.01, bar.get_y() + bar.get_height()/2,
                               f'${val:,.0f}', va='center', fontsize=9)

                    plt.tight_layout()

                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=100, facecolor='white')
                    buf.seek(0)
                    self.charts['campaigns'] = base64.b64encode(buf.read()).decode()
                    plt.close()
                    print("  - Campaign spend chart")
            except Exception as e:
                print(f"  - Campaign chart failed: {e}")

    def _generate_html_report(self):
        """Generate HTML report."""
        print("\nGenerating HTML report...")

        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        safe_name = self.account_name.replace(' ', '-').replace('/', '-')[:30]
        filename = f"{safe_name}-audit-{timestamp}.html"
        output_path = OUTPUT_DIR / filename

        # Build HTML
        overview = self.insights.get('overview', {})
        current = overview.get('current', {})
        deltas = overview.get('deltas', {})

        def format_delta_html(value, invert=False):
            if value is None:
                return ''
            is_good = value >= 0 if not invert else value <= 0
            color = SUCCESS_COLOR if is_good else DANGER_COLOR
            arrow = '↑' if value >= 0 else '↓'
            return f'<span style="color:{color};font-weight:bold">{arrow} {abs(value):.1f}%</span>'

        # Zero conv search terms table
        search_terms_html = ''
        for term in self.data.get('search_terms', [])[:5]:
            search_terms_html += f"""<tr>
                <td>{term['term'][:40]}</td>
                <td>{term['campaign'][:25]}</td>
                <td>${term['cost']:.2f}</td>
                <td>{term['clicks']}</td>
            </tr>"""

        # Low QS keywords table
        low_qs_html = ''
        for kw in self.insights.get('quality_score', {}).get('low_qs_list', [])[:5]:
            low_qs_html += f"""<tr>
                <td>{kw['keyword'][:40]}</td>
                <td style="color:{DANGER_COLOR}">{kw['qs']}</td>
            </tr>"""

        # Conversion health
        conv_health = self.insights.get('conversion_health', {})
        warning_html = ''
        for w in conv_health.get('warning', [])[:5]:
            warning_html += f"<li>{w['name']} - {w['days']} days ago</li>"
        stale_html = ''
        for s in conv_health.get('stale', [])[:5]:
            stale_html += f"<li style='color:{DANGER_COLOR}'>{s['name']} - {s['days']} days ago</li>"

        # Asset performance
        assets = self.insights.get('assets', {})
        low_assets_html = ''
        for a in assets.get('low_list', []):
            low_assets_html += f"<tr><td style='color:{DANGER_COLOR}'>{a['text'][:50]}</td><td>{a['campaign'][:25]}</td></tr>"
        best_assets_html = ''
        for a in assets.get('best_list', []):
            best_assets_html += f"<tr><td style='color:{SUCCESS_COLOR}'>{a['text'][:50]}</td><td>{a['campaign'][:25]}</td></tr>"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Account Audit - {self.account_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h1 {{ color: {PRIMARY_COLOR}; margin: 0 0 10px 0; }}
        .container {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #333;
            border-bottom: 3px solid {PRIMARY_COLOR};
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card label {{
            display: block;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: {PRIMARY_COLOR};
            margin: 5px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .alert {{
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .alert-danger {{ background: #f8d7da; border-left: 4px solid {DANGER_COLOR}; }}
        .alert-warning {{ background: #fff3cd; border-left: 4px solid {WARNING_COLOR}; }}
        .alert-success {{ background: #d4edda; border-left: 4px solid {SUCCESS_COLOR}; }}
        .alert-info {{ background: #d1ecf1; border-left: 4px solid {PRIMARY_COLOR}; }}
        img.chart {{ max-width: 100%; border-radius: 8px; margin: 15px 0; }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-success {{ background: {SUCCESS_COLOR}; color: white; }}
        .badge-warning {{ background: {WARNING_COLOR}; color: black; }}
        .badge-danger {{ background: {DANGER_COLOR}; color: white; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Account Audit - {self.account_name}</h1>
        <p style="margin:5px 0;color:#666;">
            <strong>CID:</strong> {self.customer_id} |
            <strong>Period:</strong> {self.days} days |
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </p>
        <p style="margin:5px 0;color:#666;font-size:12px;">
            Google Ads Account Audit v1.0
        </p>
    </div>

    <!-- Section 1: Overview -->
    <div class="container">
        <h2>1. Account Overview</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <label>Spend</label>
                <div class="value">${current.get('cost', 0):,.0f}</div>
                {format_delta_html(deltas.get('cost'))}
            </div>
            <div class="summary-card">
                <label>Conversions</label>
                <div class="value">{current.get('conversions', 0):,.0f}</div>
                {format_delta_html(deltas.get('conversions'))}
            </div>
            <div class="summary-card">
                <label>Conv Value</label>
                <div class="value">${current.get('value', 0):,.0f}</div>
                {format_delta_html(deltas.get('value'))}
            </div>
            <div class="summary-card">
                <label>CPA</label>
                <div class="value">${current.get('cpa', 0):,.2f}</div>
                {format_delta_html(deltas.get('cpa'), invert=True)}
            </div>
        </div>
    </div>

    <!-- Section 2: Pacing -->
    <div class="container">
        <h2>2. Budget Pacing & Forecast</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <label>Daily Average</label>
                <div class="value">${self.insights.get('pacing', {}).get('daily_avg', 0):,.2f}</div>
            </div>
            <div class="summary-card">
                <label>30-Day Forecast</label>
                <div class="value">${self.insights.get('pacing', {}).get('forecast_30d', 0):,.0f}</div>
            </div>
            <div class="summary-card">
                <label>Month Remaining</label>
                <div class="value">${self.insights.get('pacing', {}).get('forecast_month_remaining', 0):,.0f}</div>
            </div>
            <div class="summary-card">
                <label>Days Left</label>
                <div class="value">{self.insights.get('pacing', {}).get('days_remaining', 0)}</div>
            </div>
        </div>
        {'<img class="chart" src="data:image/png;base64,' + self.charts.get('daily', '') + '">' if 'daily' in self.charts else ''}
    </div>

    <!-- Section 3: Campaigns -->
    <div class="container">
        <h2>3. Campaign Performance</h2>
        <p>Active campaigns: <strong>{self.insights.get('campaigns', {}).get('count', 0)}</strong></p>
        {'<img class="chart" src="data:image/png;base64,' + self.charts.get('campaigns', '') + '">' if 'campaigns' in self.charts else ''}
    </div>

    <!-- Section 4: Keywords -->
    <div class="container">
        <h2>4. Keyword Analysis</h2>
        <div class="summary-grid" style="grid-template-columns: repeat(2, 1fr);">
            <div class="summary-card">
                <label>Highest CPC</label>
                <div class="value" style="color:{DANGER_COLOR}">${self.insights.get('keywords', {}).get('highest_cpc', 0):.2f}</div>
                <small>{self.insights.get('keywords', {}).get('highest_cpc_keyword', '')[:30]}</small>
            </div>
            <div class="summary-card">
                <label>Zero-Conv Keywords</label>
                <div class="value" style="color:{WARNING_COLOR}">{self.insights.get('keywords', {}).get('zero_conv_count', 0)}</div>
                <small>${self.insights.get('keywords', {}).get('zero_conv_cost', 0):,.2f} wasted</small>
            </div>
        </div>
    </div>

    <!-- Section 5: Search Terms -->
    <div class="container">
        <h2>5. Search Term Analysis</h2>
        <div class="alert alert-warning">
            <strong>{self.insights.get('search_terms', {}).get('zero_conv_count', 0)}</strong> search terms
            with <strong>${self.insights.get('search_terms', {}).get('zero_conv_cost', 0):,.2f}</strong> spend and zero conversions
        </div>
        <h4>Top Zero-Conversion Terms</h4>
        <table>
            <tr><th>Search Term</th><th>Campaign</th><th>Cost</th><th>Clicks</th></tr>
            {search_terms_html if search_terms_html else '<tr><td colspan="4">No data</td></tr>'}
        </table>
    </div>

    <!-- Section 6: Conversion Health -->
    <div class="container">
        <h2>6. Conversion Tracking Health</h2>
        <div class="summary-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="summary-card" style="background:#d4edda;">
                <label>Healthy</label>
                <div class="value" style="color:{SUCCESS_COLOR}">{conv_health.get('healthy', 0)}</div>
            </div>
            <div class="summary-card" style="background:#fff3cd;">
                <label>Warning</label>
                <div class="value" style="color:{WARNING_COLOR}">{len(conv_health.get('warning', []))}</div>
            </div>
            <div class="summary-card" style="background:#f8d7da;">
                <label>Stale</label>
                <div class="value" style="color:{DANGER_COLOR}">{len(conv_health.get('stale', []))}</div>
            </div>
            <div class="summary-card" style="background:#e2e3e5;">
                <label>No Data</label>
                <div class="value">{len(conv_health.get('no_data', []))}</div>
            </div>
        </div>
        {f'<h4>Warning (15-30 days)</h4><ul>{warning_html}</ul>' if warning_html else ''}
        {f'<h4>Stale (30+ days)</h4><ul>{stale_html}</ul>' if stale_html else ''}
    </div>

    <!-- Section 7: PM Conversion Standards -->
    <div class="container">
        <h2>7. PM Conversion Standards</h2>
        {f'<div class="alert alert-success">All 4 PM standard conversions present</div>' if self.insights.get('conversion_standards', {}).get('all_present') else ''}
        {f'<div class="alert alert-danger">Missing: {", ".join(self.insights.get("conversion_standards", {}).get("missing", []))}</div>' if self.insights.get('conversion_standards', {}).get('missing') else ''}
        <p><strong>Present:</strong> {', '.join(self.insights.get('conversion_standards', {}).get('present', [])) or 'None'}</p>
    </div>

    <!-- Section 8: Bid Management -->
    <div class="container">
        <h2>8. Bid Management & Impression Share</h2>
        <div class="alert alert-info">
            <strong>Diagnosis:</strong> {self.insights.get('bid_management', {}).get('diagnosis', 'N/A')}
        </div>
        <div class="summary-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="summary-card">
                <label>Search IS</label>
                <div class="value">{self.insights.get('bid_management', {}).get('avg_search_is', 0):.1f}%</div>
            </div>
            <div class="summary-card">
                <label>Budget Lost IS</label>
                <div class="value">{self.insights.get('bid_management', {}).get('avg_budget_lost', 0):.1f}%</div>
            </div>
            <div class="summary-card">
                <label>Rank Lost IS</label>
                <div class="value">{self.insights.get('bid_management', {}).get('avg_rank_lost', 0):.1f}%</div>
            </div>
        </div>
    </div>

    <!-- Section 9: Asset Performance -->
    <div class="container">
        <h2>9. Asset Performance</h2>
        <div class="summary-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="summary-card" style="background:#d4edda;">
                <label>Best</label>
                <div class="value" style="color:{SUCCESS_COLOR}">{assets.get('best', 0)}</div>
            </div>
            <div class="summary-card" style="background:#fff3cd;">
                <label>Good</label>
                <div class="value" style="color:{WARNING_COLOR}">{assets.get('good', 0)}</div>
            </div>
            <div class="summary-card" style="background:#f8d7da;">
                <label>Low</label>
                <div class="value" style="color:{DANGER_COLOR}">{assets.get('low', 0)}</div>
            </div>
        </div>
        {f'<h4 style="color:{DANGER_COLOR}">LOW Performers - Replace These</h4><table><tr><th>Asset</th><th>Campaign</th></tr>{low_assets_html}</table>' if low_assets_html else ''}
        {f'<h4 style="color:{SUCCESS_COLOR}">BEST Performers - Replicate These</h4><table><tr><th>Asset</th><th>Campaign</th></tr>{best_assets_html}</table>' if best_assets_html else ''}
    </div>

    <!-- Section 10: Creative Compliance -->
    <div class="container">
        <h2>10. Creative Compliance</h2>
        {f'<div class="alert alert-danger"><strong>DKI Found:</strong> {self.insights.get("creative", {}).get("dki_count", 0)} ads with Dynamic Keyword Insertion</div>' if self.insights.get('creative', {}).get('dki_count', 0) > 0 else ''}
        {f'<div class="alert alert-danger"><strong>Disapproved:</strong> {self.insights.get("creative", {}).get("disapproved", 0)} ads disapproved</div>' if self.insights.get('creative', {}).get('disapproved', 0) > 0 else ''}
        {f'<div class="alert alert-warning"><strong>AI Assets:</strong> {self.insights.get("creative", {}).get("ai_assets", 0)} auto-created assets detected</div>' if self.insights.get('creative', {}).get('ai_assets', 0) > 0 else ''}
        {f'<div class="alert alert-success">No creative compliance issues found</div>' if self.insights.get('creative', {}).get('issues', 0) == 0 else ''}
        <p><small>Run full Ads Checker audit for detailed creative analysis (10 checks)</small></p>
    </div>

    <!-- Section 11: PMAX Settings -->
    <div class="container">
        <h2>11. PMAX Settings</h2>
        <p>PMAX campaigns found: <strong>{self.insights.get('pmax', {}).get('campaign_count', 0)}</strong></p>
        <p><small>Run standalone PMAX audit (audit_pmax_asset_automation.py) for detailed settings check</small></p>
    </div>

    <!-- Section 12: Quality Score -->
    <div class="container">
        <h2>12. Quality Score</h2>
        <p>Keywords with QS data: <strong>{self.insights.get('quality_score', {}).get('total_with_qs', 0)}</strong></p>
        <p>Low QS (&lt;5): <strong style="color:{DANGER_COLOR}">{self.insights.get('quality_score', {}).get('low_qs_count', 0)}</strong></p>
        {f'<h4>Lowest QS Keywords</h4><table><tr><th>Keyword</th><th>QS</th></tr>{low_qs_html}</table>' if low_qs_html else ''}
    </div>

    <!-- Section 13: Negative Keywords -->
    <div class="container">
        <h2>13. Negative Keywords</h2>
        <div class="summary-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="summary-card">
                <label>Total Negatives</label>
                <div class="value">{self.insights.get('negative_keywords', {}).get('total', 0)}</div>
            </div>
            <div class="summary-card">
                <label>Avg per Campaign</label>
                <div class="value">{self.insights.get('negative_keywords', {}).get('avg_per_campaign', 0):.1f}</div>
            </div>
            <div class="summary-card">
                <label>Campaigns &lt;10</label>
                <div class="value" style="color:{WARNING_COLOR}">{len(self.insights.get('negative_keywords', {}).get('low_negative_campaigns', []))}</div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Google Ads Account Audit v1.0</p>
        <p>Generated by <a href="https://github.com/fourteenwm/ppc-ai-skills">ppc-ai-skills</a></p>
    </div>
</body>
</html>
"""

        # Write file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  Report saved: {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description='Google Ads Single-Account Audit')
    parser.add_argument('account', nargs='?', help='Account name from accounts.md')
    parser.add_argument('--cid', help='Customer ID (if not using account name)')
    parser.add_argument('--days', type=int, default=30, help='Analysis period in days (default: 30)')
    args = parser.parse_args()

    if not args.account and not args.cid:
        print("Error: Provide account name or --cid")
        print("Usage: python account_audit.py \"Account Name\"")
        print("       python account_audit.py --cid 1234567890")
        sys.exit(1)

    # Resolve account
    customer_id, account_name = resolve_account(args.account, args.cid)

    # Run audit
    audit = AccountAudit(customer_id, account_name, args.days)
    report_path = audit.run()

    # Open in browser (optional)
    print(f"\nTo view: file://{report_path}")


if __name__ == '__main__':
    main()
