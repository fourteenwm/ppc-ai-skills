# RSA Bulk Edit

Find-and-replace text across RSA ads in one or more Google Ads accounts, outputting results to a Google Sheet in Google Ads Editor-ready format for review and import.

**The pain point:** A client rebrands, a spelling convention changes, or an old customizer needs replacing across dozens of accounts. Doing find-and-replace ad by ad in the Google Ads UI doesn't scale. This skill queries all RSA headlines, descriptions, and paths, applies your text replacement, and outputs a sheet you can paste directly into Google Ads Editor.

---

## What's Inside

- Find-and-replace across all RSA headlines (1-15), descriptions (1-4), and path fields
- Single account or multi-account batch processing
- Google Ads Editor-ready output: one row per ad with all 15 headlines, 4 descriptions, paths, and final URL
- "Has Match" column for quick filtering to only affected ads
- Dry-run mode for previewing matches without writing to sheet
- Case-insensitive search by default with optional case-sensitive flag
- Custom tab naming for organized review

---

## Installation

```bash
mkdir -p .claude/skills/rsa-bulk-edit/scripts
curl -o .claude/skills/rsa-bulk-edit/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-bulk-edit/SKILL.md
curl -o .claude/skills/rsa-bulk-edit/scripts/rsa_bulk_edit.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-bulk-edit/scripts/rsa_bulk_edit.py
```

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` at project root) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one
- The `--sheet-id` output step reuses that same `google-ads.yaml` OAuth token — its refresh token needs the `spreadsheets` scope, which the setup skill's generator grants by default (token predates that? re-run the generator once)
- Python with `google-ads`, `gspread`, `google-auth`, and `pyyaml` packages

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
