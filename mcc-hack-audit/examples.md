# Worked Examples — reading link scans

Three real decision walks (synthetic tree: login MCC 1234567890, ~214
accounts). Output mechanics are in
[`references/scan-contract.md`](references/scan-contract.md); the judgment
calls are [`rules.md`](rules.md).

## Example 1 — clean quarterly scan (the baseline read)

```
$ python scripts/mcc_hack_audit.py
Logged in via MCC: 1234567890
Workers: 20
Hostile list entries: 0
User-marked trusted CIDs: 0

Walking MCC tree from 1234567890...
  Found 214 total accounts (9 are internal managers)

Scanning 214 accounts with 20 parallel workers...
  [214/214] 41s elapsed  rate: 5.2/s  ETA: 0s  errors: 7

Scan finished in 41s (0.7 min)
Total links found: 231
Errors (expected for CANCELED/CLOSED accounts): 7

CSV outputs:
  All links:       output/mcc_link_scan_20260723.csv
  Suspicious only: output/mcc_link_scan_20260723_SUSPICIOUS.csv

======================================================================
MCC HACK AUDIT — SUMMARY
======================================================================
Total manager links: 231
Errors (CANCELED/CLOSED accounts): 7 (expected)
Distinct managers seen: 12

Classification breakdown:
  HOSTILE    0
  EXTERNAL   3
  TRUSTED    0
  INTERNAL   228
```

The read, in triage order: no HOSTILE rows; the SUSPICIOUS CSV holds three
EXTERNAL rows to verdict. The 228 INTERNAL rows carry no signal (every
account links its parent — rules false-alarm table), and 7 errors against an
inventory of 7 canceled accounts is the healthy signature.

The three EXTERNAL rows, oldest link_ids in the file:

| account_name | manager_cid | manager_link_id | link_status | Verdict |
|---|---|---|---|---|
| Halstead Automotive Group | 0987654321 | 111222333 | ACTIVE | **Expected** — UI lookup names the client's former agency; link predates onboarding; client confirms they never removed it. Recorded, flagged to client for cleanup |
| Halstead Automotive Group | 0987654321 | 111222334 | INACTIVE | Same manager, dead link — attempt/teardown history, no live access |
| Kingsbury District | 2345678901 | 222333444 | ACTIVE | **Expected** — the property's parent-company MCC; known relationship |

All three get names via the UI Account Access page (the API can't name
external MCCs — contract, limitation 1). Nothing gets `--trusted-cids`
treatment yet: first-scan verdicts get *recorded*, and suppression is a
deliberate later choice with a visibility cost (rules invariant).

## Example 2 — the PENDING invite (pre-breach catch → incident)

Next quarter's scan on the same tree: breakdown now shows `EXTERNAL   5`,
and the SUSPICIOUS CSV's top rows (newest link_id first) are new:

| account_name | manager_cid | manager_link_id | link_status | |
|---|---|---|---|---|
| Kestrel Automotive | 3456789012 | 999888777 | **PENDING** | newest link in the file |
| Bridgeline Auto Care | 3456789012 | 999888775 | **REFUSED** | same manager, days earlier |

Triage order puts PENDING-to-unknown second only to HOSTILE: this is a live
invite awaiting acceptance — pre-breach, the scan's highest-value catch. And
the REFUSED row upgrades it: the same unknown CID already tried Bridgeline
and got refused. Two attempts across the book is probing, not noise.

The escalation path, step by step:

1. **Post-link activity:** [`change-history-checker`](../change-history-checker/)
   on Kestrel finds a Saturday bulk cluster — 58 ads added via
   `GOOGLE_ADS_API` under an email nobody recognizes. The attacker isn't
   waiting for the pending manager link; they're already in through
   compromised client-side admin credentials (the known entry path — the
   pending MCC invite is how they make access durable).
2. **Name the CID:** UI lookup returns nothing usable (external MCCs expose
   no name to the API, and this one's UI trail is empty). Client confirms
   nobody authorized it.
3. **Act:** reject the pending invite and revoke in the UI, client rotates
   admin credentials, and `hostile.json` gets its first entry:

```json
{
  "3456789012": "May 2026 incident - invite via compromised client admin login, API mutations on Kestrel"
}
```

The next scan (`--hostile-list hostile.json`) classifies that CID HOSTILE
automatically and prints the warning block:

```
  WARNING: HOSTILE MCCs ACTIVELY LINKED
    3456789012  -> 2345678901 (Kestrel Automotive)
      May 2026 incident - invite via compromised client admin login, API mutations on Kestrel
```

**Read the block against `link_status` before re-declaring an incident:** the
header says "ACTIVELY LINKED," but the script prints it for every
HOSTILE-classified row — including this one, whose status is now CANCELED
after the revocation. Classification says *convicted CID seen*; only
`link_status` says *live access* (rules false-alarm table).

## Example 3 — the account that wasn't in the CSV

Quarterly scan, two quarters on: `errors: 8` where the account inventory
knows only 7 canceled accounts. The full CSV has no Bridgeline Auto Care
rows at all — and the almost-made misread was "no external managers on
Bridgeline anymore."

Wrong on two counts. First, **absence is not evidence** (rules invariant):
an account missing from the CSV errored out of the scan — its links weren't
checked, not cleared. Second, the console's error label
(`CANCELED/CLOSED accounts... (expected)`) is an assumption the code never
verifies (contract) — the arithmetic 8 > 7 says exactly one error is
something else.

The walk output locates it: Bridgeline's `account_status` came back
SUSPENDED (mid-quarter, unrelated billing dispute) — suspended accounts
error on the link query just like canceled ones, but a *suspended* account
with attempt history from example 2 is not an account to lose visibility on.
Its manager links get checked in the UI while the suspension lasts, and the
scan's coverage gap is recorded in the quarter's notes: 213 of 214 accounts
scanned, one checked manually.

The error-count arithmetic — errors vs your own canceled/closed inventory —
is a one-line health check worth running on every scan before trusting
coverage (rules false-alarm table).
