# Worked Examples — PMax Asset Automation

Three real-shaped audit reads. All account names and CIDs are synthetic;
console excerpts match the script's actual output format (80-char `=`
separators, `[OK]`/`[!]` icons, exact summary lines).

---

## Example 1 — Routine single-account audit with a judgment call on video

```bash
python scripts/audit_pmax_asset_automation.py --cid 1234567890 > pmax-audit-before.txt
```

(Redirecting matters: the audit writes nothing to disk, and you'll want this
run as the "before" half of a before/after pair if anything gets fixed.)

```
================================================================================
ACCOUNT: CID 1234567890
CID: 1234567890
================================================================================

  Campaign: Pmax: Brightwell Yards
  Status: ENABLED
  Asset Automation Settings:
    [OK] Auto-created text (headlines/descriptions): OPTED_OUT
    [OK] Final URL expansion: OPTED_OUT
    [OK] Auto-created videos: OPTED_OUT
    [OK] Auto image enhancement (cropping): OPTED_OUT
    [OK] Auto image extraction from URLs: OPTED_OUT
  -> FULLY COMPLIANT (5/5)

  Campaign: Pmax: Brightwell Yards - Grand Opening
  Status: PAUSED
  Asset Automation Settings:
    [OK] Auto-created text (headlines/descriptions): OPTED_OUT
    [!] Final URL expansion: OPTED_IN
    [!] Auto-created videos: OPTED_IN
    [OK] Auto image enhancement (cropping): OPTED_OUT
    [OK] Auto image extraction from URLs: OPTED_OUT
  -> NEEDS ATTENTION (3/5 opted out)

================================================================================
AUDIT SUMMARY
================================================================================
Total accounts audited: 1
Total settings checked: 10
Compliant settings: 8
Non-compliant settings: 2

Accounts needing attention: 1
  - CID 1234567890 (1234567890): 8/10 (80%)
================================================================================
```

**The read.** The flagship campaign is clean. The two `[!]` rows sit on a
**PAUSED** campaign — real findings, but dormant: they bite the day someone
re-enables it, so the deadline is "before re-enable", not "right now"
(rules.md false-alarm table). The `- CID 1234567890 (1234567890)` redundancy
is the display rule for `--cid` runs, not a glitch.

**The judgment call.** `Auto-created videos: OPTED_IN` on this account is
the priority of the two: the client runs professionally produced brand
video, and OPTED_IN means Google may serve trimmed/remixed variants of
creative that was approved frame-by-frame. URL expansion gets the
check-before-flipping treatment (rules.md — it's the setting most often ON
deliberately). The escalation ladder, cheapest check first: the
[change-history-checker](../change-history-checker/) pull shows both
settings untouched since campaign creation — the seasonal campaign was
built in the UI with Google's defaults and never configured. Default-config
case: fix both via the mutation pattern (SKILL.md § fix) under
[mutation-safety](../mutation-safety/) before the campaign re-enables, then
re-audit into `pmax-audit-after.txt`.

---

## Example 2 — The audit that says "fully compliant" and isn't

Three accounts, quarterly compliance pass:

```bash
python scripts/audit_pmax_asset_automation.py --cids "1234567890,2345678901,3456789012"
```

```
================================================================================
PERFORMANCE MAX ASSET AUTOMATION AUDIT
================================================================================
Accounts to audit: 3
================================================================================

================================================================================
ACCOUNT: CID 1234567890
CID: 1234567890
================================================================================

  Campaign: Pmax: Brightwell Yards
  Status: ENABLED
  Asset Automation Settings:
    [OK] Auto-created text (headlines/descriptions): OPTED_OUT
    [OK] Final URL expansion: OPTED_OUT
    [OK] Auto-created videos: OPTED_OUT
    [OK] Auto image enhancement (cropping): OPTED_OUT
    [OK] Auto image extraction from URLs: OPTED_OUT
  -> FULLY COMPLIANT (5/5)

  ERROR querying account 2345678901: User doesn't have permission to access customer.
================================================================================
ACCOUNT: CID 3456789012
CID: 3456789012
================================================================================

  Campaign: Pmax: Tolliver Station
  Status: ENABLED
  Asset Automation Settings:
    [OK] Auto-created text (headlines/descriptions): OPTED_OUT
    [OK] Final URL expansion: OPTED_OUT
    [OK] Auto-created videos: OPTED_OUT
    [OK] Auto image enhancement (cropping): OPTED_OUT
    [OK] Auto image extraction from URLs: OPTED_OUT
  -> FULLY COMPLIANT (5/5)

================================================================================
AUDIT SUMMARY
================================================================================
Total accounts audited: 3
Total settings checked: 10
Compliant settings: 10
Non-compliant settings: 0

All accounts fully compliant!
================================================================================
```

**The read — triage order, error lines first.** `All accounts fully
compliant!` is false: account `2345678901` was never audited. It threw a
permission error, got skipped, and left exactly one trace — the ERROR line
between the account blocks. The summary still counts it
(`Total accounts audited: 3`) while the arithmetic quietly disagrees: three
accounts should not produce 10 settings from two account blocks. The
compliant-message logic only knows about accounts that *were* audited.

**The move:** fix access first (that permission message usually means the
yaml's `login_customer_id` isn't the manager of that account), re-run the
failed account alone, and only then write "portfolio compliant" anywhere.
Count sanity — blocks seen vs audited total, settings vs 5×campaigns — is
rules.md triage step 2 for exactly this report shape.

---

## Example 3 — All five ON (and an account that was never in scope)

A new-client baseline audit before taking over management:

```bash
python scripts/audit_pmax_asset_automation.py --cids "1234567891,0987654321"
```

```
================================================================================
ACCOUNT: CID 1234567891
CID: 1234567891
================================================================================

  Campaign: Pmax: Ravenna Heights
  Status: ENABLED
  Asset Automation Settings:
    [!] Auto-created text (headlines/descriptions): OPTED_IN
    [!] Final URL expansion: OPTED_IN
    [!] Auto-created videos: OPTED_IN
    [!] Auto image enhancement (cropping): OPTED_IN
    [!] Auto image extraction from URLs: OPTED_IN
  -> NEEDS ATTENTION (0/5 opted out)

================================================================================
ACCOUNT: CID 0987654321
CID: 0987654321
================================================================================
  No PMAX campaigns found

================================================================================
AUDIT SUMMARY
================================================================================
Total accounts audited: 2
Total settings checked: 5
Compliant settings: 0
Non-compliant settings: 5

Accounts needing attention: 1
  - CID 1234567891 (1234567891): 0/5 (0%)
================================================================================
```

**The read.** A clean 0/5 sweep looks alarming and is usually the *most*
benign finding shape: all-five-ON is Google's default state, and the audit
seeds absent settings to OPTED_IN — so "someone turned everything on" and
"nobody ever opened the Asset automation panel" print identically. On a
just-inherited account, the prior manager building the campaign in the UI
and never touching the panel is the overwhelming favorite. Change history
confirms it (creation event, no setting edits since) — routine setup fix,
no incident narrative needed. Worth knowing which story you're in anyway:
if history DID show a deliberate opt-in by the client's in-house team, this
becomes a coordinate-first conversation (rules.md, when-ON-is-legitimate),
not a silent flip.

**The second account is not a win.** `No PMAX campaigns found` contributes
0/0 — out of scope, not audited-clean. Note it as "no PMax presence" in the
handoff doc, and expect it to enter scope the day someone launches PMax
there (new-campaign cadence, rules.md). The five findings on Ravenna
Heights become the first work item of the engagement: dry-run the fix,
get approval, execute, re-audit next day.
