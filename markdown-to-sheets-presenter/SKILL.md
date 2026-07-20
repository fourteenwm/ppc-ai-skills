---
name: markdown-to-sheets-presenter
description: Transforms markdown reports into professionally formatted Google Sheets for client presentation. Auto-invoke when user wants to make a report presentable, share analysis with clients, convert markdown to Sheets, or export competitive analysis. Triggers include "make this presentable", "create a Google Sheet", "export to sheets", "format for client".
allowed-tools: [Read, Write, Bash, Glob, Grep, WebFetch]
version: "1.0.0"
---

# Markdown to Google Sheets Presenter

## Overview

This skill transforms markdown reports (competitive analysis, ad recon, performance reports) into professionally formatted Google Sheets ready for client presentation.

**Trigger Phrases:**
- "Make this presentable for the client"
- "Create a Google Sheet from this"
- "Export this to Google Sheets"
- "Format this report for sharing"
- "Convert this to a spreadsheet"

## Prerequisites

1. **Credentials:** `google-ads.yaml` at project root — see the [google-ads-api-setup skill](../google-ads-api-setup/) if you don't have one. The script reuses this same file's OAuth credentials for the Sheets API — its refresh token must carry the `spreadsheets` scope, which the setup skill's generator grants by default (token predates that? re-run the generator once)
2. **Python packages:** `pip install google-api-python-client google-auth pyyaml`

## Workflow

### Step 1: Identify Input

When triggered, identify the source:
- If path provided: Use that path directly
- If recent analysis in conversation: Use that content
- If ambiguous: Ask user to specify

### Step 2: Parse Markdown Structure

Analyze the markdown to determine:
- Document title and metadata
- Section hierarchy (H1, H2, H3)
- Tables with headers and data
- Lists (bulleted, numbered, checkbox)
- Scoring data (X/45, percentages, etc.)

### Step 3: Determine Tab Structure

**For Competitive Analysis / Ad Recon Reports:**

| Section | Tab Name | Notes |
|---------|----------|-------|
| Executive Summary | `Summary` | First tab, KPIs |
| Strategic Analysis | `Strategic_Scores` | 15-attribute scoring |
| Tactical Scan | `Tactical_Scores` | 7-attribute flags |
| Gap Identification | `Gaps` | Opportunities list |
| Verified Angles | `Recommendations` | Client-ready angles |
| Per Competitor | `Competitor_[Name]` | If multiple competitors |

**For Performance Reports:**

| Section | Tab Name | Notes |
|---------|----------|-------|
| Overview | `Dashboard` | KPI metrics |
| Campaign Data | `Campaigns` | Main data table |
| Recommendations | `Action_Items` | Next steps |

### Step 4: Apply Formatting

**Color Palette (Professional Blue):**
```
Header Background: #1a73e8 (Google Blue)
Header Text: #ffffff (White)
Subheader Background: #e8f0fe (Light Blue)
Subheader Text: #1a73e8 (Google Blue)
Row Alternating 1: #ffffff (White)
Row Alternating 2: #f8f9fa (Light Gray)
Border Color: #dadce0 (Gray)
Success/Green: #34a853
Warning/Yellow: #fbbc04
Alert/Red: #ea4335
```

**Typography:**
- Headers: Bold, 12pt
- Subheaders: Bold, 11pt
- Data: Regular, 10pt
- Font: Arial (default)

**Conditional Formatting (Auto-Applied):**

| Pattern | Condition | Format |
|---------|-----------|--------|
| Score columns | >= 80% of max | Green background |
| Score columns | 50-79% of max | Yellow background |
| Score columns | < 50% of max | Red background |
| Status | "HIGH" threat | Red background |
| Status | "MEDIUM" threat | Yellow background |
| Status | "LOW" threat | Green background |
| Flags | Contains checkmark | Green text |
| Flags | Contains X | Red text |

### Step 5: Create Google Sheet

Use the create_spreadsheet.py script from your project root (where `google-ads.yaml` lives):

```bash
python .claude/skills/markdown-to-sheets-presenter/scripts/create_spreadsheet.py "Report Name"
```

Pass `--config path/to/google-ads.yaml` if your credentials live elsewhere. The sheet is created in the Drive root of the authorized account — move it into a client folder in Drive afterward if needed. The script returns the spreadsheet ID and URL as JSON; use the ID for the data-population and formatting calls that follow.

**Naming Convention:**
```
[Client Name] - [Report Type] - [YYYY-MM-DD]
Example: "Example Client - Competitive Analysis - 2025-12-16"
```

### Step 6: Return Results

Provide user with:
1. **Clickable Google Sheets link**
2. **Summary of tabs created**
3. **Data rows per tab**

## Output Format

```markdown
## Google Sheet Created

**Sheet Name:** [Name]
**Link:** [URL]

### Tabs Created:
| Tab | Rows | Description |
|-----|------|-------------|
| Summary | 15 | Executive overview with KPIs |
| Strategic_Scores | 20 | 15-attribute competitive scoring |
| ... | ... | ... |

---
*Click the link above to open your Google Sheet.*
```

## Executive Presentation Requirements

When creating CEO/executive presentations:

### NEVER Truncate Text
Ad copy and descriptions are critical - always show full text.

### Column Width
Description columns must be 550+ pixels for full visibility.

### Chart Positioning
Charts must be positioned BELOW all data (row 24+), never overlapping.

## Special Handling

### Large Tables (>100 rows)
- Enable filtering on header row
- Add pagination note

### Scoring Tables
- Apply conditional formatting based on score thresholds
- Right-align numeric columns
- Include score interpretation legend

### Missing Data
- Use "—" for empty cells (not blank)
- Gray out unavailable metrics

### Currency Values
- Apply accounting format
- Right-align

### Percentages
- Apply percentage format
- Right-align

## Error Handling

| Error | Action |
|-------|--------|
| No credentials | Point at the [google-ads-api-setup skill](../google-ads-api-setup/) |
| 403 / PERMISSION_DENIED | Refresh token predates the Sheets scope — re-run the api-setup generator once, paste the new `refresh_token` into `google-ads.yaml` |
| File not found | Ask user to verify path |
| API quota | Suggest waiting or manual copy |
| Parse failure | Fall back to raw text layout |

## Integration

Feeds naturally from other skills' markdown outputs:
- Competitive analysis reports
- Extension audit reports
- Performance assessments
- Search query / keyword analysis summaries

## Maintenance

Update this skill when:
- New report types are added
- Formatting requirements change
- Google Sheets API updates
