# Edit Contract — selection, match semantics, sheet output, Editor paste

> **Source of truth:** `scripts/rsa_bulk_edit.py` — the script wins over
> this document. Mirrors the shipped revision as of 2026-07-23. Any
> behavior change in the script must update this contract and the
> CHANGELOG in the same commit.

Exactly what the script matches, what it writes, and what the Google Ads
Editor paste carries. Judgment about *running* an edit lives in
[`rules.md`](../rules.md).

## Selection scope

The query pulls ads where:

- `ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD`
- `ad_group_ad.status = ENABLED`
- `campaign.status = ENABLED`

There is **no ad-group status filter** — an enabled ad inside a paused ad
group is included (it isn't serving, but its row appears). Paused ads and
paused campaigns are invisible: "I can see that text in the UI but got 0
matches" usually means the ad or campaign holding it isn't ENABLED.

Accounts: `--cid` (single) and/or `--cids` (comma-separated) — at least one
required; passing both combines them. Dashes are stripped from every CID.

## Match and replace semantics

- **Literal text, not regex.** The search string is escaped before
  compiling — wildcards and regex syntax match themselves.
- **Substring matching, no word boundaries.** `car` matches inside
  `Carefree`. There is no whole-word mode; the only narrowing tools are a
  longer search string and `--case-sensitive`.
- **Case-insensitive by default** (`--case-sensitive` to disable) — but the
  **replacement is inserted exactly as typed**. A case-insensitive match on
  `Color` replaced with `colour` produces lowercase `colour` mid-headline.
  Casing discipline is the operator's job (`rules.md`).
- **Backslashes in the replacement are interpreted** by the regex engine's
  replacement parser (`\g`, `\1`, and invalid escapes error out). Avoid
  `\` in replacement text.
- **Fields searched: Headlines 1–15 and Descriptions 1–4 only.** Path 1,
  Path 2, and the Final URL are carried into the output for the Editor
  paste but are **never searched or modified**.
- An empty `--replace ""` is valid — deletion mode.
- **No length validation anywhere.** A replacement that pushes a headline
  past 30 characters (or a description past 90) is written to the sheet
  unflagged. The length audit is a mandatory review step (`rules.md`).

`Has Match` = YES when any headline or description on the ad matched;
`Changes Made` lists which fields (`H3, D1`). Non-matching ads are still
written, with `Has Match` = NO.

## Per-account error isolation

Each account is queried in its own try/except: a failing account prints
`  Error: …` under its `Querying {cid}...` line and contributes **zero
rows** — the run continues and the summary counts don't distinguish "no
ads" from "query failed." The console is the only record of a failed
account; its ads are simply absent from the sheet.

## Sheet contract

- Sheets auth reuses **`google-ads.yaml` only** (its OAuth refresh token
  with the `spreadsheets` scope) — there is no `token-sheets.json` path in
  this script, and both the API client and the sheet writer load the file
  literally as `google-ads.yaml`, so **run from the directory that holds
  it** (there is no `--config` flag).
- Tab (`--tab-name`, default `RSA Edits`): **cleared and rewritten** every
  run; created (1000×30) if missing. **No run timestamp anywhere** — use
  dated tab names if you need run-over-run history.
- Every selected ad is one row, matched or not.

| Columns | Content |
|---|---|
| A–D | Account Name, Customer ID (dashed), Campaign, Ad Group |
| E–S | Headline 1–15 (post-replacement text) |
| T–W | Description 1–4 (post-replacement text) |
| X–Z | Path 1, Path 2, Final URL (carried through, never edited) |
| AA–AC | Has Match, Changes Made, Ad ID |

## Run modes

- `--dry-run`: console only — prints the first **10** matched ads (account,
  ad ID, changed fields). Wins over `--sheet-id` if both are passed.
  Nothing is written.
- `--sheet-id`: full write as above, then the sheet URL.
- Neither: the run computes matches, prints
  `No --sheet-id provided. Use --sheet-id to write results.` and persists
  nothing.

Console summary either way: per-account `Found N RSA ads`, then
`Total RSA ads: N` and `Ads with matches: X / Y`.

## Google Ads Editor paste

The documented paste range is **columns C onward through Z** (Campaign →
Final URL). Two consequences:

- The range excludes account identity (A–B) — on a multi-account run,
  **filter the tab to one account before copying**, and paste with that
  account open in Editor.
- The range excludes Ad ID (AC) — **pasted rows carry no ad identity**, so
  Editor cannot match rows to specific existing ads by ID. With more than
  one RSA in an ad group, review Editor's proposed changes carefully before
  posting (the review step in Editor is part of the workflow, not
  optional).

Rows with `Has Match` = NO are in the tab too — paste only the filtered
matches, or Editor will treat every pasted row as a change candidate.

## Reading run state cold

The tab is a snapshot with no stamp: a cold session cannot date it from
content (dated `--tab-name` is the fix), and can't see failed accounts (the
console was the only record). After an Editor post, the authoritative
record of what actually changed in Google Ads is change history —
[`change-history-checker`](../../change-history-checker/) reads it.
