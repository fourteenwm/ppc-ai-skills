# SQR Upload

Uploads approved negative keywords from a Google Sheet "Uploader" tab to shared negative keyword lists via the Google Ads API, with mandatory dry-run preview and two-step mutation approval.

**The pain point:** After classifying hundreds of search queries as off-brand, you still need to add them as negatives to the right shared keyword lists in the right accounts. Doing this manually in the Google Ads UI — one keyword at a time, across multiple accounts — takes hours. This skill reads the approved list from your sheet, groups by account, previews the changes, and uploads them all in one approved batch.

---

## What's Inside

- Reads pending keywords from Google Sheet "Uploader" tab (Query, CID, Neg List ID)
- Groups keywords by account and shared negative keyword list
- Dry-run preview showing exactly what will be uploaded, with mutation guard approval code
- Two-step execution: preview first, then execute only after explicit user approval with code
- Adds keywords as PHRASE match negatives to shared keyword lists via SharedCriterionService
- Stamps "X" in the sheet for successfully uploaded rows
- Profile-locked: must select credentials before running

---

## Installation

```bash
mkdir -p .claude/skills/sqr-upload
curl -o .claude/skills/sqr-upload/SKILL.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/sqr-upload/SKILL.md
```

---

## Prerequisites

- Google Ads API credentials (YAML config) with write access to shared keyword lists
- Google Sheets API credentials with read/write access
- Python with `google-ads`, `google-auth`, and `google-api-python-client` packages
- The `mutation-safety` skill (for the two-step approval protocol)

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 118 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
