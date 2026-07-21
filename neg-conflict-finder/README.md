# MCC Negative Keyword Conflict Finder

A Google Ads Script that finds every place a negative keyword is silently blocking a positive keyword you bid on — across every account under your MCC, at every level Google supports.

**The pain point:** Old negatives accumulate. A negative you added 2 years ago against a stale campaign can quietly block keywords you're paying for today. Most agencies never check, because checking manually across 10+ accounts is hours of work. This script does it in one run and writes the results to a Google Sheet.

---

## What It Finds

Conflicts at every level Google supports:

| Level | What's checked |
|---|---|
| **Ad group** | Negatives that block positives in the same ad group |
| **Campaign** | Campaign-level negatives blocking positives in any ad group |
| **Account shared lists** | Lists applied at the account level |
| **MCC shared lists** | Lists applied via the manager account |
| **Account-level negatives** | Customer-level negative keywords (when the API supports the field path) |

The detection is **match-type-aware**:
- Broad negatives block broad, phrase, and exact positives
- Phrase negatives block phrase and exact positives via subsequence match (the same way Google actually blocks them)
- Exact negatives block exact positives only

---

## Output

A Google Sheet with one row per conflict:

| Account Name | Conflicting Negative Keyword | Level & Location | Blocked Positive Keywords |
|---|---|---|---|
| Acme Co | "free" | Shared List: Global Negatives | "free shipping calculator", "free trial sign up" |
| Acme Co | [reviews] | Campaign: Brand - Search | [acme reviews] |
| Beta LLC | "diy" | Ad Group: Bathroom Remodel | "diy bathroom remodel cost" |

Run it daily on a schedule. Review conflicts. Remove the negatives you actually want gone. Don't auto-delete — some conflicts are intentional (a brand campaign with `[brand]` positive and `brand reviews` negative is a deliberate split).

---

## Setup

### 1. Label the accounts you want to process

In your MCC, apply a label (e.g., `kw-conflict-audit`) to the accounts you want the script to scan. Only labeled accounts are processed.

> Why a label? An MCC can have hundreds of child accounts. Running on all of them at once is slow and noisy. Labels let you scope by portfolio, service tier, or whatever.

### 2. Paste the script into the MCC

1. In the MCC UI: **Tools → Bulk actions → Scripts** (or **Tools → Scripts** in the modern UI)
2. Click **+ New Script**
3. Paste the contents of [`scripts/mcc-neg-keyword-conflict.js`](scripts/mcc-neg-keyword-conflict.js)

### 3. Configure

At the top of the script, edit these constants:

```javascript
const SHEET_URL = '';                          // Optional: existing Sheet URL, or leave blank
const ACCOUNT_LABEL = 'YOUR_ACCOUNT_LABEL';    // Required: the label you applied in step 1

const REQUIRE_RECENT_SPEND = true;             // Skip accounts with no recent spend
const RECENT_SPEND_DATE_RANGE = 'LAST_7_DAYS'; // Spend window for the filter
const MIN_RECENT_SPEND = 0;                    // 0 = "any spend > 0"
```

### 4. Authorize and run

1. Click **Preview** the first time — Google will prompt for authorization
2. Once authorized, click **Run**
3. Watch the logs for progress
4. Open the Sheet URL printed in the logs

### 5. Schedule it

Click **Frequency** in the script editor and pick Daily or Weekly. The script overwrites the Sheet on each run, so you always have the current state.

---

## What's Different About This Version

This script is a derivative of Google's official Negative Keyword Conflict reference script (see Apache 2.0 license header in the source). Modifications by [Kurt Henninger](https://fourteenwebmedia.com):

- **MCC-wide instead of single-account** — iterates labeled accounts under the manager account
- **MCC-level shared list support** — pulls lists owned by the manager and checks them against every child account they're applied to
- **Account-level negative keywords** — added detection (with graceful degradation when Google's API field path is unstable)
- **Phrase-vs-exact blocking fix** — the original equality check missed real conflicts like phrase-neg `"acme"` blocking exact-pos `[acme apartments]`. Replaced with subsequence match that mirrors Google's actual blocking behavior.
- **Shared-list keyword-loss fix** — earlier versions had a cache-skip bug that silently dropped every keyword after the first in a given list. Fixed.
- **Optional spend filter** — skip dormant accounts that have a label but zero recent spend, to cut noise from cancelled or paused budgets.

If you've used the original reference script and gotten zero or partial conflict rows, this version is what you actually want.

---

## Limitations

- **Search campaigns only.** Performance Max, Display, and Video campaigns don't use traditional negatives the same way.
- **Enabled keywords only.** Paused positives won't show as blocked.
- **Read-only.** This script never modifies an account. It writes to a Sheet. Removal is your judgment call.
- **MCC-level only.** Doesn't run inside a single account directly — it's a manager-account script.

---

## License

Apache 2.0 (preserved from the original Google reference script). Use, modify, and distribute freely. Attribution appreciated.

---

Built by [Kurt Henninger](https://fourteenwebmedia.com) — I manage 100+ Google Ads accounts with a system of specialized AI skills.

More free skills: [github.com/fourteenwm/ppc-ai-skills](https://github.com/fourteenwm/ppc-ai-skills)
