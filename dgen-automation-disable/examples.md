# Worked Examples — a clean run, a drift mismatch, and a false compliance

Synthetic accounts, CIDs, and codes throughout. Console excerpts are trimmed
to the decision-bearing lines; formats match what the script prints. Every
example runs the same discipline: dry-run → READ → decide → execute.

---

## Example 1 — The routine one: read, approve, execute, verify

**Setup:** newly onboarded apartment advertiser with one Demand Gen
campaign. Post-onboarding cadence says run the fix.

```
python scripts/fix_dgen_ad_automation.py --cid 1234567890
```

```
DGEN AD AUTOMATION FIX - DRY RUN
================================================================================
Accounts to process: 1
================================================================================

================================================================================
ACCOUNT: Account 1234567890
CID: 1234567890
================================================================================

  Campaign: Fernbrook - DGen - Prospecting
  Ad Group: Lifestyle Imagery
  Ad Type: DEMAND_GEN_MULTI_ASSET_AD
  Settings to change (2):
    - Image design versions (adds design elements): OPTED_IN -> OPTED_OUT
    - Video generation (from images/text): OPTED_IN -> OPTED_OUT

  Campaign: Fernbrook - DGen - Prospecting
  Ad Group: Video - Tours
  Ad Type: DEMAND_GEN_VIDEO_RESPONSIVE_AD
  Settings to change (3):
    - Vertical video conversion: OPTED_IN -> OPTED_OUT
    - Video shortening: OPTED_IN -> OPTED_OUT
    - Landing page screenshot in ads: OPTED_IN -> OPTED_OUT
...
SUMMARY
================================================================================
Accounts with changes needed: 1
Ads to update: 3
Total settings to change: 7

APPROVAL CODE: APPROVE-4C9A21E7
```

(With `--cid`/`--cids` the account prints as `Account {cid}` — display
names resolve on `--all` runs only.)

**The read (rules.md, five checks):** one account as asked, no error lines.
Three ads is right for this campaign. Settings-per-ad reconcile (2+2+3=7 —
the summary counts settings, not ads). The landing-page-preview line is
expected THIS time: the tours ad group was built by the previous agency,
and the client already told us they'd turned every automation on "to try
it". Nothing unexplained → approve.

```
python scripts/fix_dgen_ad_automation.py --cid 1234567890 APPROVE-4C9A21E7 --verify
```

```
Approval code validated. Executing 7 setting changes across 3 ads...

  Updating Account 1234567890 (1234567890)... 3 ad(s) updated
...
Successfully updated: 3 ads

Logged to: logs/mutations_log.jsonl

================================================================================
VERIFICATION: Account 1234567890
================================================================================
  All 3 DGen ads are now compliant
```

The JSONL row is the durable record; the monthly drift re-run goes on the
calendar (new ads will arrive `OPTED_IN`).

---

## Example 2 — The mismatch that was telling you something

**Setup:** Monday's dry-run across three accounts showed 5 ads / 11
settings, code `APPROVE-B83D110F`. Nobody executed until Wednesday.

```
python scripts/fix_dgen_ad_automation.py --cids "1234567890,2345678901,3456789012" APPROVE-B83D110F
```

```
================================================================================
ERROR: Approval code mismatch.
================================================================================
  Provided: APPROVE-B83D110F
  Expected: APPROVE-7E02C4A9

The approval code is derived from the hash of pending mutations.
If ads changed since your dry-run, the code changes.
Re-run without an approval code to see current state and get a fresh code.
```

**The read:** not a bug — the pending set moved (rules, "the mismatch is a
feature"). Wednesday's fresh dry-run shows account `2345678901` grew from 2
ads to 4: two new multi-asset ads, `OPTED_IN` on both settings. **Diff the
diffs:** two new ads on one account midweek = a creative launch landed
Tuesday.

**The decision:** check with whoever launched (rules, when-NOT table — a
just-launched test deserves a heads-up before you flip its settings). The
launcher confirms the new ads should follow house standard (automation
OFF). Execute with Wednesday's code, covering all 7 ads / 15 settings:

```
python scripts/fix_dgen_ad_automation.py --cids "1234567890,2345678901,3456789012" APPROVE-7E02C4A9
```

Had the launcher said "that's a deliberate automation test" — the run would
have waited, and the two accounts NOT in the test would ship as their own
batch with their own dry-run and code.

---

## Example 3 — The false compliance, then the setting nobody remembered enabling

**Setup:** two storage-facility accounts queued for the monthly drift
re-run. The CIDs came off a spreadsheet — one kept its dashes.

```
python scripts/fix_dgen_ad_automation.py --cids "123-456-7890,2345678901"
```

```
  ERROR querying account 123-456-7890: Invalid customer ID '123-456-7890'.
================================================================================
ACCOUNT: Account 2345678901
CID: 2345678901
================================================================================
  No DGen ads need fixing (all compliant or no DGen campaigns)

...
All accounts are compliant - no changes needed!
```

**The read:** the summary is FALSE for the first account — it was never
audited. The script uses CIDs exactly as typed (no dash-stripping,
contract), the dashed CID errored, and an erroring account silently leaves
the run (the false-compliance trap). The error line above the celebration
is the only tell. Fix the CID and re-run:

```
================================================================================
ACCOUNT: Account 1234567890
CID: 1234567890
================================================================================

  Campaign: Kingsbury Storage - DGen - Remarketing
  Ad Group: Facility Video
  Ad Type: DEMAND_GEN_VIDEO_RESPONSIVE_AD
  Settings to change (3):
    - Vertical video conversion: OPTED_IN -> OPTED_OUT
    - Video shortening: OPTED_IN -> OPTED_OUT
    - Landing page screenshot in ads: OPTED_IN -> OPTED_OUT
```

**The second read:** `Landing page screenshot in ads` defaults OFF
(contract, taxonomy) — someone turned it ON. Before overwriting a choice,
name the chooser: `change-history-checker`'s detailed view (inside 30 days)
shows ad changes on this account two weeks ago by a `WEB_CLIENT` actor —
the client's in-house marketer, experimenting. One short conversation
later: the experiment produced nothing, disable it all. THEN dry-run again
for a fresh code (the earlier read is stale by policy — and by hash, if
anything else moved), approve, execute.

The order matters: attribute → coordinate → approve. Flipping first and
asking later un-mutates a human's deliberate config with a batch tool.
