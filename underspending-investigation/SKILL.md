---
name: underspending-investigation
description: Investigate Google Ads accounts with significant underspending (pacing variance beyond your portfolio's tolerance). Auto-invoke when user says "investigate [account] underspending", "[account] underspending", "why is [account] underspending", or "diagnose underspend for [account]". Runs a universal investigation script, applies six diagnostic frameworks, and synthesizes a root-cause diagnosis with a budget recommendation (or explicit no-action call). Read-only — no mutations.
allowed-tools: [Read, Bash, Grep, Glob, Skill]
---

# Underspending Investigation

**Purpose:** Investigate why a Google Ads account is underspending and
determine the root cause with actionable, data-backed recommendations — or
an explicit, equally-rigorous no-action call.

**Type:** Read-only investigation skill. Reads campaign, impression share,
and pacing data; never writes to Google Ads.

This skill deliberately does NOT:

- **Mutate anything** — no budget changes, no settings edits. The product is
  a diagnosis and a recommendation; execution happens in your own change
  process, human-approved.
- **Sweep portfolios** — one account per investigation. Callers orchestrate
  parallel runs (see Invocation Patterns).
- **Replace the companion frameworks** — the pacing thresholds, IS decision
  tree, and budget calculation live in their own skills; this skill loads
  and applies them.
- **Read your pacing dashboard or optimization log out of the box** — those
  are bring-your-own data sources with documented extension hooks
  (contract, "Adapting the script").
- **Diagnose Display campaigns via impression share** — Display has no
  Search IS metrics; it gets its own check ([`rules.md`](rules.md), the
  "Bid setting limited" section).

---

## Inputs

- **`{ACCOUNT_NAME}`** — full account name (e.g., `Example Property - Pmax`)
- **`{ADDITIONAL_CONTEXT}`** (optional) — pacing variance or other prior
  context (e.g., `Underspending by 12.5%`)

When invoked via `Task(subagent_type="general-purpose", …)`, the
orchestrator substitutes both values into the prompt.

---

## Load the Frameworks First

**At the start of every investigation — before reading script output — load
the three required companion skills via the Skill tool:**

1. [`portfolio-pacing-rules`](../portfolio-pacing-rules/)
2. [`impression-share-diagnostics`](../impression-share-diagnostics/)
3. [`budget-recommendation-calculator`](../budget-recommendation-calculator/)

All three ship in this repo; the investigation will not work correctly
without them. [`rules.md`](rules.md) § "The framework load-map" states what
each one answers and where the other three (bring-your-own) frameworks plug
in.

---

## Prerequisites

1. **Google Ads API credentials** — `google-ads.yaml` at project root (see
   [`google-ads-api-setup`](../google-ads-api-setup/))
2. **Python packages** — `pip install google-ads pyyaml`
3. **Optional: `accounts.md`** at project root — a name→CID registry so
   investigations can run by account name (format in the script header).
   Without it, the script falls back to walking your MCC.

---

## Investigation Protocol

### STEP 0: Run the Universal Investigation Script

```bash
# By account name (resolved via accounts.md, or by walking the MCC)
python scripts/investigate_underspend.py "{ACCOUNT_NAME}"

# By customer ID
python scripts/investigate_underspend.py --cid 1234567890

# Pace against the contracted monthly budget instead of the daily-budget estimate
python scripts/investigate_underspend.py "{ACCOUNT_NAME}" --monthly-budget 5000
```

The script prints three sections — 7-day campaign spend, impression share
with a per-campaign readout, and month-to-date pacing.
[`references/investigation-contract.md`](references/investigation-contract.md)
defines exactly what each line means (windows, display gates, shared-budget
double-counting, the readout ladder, the sign convention) — read findings
through it, especially before trusting a variance number. Pass
`--monthly-budget` whenever a contracted budget exists.

### Step 1: Recent Optimizations Check

**Data source (yours):** your budget-change log — or
[`change-history-checker`](../change-history-checker/) in this repo, which
answers the same question from the API.

A budget increase **3-7 days old** ends the investigation: diagnosis
"ramp-up period", recommendation "monitor 3-5 days, no action" — stop here.
An increase **7-14 days old**: note it and continue (it should be ramped by
now). The full stop-early ladder, including the ended-by-design check, is in
[`rules.md`](rules.md).

### Step 2: Campaign Spend Pattern Analysis

Filter the STEP 1 campaign list to the campaigns in scope per **your own
account-naming convention** (bring-your-own framework — e.g., a name suffix
marking the account's line). Set aside ended/removed campaigns, note unusual
patterns (paused campaigns with spend, shared-budget rows, disappeared
campaigns — the false-alarm table covers each), and identify the primary
spenders.

### Step 3: Impression Share Analysis (Root Cause)

Apply the [`impression-share-diagnostics`](../impression-share-diagnostics/)
decision tree to the STEP 2 metrics — it separates budget-constrained from
quality-constrained from low-demand, and owns the critical context (Rank
Lost IS is informational, never an optimization target). Check the
performance guardrails from
[`portfolio-pacing-rules`](../portfolio-pacing-rules/) (CPA/ROAS
acceptable?) before any budget conclusion.

**Performance Max caveat:** Pmax campaigns expose no meaningful Search IS
metrics — the script flags them `[i]` and excludes them from Search
averages. Diagnose Pmax via budget utilization % plus performance vs. goal
(STEP 1 data).

### Step 4: Budget Recommendation (Only If Budget-Constrained)

Calculate per
[`budget-recommendation-calculator`](../budget-recommendation-calculator/) —
the conservative close-half-the-gap method under its hard **10% single-change
cap**, with its don't-recommend gates (recent increase, failing CPA/ROAS,
low demand, early month). The no-action verdicts and their exact wording
live in [`rules.md`](rules.md) § "The no-action calls" — a no-action answer
is written with the same rigor as an increase.

### Adaptive Investigation

Stop early, pivot, or add checks (ad schedules, geo targeting, negative
conflicts, disapprovals, the Display "Bid setting limited" check) as the
data directs — the ladder and escalation default are in
[`rules.md`](rules.md). Skip Step 4 entirely unless the diagnosis is
budget-constrained.

---

## Output Format

Return findings in this exact structure:

```
================================================================================
UNDERSPENDING INVESTIGATION: {ACCOUNT_NAME}
================================================================================

INVESTIGATION SUMMARY:
- Account: {Full account name}
- Customer ID: {CID}
- Date: {Current date}
- Investigation time: {How long it took}

================================================================================
ROOT CAUSE DIAGNOSIS
================================================================================

Primary Issue: {Budget Constraint | Quality Issues | Low Demand | Ramp-Up Period | Other}

Evidence:
- Pacing Variance: {−X.X}% ({source; state the sign convention — the script
  prints underspend as negative, dashboards often quote it positive})
- Search Impression Share: XX%
- Budget Lost IS: XX%
- Rank Lost IS: XX%
- CPA: $XX.XX (Goal: $XX.XX) {OK or over}

Explanation:
{2-3 sentences on WHY, citing the framework that made the call}

================================================================================
DETAILED FINDINGS
================================================================================

Step 1: Recent Optimizations
Step 2: Campaign Spend Analysis (filtered per your naming convention)
Step 3: Impression Share Analysis (per the companion decision tree)
{Any additional steps taken}

================================================================================
RECOMMENDATIONS
================================================================================

BUDGET RECOMMENDATION:
{If increasing:}
Increase Monthly Budget: $X,XXX → $X,XXX (+X.X%)
New Daily Budget: $XX.XX/day
Rationale: {variance vs tolerance, Budget Lost IS, performance guardrails,
calculator methodology}
Expected Outcome: {variance path, ramp window}

{If NOT increasing:}
Do NOT Increase Budget
Reason: {ramp-up / low demand / performance failure / artifact — per
rules.md, written as a complete answer with monitoring terms}

MONITORING: {what you're watching, for how long}

Confidence Level: {High | Medium | Low}

================================================================================
```

---

## Success Criteria

1. Three companion skills loaded at start
2. Root cause identified with quotable evidence (script lines + named
   frameworks)
3. Recommendation specific ("$1,000 → $1,065, +6.5%") — or a no-action call
   written as a complete answer
4. WHY explained, not just WHAT
5. Investigation path adapted (stopped early when Step 1 answered it)

Operating notes: be autonomous (don't ask permission between steps), be
data-driven (every conclusion cites script output), be specific.

---

## Invocation Patterns

**Inline (single account, manual):**

> "Use the underspending-investigation skill to investigate
> `Example Property - Pmax`. Pacing variance: 12.5% under."

**Parallel orchestration (morning-briefing pattern):**

The orchestrator launches N parallel
`Task(subagent_type="general-purpose", …)` calls in a single message, each
invoking this skill against one account. Parallelism and per-investigation
context isolation live at the Task layer; the skill runs identically.

---

## Files in This Skill

| File | Role |
|---|---|
| `SKILL.md` | This workflow — protocol, output format, routing |
| `rules.md` | Judgment layer: framework load-map, stop-early ladder, no-action calls, false-alarm table, Display check, escalation default |
| `examples.md` | Three worked investigations — two end without a budget change |
| `references/investigation-contract.md` | Exact script-output contract + extension hooks (source of truth: the script) |
| `scripts/investigate_underspend.py` | The evidence collector — read-only, API-only |
| `README.md` | Zero-context install and orientation |

Runtime artifacts: **none** — the script writes nothing to disk.

## After a Run

Console output is the entire record (timestamped in its header) — the
investigation report you write is the durable artifact, so write it before
the terminal scrolls away. There is no state to clean up; re-running is
always safe and always current.

## When to Load Something Else

| Trigger | Load |
|---|---|
| Investigation start — always | The three companion frameworks (list above; per-framework load-map in `rules.md`) |
| Step 1 with no budget-change log | [`change-history-checker`](../change-history-checker/) — API-based recent-changes lookup |
| A campaign absent from STEP 1, or you need end dates / settings | [`google-ads-query`](../google-ads-query/) — campaigns pull to CSV |
| Extending the shipped script or writing follow-up GAQL | [`gaql-query-patterns`](../gaql-query-patterns/) — spend/IS/settings templates |
| Underspend was the ticket, but the account smells broadly unhealthy | [`account-diagnostic`](../account-diagnostic/) — full 42-point inspection |
| No working `google-ads.yaml` yet | [`google-ads-api-setup`](../google-ads-api-setup/) — one-time credential setup |
