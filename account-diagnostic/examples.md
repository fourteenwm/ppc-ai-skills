# Examples — worked inspection reads

Three worked triage decisions applying `rules.md`. All accounts, numbers, and
findings are synthetic.

## 1. RED overall with $9,800 estimated waste — ordering the fixes

**Report:** Summit Auto Care (1234567890), `local-service` run, 44 checks:
30 GREEN / 7 YELLOW / 5 RED / 2 N/A. Estimated waste $9,800/mo. The REDs:

- Check 22 — auto-apply enabled, high-risk: `USE_BROAD_MATCH_KEYWORD`
- Check 12 — 22% zero-conv search-term waste ($4,400)
- Check 13 — 5 terms over $50 with 0 conversions ($1,700)
- Check 35 — avg 2 negatives/campaign
- Check 8 — 31% Budget Lost IS ($3,700)

**Reasoning:** Sorted by dollars, check 12 leads. But the triage order says
dependencies beat dollars. Check 22 is the root: Google has been auto-flipping
keywords to broad match, which is exactly how search-term waste (12/13)
exploded past a 2-negative wall (35). And check 8's "add budget" implication
is a trap — the false-alarm mindset applies in reverse: raising budget while
22% of spend converts nothing scales the waste, not the results.

**Decision:** Three actions, in order. (1) Switch off the auto-apply types —
UI change, listed exactly, human executes. (2) One `sqr-pipeline` run to
classify the search terms and build negatives — covers 12, 13, and 35
together, with its own review gate. (3) Only after a clean re-inspection
shows waste under control, revisit check 8 with
`underspending-investigation` to decide whether the budget cap is real.
Nothing mutated from this session; the report and the ordered plan are the
deliverable.

## 2. Pacing REDs on an otherwise-green account — the false alarm

**Report:** Lakeside Property Group (9876543210), `property-management` run,
42 checks: 36 GREEN / 3 YELLOW / 2 RED / 1 N/A. The REDs:

- Check 5 — +21% underspent (threshold ±8%), $2,100/mo gap
- Check 6 — projected EOM spend 74% of budget

**Reasoning:** Two pacing REDs with everything else green is the false-alarm
table's opening case. Campaign start dates show the account's largest
campaign launched on the 12th — it's the 19th, so the month's expected-spend
math includes 11 days when the campaign didn't exist, and smart bidding is
still in its ramp. The verdicts are correct (the account IS behind month
pace) and stay RED in the report; the *interpretation* is that the gap is a
launch artifact, not a delivery problem.

**Decision:** No budget change — explicitly. Raising daily budgets to "catch
up" mid-learning would destabilize bidding and overshoot next month. Note the
artifact in the triage summary, re-inspect after the first full calendar
month. This is the never-overrule-but-contextualize invariant in action: the
report stays honest, the recommendation stays calm.

## 3. Edge case: "just fix everything it found"

**Instruction:** After a RED report on Harbor Dental (1234567890), the
operator is told: "Great — go ahead and fix all of it."

**Reasoning:** Direct instruction, but the diagnosis-only invariant isn't a
formality — it exists because half the "fixes" are mutations with blast
radius (negative uploads, automation opt-outs, asset changes), and batch-
approving them sight-unseen is how accounts get wrecked. There is also no
single "fix it" path: each finding routes to a different tool with its own
dry-run and approval gate, and several (auto-apply, content suitability) are
UI-only changes no script here can make.

**Decision:** Decline the blanket execution, deliver the routed punch list
instead: each finding mapped per the routing table — which skill to run,
what it will preview, and where a human approval code is required — plus the
UI-only items listed as exact setting → target value. The human picks the
order and approves each mutation at its own gate. Fastest safe path, same
end state.
