# Change History Checker

Query Google Ads account change history up to 90 days back — three times the
30-day window of `change_event`, with the escalation map for everything the
API can't reach.

**The pain point:** Google Ads' `change_event` resource only goes back 30
days, so you can't answer "what did I change in October?" in December. This
skill uses `change_status` instead — 90 days, the API's hard cap — and ships
the query patterns, the window semantics both resources actually enforce
(finite range + `LIMIT` required), and the ladder for the questions counts
can't answer: *who* made a change (`change_event` inside 30 days), and
anything older than 90 days (the web UI's 2-year Change History export).

---

## What's Inside

- Shipped script (`scripts/check_change_history.py`) for querying
  `change_status` across any window inside the 90-day cap
- Filters by resource type (campaigns, keywords, extensions, budgets, ads,
  bid strategies)
- `--detailed` mode showing asset details for extension changes;
  `--list-accounts` for finding CIDs under your MCC
- Groups results by date and resource type for readable summaries
- Operator docs: `rules.md` (routine-vs-investigate reading, the attribution
  ladder, false-alarm table), `examples.md` (three worked reads including a
  bulk-signature investigation), and `references/history-windows.md` (the
  two-resource semantics, API-enforced query rules, resource/status tables,
  and the `change_event` "who did this" pattern)

---

## Installation

```bash
mkdir -p .claude/skills/change-history-checker/scripts .claude/skills/change-history-checker/references
for f in SKILL.md rules.md examples.md; do
  curl -o .claude/skills/change-history-checker/$f \
    https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/change-history-checker/$f
done
curl -o .claude/skills/change-history-checker/references/history-windows.md \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/change-history-checker/references/history-windows.md
curl -o .claude/skills/change-history-checker/scripts/check_change_history.py \
  https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/change-history-checker/scripts/check_change_history.py
```

---

## Prerequisites

- Google Ads API credentials (`google-ads.yaml`, loaded by that literal name
  from the directory you run in) — see
  [google-ads-api-setup](../google-ads-api-setup/) if you don't have one
- Python with `google-ads` and `pyyaml` packages

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage over 110 Google Ads accounts with 85+ specialized skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
