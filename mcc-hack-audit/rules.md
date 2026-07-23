# Rules — triaging link findings, the escalation default, and cadence

Decision logic around an identification instrument. The script maps who has
manager access; every judgment — which EXTERNAL rows matter, when a finding
becomes an incident, what "trusted" costs — is the operator's.
[`examples.md`](examples.md) has worked reads;
[`references/scan-contract.md`](references/scan-contract.md) has the exact
walk/classification/output mechanics.

## Invariants (never break these)

- **Identification, not judgment.** The scan never auto-clears a link. Every
  non-internal manager is a finding until *you* classify it — even the agency
  you've worked with for ten years, even the link older than the account
  manager's tenure. Age and familiarity are context, not clearance.
- **No allowlist by design.** `--trusted-cids` reduces a partner's
  *visibility* (drops them from the SUSPICIOUS CSV), not their *attack
  surface*. Every trusted entry is a place a determined attacker could
  target; re-audit trusted CIDs on the same cadence as everything else.
- **Read-only.** The script removes nothing, notifies nobody. Link removal is
  a manual UI action; client communication is your call. Anything you *do*
  in response to findings goes through
  [`mutation-safety`](../mutation-safety/) discipline.
- **Absence is not evidence.** An account missing from the CSV errored out of
  the scan (contract, error isolation) — it was not certified manager-free.

## Triage order — reading a scan

1. **HOSTILE rows first.** Any HOSTILE row = incident mode: that's a CID you
   already convicted, actively linked. The console warning block lists each
   pair; the label column carries your own context note.
2. **PENDING links to unknown MCCs next.** A PENDING link is a live invite
   awaiting acceptance — someone is trying to get in *right now*, and you're
   reading it pre-breach. Find out who initiated it before it's accepted.
   This is the highest-value catch the scan makes.
3. **EXTERNAL, newest first.** The SUSPICIOUS CSV already sorts by
   `manager_link_id` descending — the API's only chronology (contract,
   limitation 2). Recent links are hottest: fraud is fresh, forgotten
   agencies are old.
4. **REFUSED / CANCELED / INACTIVE rows last — but read them.** Not live
   access; attempt history. A pattern of refused invites from the same
   unknown CID across accounts is probing, and probing that predates a
   successful PENDING/ACTIVE link elsewhere is a campaign.

For each EXTERNAL row, one of three verdicts:

| Verdict | Looks like | Action |
|---|---|---|
| **Expected** | Former agency, franchisor/parent org, platform partner — a name (via UI lookup) and a link age that match known history | Record it (or `--trusted-cids` it, accepting the visibility cost) |
| **Unknown** | No name resolvable, no client memory of it, or a recent link nobody authorized | Investigate now — escalation path below |
| **Hostile** | Unknown + post-link mutation activity, or matches incident intel | Incident mode: revoke, rotate, record in `hostile.json` |

**What a suspicious link looks like** (the profile, all four together =
act immediately): high `manager_link_id` (recent) + `ACTIVE` or `PENDING` +
no one can name the MCC + change activity on the account after the link
appeared.

## The escalation default (when you can't identify an EXTERNAL manager)

Treat unidentifiable as potentially hostile — never as "probably fine":

1. **Check post-link activity:** [`change-history-checker`](../change-history-checker/)
   on the affected accounts — bulk change signatures after the link date are
   the confirmation signal (inside 30 days, its `change_event` pattern also
   names the actor).
2. **Put a name on the CID:** Google Ads UI → the account's Access and
   security page (the API can't do this — contract, limitation 1). Ask the
   client what they authorized; compromised client-side admin credentials are
   the known entry path.
3. **If unauthorized: revoke in the UI** (manual by design), have the client
   rotate their admin credentials, then add the CID to your `hostile.json`
   with a context note — future scans classify it HOSTILE automatically.
4. **Never mark a CID TRUSTED to make a row go away.** Suppression is for
   verified partners you consciously accept, not for findings you're tired
   of seeing.

## Cadence and the manual watchdog

- **Quarterly** baseline scan; **immediately** on any client report of
  unexpected campaign activity; **after onboarding** (verify existing access)
  and **after offboarding** (verify your own removal).
- The script has no watchdog mode. The manual pattern: run on a cadence, keep
  the datestamped CSVs (different days accumulate — contract), and diff the
  newest two full CSVs. New rows = new links since last scan; that diff is
  your link-acceptance alarm, since the API never records acceptance events
  (contract, limitation 3).

## Sharing hostile-MCC intelligence

Community threat-intel helps everyone, but share a CID only when all three
hold: (1) you *confirmed* hostility (mutations made, link rejected, client
confirmed compromise — not just "unknown"); (2) the CID is no longer your
active threat (publishing tips off attackers still in your tree); (3) you're
comfortable with the CID being public. There is no central registry — you
maintain your own `hostile.json` and share excerpts deliberately.

## False-alarm table

| Signal | Likely cause | Verify by | Then |
|---|---|---|---|
| Huge INTERNAL count | Every account links its parent MCC — a 1,000-account tree yields 1,000+ INTERNAL rows | Breakdown block math | Normal; INTERNAL volume carries no signal |
| An account missing from the CSV | Its link query errored (usually CANCELED/CLOSED) — absent, not clean | Console error count; account status in the walk | Re-run if you need that account specifically; never read absence as "no managers" |
| Error count ≈ your canceled/closed count | The expected error population (contract) | Your own account-status inventory | Healthy signature |
| Error count far above canceled count | Auth/permission problem, not account statuses — the console label ("CANCELED/CLOSED… expected") is an assumption | Re-run one failing account solo and read the actual error | Fix credentials/access before trusting the scan's coverage |
| `RESOURCE_EXHAUSTED` errors | Worker count above the API's tolerance | Errors clear at lower parallelism | `--workers 10` re-run — throttling, not intrusion |
| Your own MCC appears as `account_cid` with an EXTERNAL manager | The walk includes your root — that row is who manages YOUR tree | Whether your org has a parent/franchisor MCC | Expected if a parent exists; investigate like any EXTERNAL if not |
| A known partner shows EXTERNAL | By design — there is no auto-trust | — | Verify, then record or `--trusted-cids` (accepting the visibility trade) |
| A trusted partner vanished from SUSPICIOUS | That's literally what `--trusted-cids` does | Full CSV still shows the row as TRUSTED | Expected; re-audit on cadence |
| REFUSED links in the output | No status filter — attempt records included deliberately | `link_status` column | Not live access; read for probing patterns (triage order 4) |
| `WARNING: HOSTILE MCCs ACTIVELY LINKED` after you already revoked | The block prints for every HOSTILE-classified row regardless of `link_status` (contract) | The row's `link_status` — CANCELED/REFUSED = remediated history | Classification says *convicted CID seen*; only `link_status` says *live access* |

## Escalation default, restated

Unknown + linked = investigate now, not next quarter. The scan's whole value
is that the UI shows manager access one account at a time while attackers
work portfolio-wide; when a row you can't explain survives the triage table,
the next hour belongs to the escalation path, not to the rest of the CSV.
