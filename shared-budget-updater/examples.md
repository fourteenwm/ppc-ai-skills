# Examples - worked triage decisions

## 1. NOT_FOUND on a budget ID

**Alert:** Row 12 - CID 1234567890, Budget 9876543, $450 - NOT_FOUND: The
mutate resource was not found.

**Reasoning:** NOT_FOUND is sheet-data class per the triage table. A read-only
lookup of shared budgets under that CID (an ad-hoc pull via
[`google-ads-query`](../google-ads-query/)) shows budget 9876453 exists but
9876543 does not - two digits transposed in column B.

**Decision:** Report the exact correction ("row 12 column B should be
9876453"). The row keeps its empty column D, so after the owner fixes the cell
the next scheduled run heals it automatically. No dispatch, no sheet edit by
Claude.

## 2. One TIMEOUT among six rows, five processed

**Alert:** Row 7 - TIMEOUT after 3 attempts; footer says "5 other row(s)
processed OK."

**Reasoning:** Transient class, first occurrence. The row's column D is still
empty, so the next run retries it with zero human effort. Re-dispatching now
would add alert noise for no benefit - the five processed rows are marked done
and will be skipped, and the retry proves nothing tomorrow's run won't.

**Decision:** No action. Confirm after the next run that row 7's column D
turned `x` (the Ads-side receipt, if you want one, is the budget's change
history — [`change-history-checker`](../change-history-checker/)).
Restraint is the correct call for a first transient failure.

## 3. Edge case: a $0 row intended to "pause spend"

**Alert:** Row 3 - CID 1234567890, Budget 5551234, $0 - INVALID_AMOUNT: Budget
amount must be greater than $0 - row skipped before any API call.

**Reasoning:** The guard worked as designed - but the interesting question is
the intent behind the row. Someone entered $0 to try to stop spend through
this tool. The tool's surface is amount-only; pausing is a status change, and
the invariants forbid widening the mutation surface. A "$0.01 workaround"
would be a real budget mutation nobody approved as such.

**Decision:** The row should be removed from the sheet (by a human), and the
pause request routes through normal channels (campaign/budget status changes
are handled outside this workflow entirely). Claude does neither edit itself:
report the situation, recommend the removal, stop.
