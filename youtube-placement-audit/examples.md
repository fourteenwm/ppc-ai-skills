# Worked Examples — YouTube Placement Audit

Three reads, all synthetic data (accounts, channels, and numbers are
invented; CIDs are documentation placeholders). Rules referenced are in
[rules.md](rules.md); mechanics in
[`references/audit-contract.md`](references/audit-contract.md).

---

## Example 1 — Routine monthly run on an auto-repair MCC

Twelve accounts, full audit with `--force`. The load-bearing console
pieces (middle accounts elided):

```
======================================================================
YOUTUBE PLACEMENT BRAND SAFETY AUDIT
======================================================================
Date:       2026-07-31 09:14
MCC:        1234567890
Date Range: Last 30 days
Output:     Sheet <SHEET_ID>
Mode:       FORCE (skip confirmation)
======================================================================

Fetching accounts...
  Found 12 accounts

Processing accounts...

[1/12] Brightwell Tire & Brake (1234567891)
      No YouTube placements

[2/12] Gearline Auto Group (2345678901)
      Found 412 YouTube placements
      [!] Flagged 178 placements
```

…ten more accounts, then the results block:

```
======================================================================
YOUTUBE PLACEMENT AUDIT RESULTS
======================================================================
Total flagged: 493
  Keyword flags: 371
  Non-English:   122

Top 5 keyword flags by impressions:
    482113 | Kids content: 'toy'       | Happy Toy Parade
    391402 | Kids content: 'cartoon'   | Cartoon Craze Compilations
    287960 | Kids content: 'toy'       | Toyota Tundra Owners Club
    201554 | Gaming content: 'gaming'  | GameStorm Live Highlights
    166208 | Spam/Clickbait: 'prank'   | Ultimate Prank Wars

Top 5 non-English by impressions:
    198234 | Мастер Ремонт Авто
    112876 | 面白い動画チャンネル
     88012 | ремонт квартир своими руками
     71430 | ألعاب الأطفال
     55987 | 어린이 만화 채널

Writing to Google Sheet...
  Wrote 371 rows to 'Bad - YouTube'
  Wrote 122 rows to 'Bad - YouTube - NEA'

Sheet: https://docs.google.com/spreadsheets/d/<SHEET_ID>

AUDIT COMPLETE
```

**The read (rules.md triage order):** Run Dates fresh on both tabs.
Coverage sane — Brightwell's empty result is fine (display-only account,
no video-serving campaigns). Then the keyword tab, top down:

- The two top kids channels are exactly what they look like: negate.
- Row three is the trap: **"Toyota Tundra Owners Club" is flagged
  `Kids content: 'toy'` — a substring artifact.** For an auto-repair
  client, a truck-owners channel is plausibly *good* inventory. Kept, not
  negated (rules: when NOT to negate, row 1).
- `GameStorm Live Highlights` → the gaming judgment: local auto repair,
  no gaming angle — negate.

**Extractor pass:**

```
--- Keyword-flagged ---
Reading flagged videos from audit sheets...
  Bad - YouTube: 371 rows
Total unique videos: 214

  Looking up channels for 214 videos...
  Batch 5/5 (203 resolved)
  Resolved 203 videos
  (11 not found - deleted/private)
  89 unique channels

  Channels to Negate: 89 channels
  Wrote 89 channels
```

The NEA job resolves 44 more channels. **Final exclusion list = 89 + 44
extracted channels *plus the 12 `YOUTUBE_CHANNEL` rows sitting in the Bad
tabs* — channel-type placements never flow through the extractor (rules
triage step 5).** 145 channel exclusions, applied in Editor, minus the
Toyota club.

---

## Example 2 — The account that reads clean but isn't

August run, same MCC. Account 7 prints:

```
[7/12] Halstead Transmission (3456789012)
      No YouTube placements
```

Last month Halstead returned 340 placements, and accounts 6 and 8 — same
campaign mix — return hundreds today. That pattern is the
**silent-swallow trap** (contract): all three placement queries are
individually wrapped in bare exception handlers, so a permissions or API
failure prints nothing and looks identical to a clean account.

**The resolution:** isolate and separate "no placements" from "no
access" —

1. Re-run just this account: `--filter "Halstead" --test`. Still empty.
2. Run any simple query against the same CID with
   [google-ads-query](../google-ads-query/) — it does NOT swallow
   errors. It returns `USER_PERMISSION_DENIED`: access to Halstead was
   dropped during a login cleanup. The audit "found nothing" because it
   couldn't look.

Access restored, re-run — 297 placements, 41 flagged. The portfolio
summary was wrong until the quietest line in the console got challenged.

**Same run, second catch:** this month produced keyword flags but **zero
NEA rows** — the write skips the empty tab *including its clear*
(contract), so `Bad - YouTube - NEA` still shows July 3 in `Run Date`.
Negating from that tab today would act on month-old data. Skipped until
next month's run refreshes it.

---

## Example 3 — The judgment calls: gaming conversions and the language boundary

**Scene A — the flagged row with conversions.** In Gearline's Demand Gen
rows: `GameStorm Live Highlights`, 8,900 impressions, 41 clicks, $63.20
cost — and 3 conversions. Rules say investigate before negating
(when-NOT-to-negate, row 4). The channel is general gaming-stream
highlights, no automotive crossover; 3 conversions on 8,900 impressions
at this client's usual lead quality smells like accidental taps on a
mobile overlay. Negated. The counter-case matters though: were this a
client selling gaming chairs, that row would be *kept* — the category
table's whole point is that "Gaming content" is a judgment row, not a
verdict.

**Scene B — the channel the audit can never flag.** Scrolling Gearline's
raw placements: `Taller El Rayo` — Spanish-language car-repair tutorials,
22,000 impressions, never flagged. Correct behavior, not a miss: the NEA
check reads **scripts, not languages** (contract), and Spanish is Latin
script. Gearline's service area is English-only, so the operator extends
`FLAGGED_KEYWORDS` per SKILL.md § Customization:

```python
'mecánico': 'Non-English (Spanish)',
'taller de': 'Non-English (Spanish)',
```

— accented and multi-word terms chosen deliberately: a bare `taller`
would substring-match English ("taller than…"), the rules' customization
warning. One placement note: rows flagged by custom keywords land in
`Bad - YouTube` — the NEA tab is reserved for the built-in script
detection's exact reason string (contract). Verified with
`--test --limit 3` before the next full run. A bilingual shop two markets
over would make the opposite call and keep that inventory.
