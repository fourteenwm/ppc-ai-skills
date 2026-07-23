# RSA Bulk Edit

Find-and-replace text across RSA ads in one or more Google Ads accounts, outputting results to a Google Sheet in Google Ads Editor-ready format for review and import.

**The pain point:** A client rebrands, a spelling convention changes, or an old customizer needs replacing across dozens of accounts. Doing find-and-replace ad by ad in the Google Ads UI doesn't scale. This skill queries every RSA's headlines and descriptions, applies your literal text replacement, and outputs a sheet you can review and paste directly into Google Ads Editor — paths and final URLs ride along for the import, untouched.

---

## What's Inside

- Find-and-replace across all RSA headlines (1-15) and descriptions (1-4) — literal substring matching, with paths and final URLs carried through for the Editor paste (never edited)
- Single account or multi-account batch processing
- Google Ads Editor-ready output: one row per ad with all 15 headlines, 4 descriptions, paths, and final URL
- "Has Match" column for quick filtering to only affected ads
- Dry-run mode for previewing matches without writing to sheet
- Case-insensitive search by default with optional case-sensitive flag
- Custom tab naming for organized review
- Operator docs: `rules.md` (when bulk is the wrong tool, the pre-paste review checklist, false alarms), `examples.md` (worked reads including substring collateral), `references/edit-contract.md` (exact match/output/paste mechanics)

---

## Installation

```bash
mkdir -p .claude/skills/rsa-bulk-edit/scripts .claude/skills/rsa-bulk-edit/references
curl -o .claude/skills/rsa-bulk-edit/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-bulk-edit/SKILL.md
curl -o .claude/skills/rsa-bulk-edit/rules.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-bulk-edit/rules.md
curl -o .claude/skills/rsa-bulk-edit/examples.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-bulk-edit/examples.md
curl -o .claude/skills/rsa-bulk-edit/references/edit-contract.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-bulk-edit/references/edit-contract.md
curl -o .claude/skills/rsa-bulk-edit/scripts/rsa_bulk_edit.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/rsa-bulk-edit/scripts/rsa_bulk_edit.py
```

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml` at project root) — see [google-ads-api-setup](../google-ads-api-setup/) if you don't have one; run the script from the directory holding it (it loads the file by literal name)
- The `--sheet-id` output step reuses that same `google-ads.yaml` OAuth token — its refresh token needs the `spreadsheets` scope, which the setup skill's generator grants by default (token predates that? re-run the generator once)
- Python with `google-ads`, `gspread`, `google-auth`, and `pyyaml` packages

---

## Before you paste anything

The script validates nothing by design — no length checks, no casing
adaptation. The review checklist in `rules.md` (length audit, casing scan,
collateral read, per-account paste) is the step between the sheet and
Google Ads Editor. `examples.md` shows it catching real problems.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
