---
name: google-ads-samples
description: Reference library of official Google Ads API code samples. Auto-invoke when building NEW Google Ads scripts, agents, or functionality (campaigns, mutations, reporting, account management). Helps find relevant examples in /examples/ folder before writing custom code. Improves efficiency by starting from proven patterns rather than guessing API implementation.
allowed-tools: [Read, Grep, Glob]
---

# Google Ads Code Samples Reference Skill

**Purpose:** Automatically reference official Google Ads API examples when building new functionality.

**Type:** Reference/efficiency skill (auto-invokes when implementing new Google Ads features)

**Status:** Production - Use before writing new Google Ads code

---

## Setup (One-Time)

This skill assumes you have a local checkout of Google's official Python samples repo at `./google-ads-python/`:

```bash
git clone https://github.com/googleads/google-ads-python.git
```

All paths below reference `google-ads-python/examples/` relative to the project root. Adjust paths if you cloned elsewhere.

---

## When to Auto-Invoke This Skill

Claude should invoke this skill **automatically** whenever user asks to:

1. **Build new Google Ads scripts** (not ad-hoc queries)
2. **Implement new API operations** (mutations, campaign creation, etc.)
3. **Work with unfamiliar Google Ads API features**
4. **Create agents that interact with Google Ads API**
5. **Solve Google Ads API errors** (check examples for proper patterns)

**Examples that trigger this skill:**
- "Create a script to add Performance Max campaigns"
- "Build an agent to manage account-level negative keywords"
- "How do I batch create campaigns using the API?"
- "Write a script to update bidding strategies across accounts"
- "I'm getting an error with customer negative criteria - how should this work?"

**DO NOT trigger for:**
- Simple GAQL reporting queries (we already have patterns)
- Reading existing scripts
- Running existing workflows

---

## Available Example Categories

We have **39 official Google example scripts** organized by category:

### Account Management (10 scripts)
Located: `google-ads-python/examples/account_management/`

Key examples:
- `get_account_hierarchy.py` - MCC account traversal
- `list_accessible_customers.py` - Available customer accounts
- `get_change_summary.py` - Account change history
- `get_change_details.py` - Detailed change tracking
- `create_customer.py` - Creating new accounts
- `link_manager_to_client.py` - MCC linking
- `invite_user_with_access_role.py` - User management
- `update_user_access.py` - Permissions management
- `verify_advertiser_identity.py` - Identity verification

### Campaign Management (8 scripts)
Located: `google-ads-python/examples/campaign_management/`

Key examples:
- `add_complete_campaigns_using_batch_job.py` - **Bulk campaign creation**
- `get_all_disapproved_ads.py` - Ad disapproval checking
- `validate_ad.py` - Pre-flight ad validation
- `add_campaign_labels.py` - Label management
- `create_experiment.py` - Campaign experiments
- `set_ad_parameters.py` - Dynamic ad parameters
- `update_campaign_criterion_bid_modifier.py` - Bid adjustments

### Advanced Operations (19 scripts)
Located: `google-ads-python/examples/advanced_operations/`

Key examples:
- `add_performance_max_campaign.py` - **Performance Max setup**
- `add_responsive_search_ad_full.py` - **RSAs with all assets**
- `add_smart_campaign.py` - Smart campaigns
- `add_demand_gen_campaign.py` - Demand Gen campaigns
- `add_dynamic_search_ads.py` - DSA campaigns
- `create_and_attach_shared_keyword_set.py` - **Shared negative keywords**
- `find_and_remove_criteria_from_shared_set.py` - **Shared set management**
- `use_portfolio_bidding_strategy.py` - Portfolio bidding
- `use_cross_account_bidding_strategy.py` - Cross-account bidding
- `add_ad_group_bid_modifier.py` - Bid modifiers
- `get_ad_group_bid_modifiers.py` - Reading bid modifiers

### Reporting (2 scripts)
Located: `google-ads-python/examples/reporting/`

Key examples:
- `parallel_report_download.py` - Efficient multi-account reporting

---

## Instructions

When invoked, follow this protocol:

### Step 1: Understand the User's Request

Parse what the user is asking for:
- **Operation type:** Create, read, update, delete?
- **Resource type:** Campaign, ad group, keyword, account setting?
- **Scale:** Single account or MCC-wide?
- **Special features:** Batch operations, mutations, reporting?

### Step 2: Search Examples for Relevant Patterns

Based on the operation, search the appropriate category:

```bash
# For campaign/ad creation
ls google-ads-python/examples/campaign_management/
ls google-ads-python/examples/advanced_operations/

# For mutations and shared sets
grep -r "SharedSet" google-ads-python/examples/
grep -r "mutate" google-ads-python/examples/

# For account operations
ls google-ads-python/examples/account_management/

# For specific keywords
grep -r "CustomerNegativeCriterion" google-ads-python/examples/
grep -r "PerformanceMax" google-ads-python/examples/
```

### Step 3: Read the Most Relevant Example(s)

Once you identify 1-3 relevant examples, read them:

```python
# Read the full example to understand the pattern
Read: google-ads-python/examples/advanced_operations/add_performance_max_campaign.py
```

Pay attention to:
- **Service client usage** (e.g., `client.get_service("CampaignService")`)
- **Operation structure** (e.g., `CampaignOperation`)
- **Field access patterns** (e.g., `operation.create.name = "..."`)
- **Error handling** patterns
- **Batch operation** techniques
- **Resource name** construction

### Step 4: Explain the Pattern to the User

Before writing code, tell the user:

```
I found a relevant example: add_performance_max_campaign.py

This shows the pattern for:
- Creating asset groups
- Setting up audience signals
- Linking to merchant center
- Batch creating all resources in one call

I'll adapt this pattern to your specific needs...
```

### Step 5: Adapt the Pattern

Create new code based on the example, but adapted for:
- User's specific account/campaign structure
- Our authentication (google-ads.yaml)
- Our safety systems (the mutation-safety skill if mutations)
- Our naming conventions
- Our error handling standards

### Step 6: Reference the Source

In the new script, add a comment:

```python
"""
Create Performance Max campaigns for property management accounts

Based on official example:
google-ads-python/examples/advanced_operations/add_performance_max_campaign.py

Adapted for:
- Example portfolio structure
- mutation-safety approval workflow
- CSV-driven batch creation
"""
```

---

## Example Workflow

**User asks:** "Create a script to add account-level negative keywords to multiple accounts"

**Your process:**

1. **Search for relevant examples:**
   ```bash
   grep -r "negative" google-ads-python/examples/advanced_operations/
   grep -r "CustomerNegativeCriterion" google-ads-python/examples/
   ```

2. **Find:** `create_and_attach_shared_keyword_set.py` (closest match)

3. **Read the example:**
   ```python
   Read: google-ads-python/examples/advanced_operations/create_and_attach_shared_keyword_set.py
   ```

4. **Explain to user:**
   > "I found `create_and_attach_shared_keyword_set.py` which shows how to create shared negative keyword sets. However, for TRUE account-level negatives (that appear in Account Settings), we need `CustomerNegativeCriterionService`, not `SharedSetService`. Let me check if there's a more specific example..."

5. **Search more specifically:**
   ```bash
   grep -r "CustomerNegativeCriterion" google-ads-python/examples/
   ```

6. **If not found:**
   > "The examples don't have a CustomerNegativeCriterion example, but the shared keyword pattern shows the proper structure for mutations. I'll adapt it using CustomerNegativeCriterionService based on the API docs..."

7. **Create the script** using the shared keyword pattern as a template

---

## Benefits of Using This Skill

### Efficiency Gains
- **50-75% faster** for complex operations (proven patterns vs trial/error)
- **25-40% faster** for standard operations (better structure)
- **Higher success rate** on first attempt

### Quality Improvements
- Proper error handling (examples include it)
- Correct service usage (no guessing)
- Best practices built-in (Google's own patterns)
- Fewer API errors (examples are tested)

### Learning Effect
- Each example teaches Google's preferred patterns
- Builds knowledge for future implementations
- Reduces dependency on examples over time

---

## Quick Reference: Example Index

### For Creating Campaigns
- Performance Max: `advanced_operations/add_performance_max_campaign.py`
- Demand Gen: `advanced_operations/add_demand_gen_campaign.py`
- Smart: `advanced_operations/add_smart_campaign.py`
- Dynamic Search: `advanced_operations/add_dynamic_search_ads.py`
- Batch creation: `campaign_management/add_complete_campaigns_using_batch_job.py`

### For Mutations & Updates
- Shared negative keywords: `advanced_operations/create_and_attach_shared_keyword_set.py`
- Campaign labels: `campaign_management/add_campaign_labels.py`
- Bid modifiers: `advanced_operations/add_ad_group_bid_modifier.py`

### For Ads
- RSAs: `advanced_operations/add_responsive_search_ad_full.py`
- Call ads: `advanced_operations/add_call_ad.py`
- Display ads: `advanced_operations/add_display_upload_ad.py`
- Ad validation: `campaign_management/validate_ad.py`
- Disapprovals: `campaign_management/get_all_disapproved_ads.py`

### For Account Management
- Account hierarchy: `account_management/get_account_hierarchy.py`
- List accounts: `account_management/list_accessible_customers.py`
- Change history: `account_management/get_change_summary.py` + `get_change_details.py`
- Create accounts: `account_management/create_customer.py`
- User access: `account_management/invite_user_with_access_role.py`

### For Bidding Strategies
- Portfolio bidding: `advanced_operations/use_portfolio_bidding_strategy.py`
- Cross-account bidding: `advanced_operations/use_cross_account_bidding_strategy.py`

### For Reporting
- Multi-account reports: `reporting/parallel_report_download.py`

---

## When NOT to Use This Skill

Skip this skill when:
- Writing simple GAQL queries (the **gaql-query-patterns** skill covers these)
- Reading/debugging existing scripts
- Running existing agents
- Making minor modifications to working code

---

## Integration with Other Skills

This skill works well with:
- **mutation-safety** - Examples show mutations, its two-step approval wraps them safely
- **fair-housing-compliance** - Examples show targeting, compliance checks constraints
- **client-communication-standards** - Examples gather data, standards format reports

---

## Success Criteria

This skill is successful when:
1. ✅ Relevant example found before writing custom code
2. ✅ Example pattern explained to user
3. ✅ New code adapted from proven pattern
4. ✅ Source example referenced in comments
5. ✅ Time saved vs writing from scratch
6. ✅ Fewer API errors due to proper structure

---

## Related Documentation

- Links to official Google Ads API docs — see [developers.google.com/google-ads/api/docs](https://developers.google.com/google-ads/api/docs)
- [google-ads-python/examples/README.md](../../google-ads-python/examples/README.md) - Safety warnings and usage guide
- GitHub: https://github.com/googleads/google-ads-python
- Samples index: https://developers.google.com/google-ads/api/samples

---

**Created:** 2025-10-28
**Status:** Production - Auto-invoke for new Google Ads development
**Trigger:** User requests new Google Ads scripts/agents/functionality
