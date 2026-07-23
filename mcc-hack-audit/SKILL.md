---
name: mcc-hack-audit
description: "Portfolio-wide scan of every manager (MCC) that has access to accounts in your Google Ads tree. Built after an MCC link-fraud incident where hostile external MCCs were found linked to client accounts via compromised admin credentials. Classifies each manager link as INTERNAL (in your tree), HOSTILE (known threat), or EXTERNAL (potential exposure — no judgment). Outputs CSV by default with optional Google Sheets upload. Auto-invoke when user says 'mcc hack audit', 'audit mcc links', 'scan for external managers', 'check manager links', 'run mcc link scan', 'find external mccs', or asks who has access to their Google Ads accounts."
allowed-tools: [Bash, Read]
---

# MCC Hack Audit

Owns one workflow: walk your entire Google Ads tree and map every manager
(MCC) with a link into it — then hand the operator a triage-ready answer to
**"which MCCs currently have access to which of my accounts, and which are
outside my own tree?"** Built after a real-world MCC link-fraud incident
where hostile external MCCs gained access to client accounts via compromised
client-side admin credentials.

The triage judgment — which links matter, when a finding becomes an incident,
what "trusted" costs — is [`rules.md`](rules.md). The exact
walk/classification/output mechanics and the hard-won API limitations are
[`references/scan-contract.md`](references/scan-contract.md).

## What It Scans

**Included:**
- Every account under your `login_customer_id` (walks `customer_client`) —
  including your root MCC itself
- Every manager-link relationship on each account
  (`customer_manager_link`) — **all link statuses**, not just active ones: a
  REFUSED or CANCELED link is an attempt record, and attempt records are
  security data
- All account statuses (ENABLED, CANCELED, SUSPENDED, CLOSED) — security-relevant data lives in canceled accounts too

**Output:** every (account, manager) pair, plus a suspicious-only subset
(HOSTILE + EXTERNAL). Full column layout, sort orders, and the Sheets-tab
contract: [`references/scan-contract.md`](references/scan-contract.md).

## Classification Model — No Judgment

Three classifications, defined by objective ownership only (precedence
mechanics in the contract):

| Class | Definition |
|---|---|
| `INTERNAL` | manager_cid is inside your own MCC tree (auto-detected by walking `customer_client`) |
| `HOSTILE` | manager_cid matches an entry in your hostile-MCC list (you populate this) |
| `EXTERNAL` | Anything else. Potential exposure point regardless of name/age/footprint. **Never** auto-classified as legitimate. |

**Critical:** There is no "allowlist" or "trusted partner" concept by design.
Every non-internal manager is EXTERNAL — even an agency you've worked with
for 10 years, even an MCC that's been linked since the account was created.
The point is identification, not pre-clearance. You judge.

If you'd rather not see long-standing trusted MCCs in the suspicious list,
`--trusted-cids` classifies them TRUSTED instead — but that suppresses
visibility, not attack surface (rules invariant: re-audit trusted CIDs on
the same cadence).

## Deliberately does NOT do

- **No link removal** — revocation is a manual UI action, by design.
- **No outreach** — no client emails, no Slack, no notifications. All
  communication is your call.
- **No auto-judgment** — nothing is ever classified "legitimate"; EXTERNAL
  stays EXTERNAL until you verdict it.
- **No watchdog mode** — manual runs only; the cross-day CSV diff is the
  manual watchdog pattern (`rules.md`, cadence).
- **No name resolution for external CIDs** — the API refuses it (contract,
  limitation 1); naming happens in the UI's Account Access page.
- **Single parent MCC per run** — the script reads one `login_customer_id`
  from your YAML; multiple parent MCCs = one run each.

## Prerequisites

- Google Ads API credentials YAML with MCC access (`google-ads.yaml`) — see the [google-ads-api-setup](../google-ads-api-setup/) skill if you don't have one
- Your `login_customer_id` set in the YAML — the script auto-detects your tree from this
- Python packages: `google-ads`, `pyyaml`
- Optional: `gspread` if you want Sheets upload — auth is `gspread.service_account()`: service-account JSON at gspread's default location (`~/.config/gspread/service_account.json`), target sheet shared with the service account's email; or adapt `maybe_upload_to_sheets()` to reuse the `google-ads.yaml` OAuth credentials like this repo's other Sheets-writing skills

## How to Run

```bash
# Default: walks your full tree, writes CSVs to output/
python scripts/mcc_hack_audit.py

# Custom output directory
python scripts/mcc_hack_audit.py --output-dir my-audit-output

# Include Google Sheets upload (requires gspread auth)
python scripts/mcc_hack_audit.py --sheet-id YOUR_SHEET_ID

# Add known-hostile CIDs from a JSON file
python scripts/mcc_hack_audit.py --hostile-list hostile.json

# Mark specific external CIDs as trusted (they'll be classified TRUSTED instead of EXTERNAL)
python scripts/mcc_hack_audit.py --trusted-cids "1234567890,0987654321"

# Tune parallelism (default 20, lower if you hit RESOURCE_EXHAUSTED)
python scripts/mcc_hack_audit.py --workers 10

# Custom credentials path
python scripts/mcc_hack_audit.py --config /path/to/google-ads.yaml
```

**Runtime:** ~2-5 min for a 1,000-account tree at 20 workers. Plan ~10 min
for a 10,000-account tree.

**Hostile list format (`hostile.json`)** — CID → one-line context (the
authoritative shape lives in the contract; this is the run surface):

```json
{
  "1234567890": "label or context for this hostile MCC",
  "0987654321": "another known-bad CID with a one-line note"
}
```

Start empty. Populate as incidents occur — the escalation path in
[`rules.md`](rules.md) tells you when a CID earns an entry, and its
"Sharing hostile-MCC intelligence" section covers when (and when not) to
publish entries beyond your own list.

## After a Run (status leg)

Open `output/mcc_link_scan_YYYYMMDD_SUSPICIOUS.csv` and walk the triage
order in [`rules.md`](rules.md): HOSTILE rows, then PENDING-to-unknown, then
EXTERNAL newest-first, then the attempt records. Datestamped CSVs accumulate
across days — diff the newest two to see link churn (the manual watchdog).
Check every surprise against the false-alarm table before escalating; the
error count vs your canceled-account inventory is the standing coverage
check.

## Files in this skill

| File | Role |
|---|---|
| `SKILL.md` | This file — workflow + routing |
| `rules.md` | Judgment: triage order, escalation default, cadence, threat-intel sharing, false alarms |
| `examples.md` | Three worked reads (clean baseline, the PENDING invite incident, the absent account) |
| `references/scan-contract.md` | Exact walk/classification/output mechanics + API limitations |
| `scripts/mcc_hack_audit.py` | The parallel tree-scan engine |

Runtime artifacts (never committed): `output/*.csv` scans, your
`hostile.json`, your `google-ads.yaml`.

## When to load sibling skills

| Load | When |
|---|---|
| [`change-history-checker`](../change-history-checker/) | A link needs the activity question answered — "what changed after this manager appeared?" This skill maps who has *access*; that one reads what *changed* (and inside 30 days, who changed it) |
| [`mutation-safety`](../mutation-safety/) | Any change you make in response to findings — remediation actions go through its approval discipline |
| [`google-ads-api-setup`](../google-ads-api-setup/) | First run, or any credentials error |
| [`gaql-query-patterns`](../gaql-query-patterns/) | Writing follow-up queries beyond what the scan and the history checker ship |
