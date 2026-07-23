# Worked Examples — three bulk-edit reads

Three runs from real-shaped situations, all data synthetic. The mechanics
cited are in [`references/edit-contract.md`](references/edit-contract.md);
the judgment follows [`rules.md`](rules.md).

---

## Example 1 — Routine rebrand, and what the review checklist catches

**Halstead Auto** rebrands to **Halstead Automotive Group** across two
accounts. Dry-run first (rules pre-flight #1):

```
python scripts/rsa_bulk_edit.py \
  --cids "1234567890,2345678901" \
  --search "Halstead Auto" \
  --replace "Halstead Automotive Group" \
  --dry-run
```

```
Querying 1234567890...
  Found 24 RSA ads

Querying 2345678901...
  Found 18 RSA ads

Total RSA ads: 42
Ads with matches: 31 / 42
```

31 of 42 is the expected shape for a brand string (brand headlines plus
scattered descriptions). Re-run with `--sheet-id`, then the checklist:

- **Length audit:** filter `Has Match` = YES, `=LEN()` over the changed
  cells. It catches one: `Visit Halstead Auto Today` (25 chars) became
  `Visit Halstead Automotive Group Today` — **37 chars**. The script wrote
  it unflagged (it validates nothing); the fix is editing that cell to a
  compliant line (`Visit Halstead Automotive`) before any paste.
- **Casing scan:** one description read `your neighborhood halstead auto
  team` — the case-insensitive match inserted the replacement exactly as
  typed: `your neighborhood Halstead Automotive Group team`. Title Case
  mid-lowercase-sentence. Fixed in the cell; the alternative discipline is
  `--case-sensitive` passes per casing variant.
- **Paste:** filter to account `123-456-7890`, open that account in
  Editor, copy columns C→Z, review Editor's preview, post. Then the same
  for `234-567-8901`. Never one paste across both — the pasted range
  carries no account identity.

---

## Example 2 — EDGE: the substring collateral read

**Bridgeline Auto Care** (CID `3456789012`) drops "Care" from the brand.
The lazy search is the single word:

```
python scripts/rsa_bulk_edit.py --cid 3456789012 \
  --search "Care" --replace "Service" --dry-run
```

```
Total RSA ads: 22
Ads with matches: 22 / 22
```

**The read:** 22 of 22 is too clean — a brand term shouldn't live in every
single ad. The preview's `Changes:` lines confirm collateral: matches in
ads that have no brand headline at all. There is no word-boundary mode —
`Care` matched inside `Carefree Financing Available` (which would become
`Servicefree Financing Available`) and `Careful Diagnostics` (→
`Serviceful Diagnostics`).

**The fix is the search string, not the tool:** search the full phrase
`Bridgeline Auto Care` → `Bridgeline Auto Service`. Dry-run again: 9 / 22,
all brand slots. That's the shape of a correct rebrand match. Sheet run,
length audit (all ≤30), paste.

The general rule from `rules.md` pre-flight: short or common search strings
need lengthening with context before they're safe. Match the longest
unambiguous string that identifies the change.

---

## Example 3 — EDGE: the ask that isn't bulk work (and the one that is)

**The declined ask:** "Add '24/7 Towing Available' to all our RSA ads"
(**Kestrel Automotive**, CID `0987654321`). Two independent disqualifiers,
straight from the boundary table:

1. Bulk edit **replaces** — there is no existing string to find, so
   there's nothing for this tool to do. Inserting new lines into ads is
   copy work: [`rsa-refresh`](../rsa-refresh/) for label-guided rewrites of
   existing ads, [`rsa-single-account`](../rsa-single-account/) for a full
   set.
2. `24/7 Towing Available` is a **claim**. Whether the shop actually
   offers 24/7 towing has to be verified against the website before that
   text goes anywhere — [`ad-copy-verification-standard`](../ad-copy-verification-standard/)
   governs, whichever skill writes it.

**The adjacent ask that IS bulk work:** the same account is retiring a
stale promo customizer. The site verifiably says "family owned since
2004," so the replacement text is a verified claim, and the target is a
literal token:

```
python scripts/rsa_bulk_edit.py --cid 0987654321 \
  --search "{CUSTOMIZER.Promo}" \
  --replace "Family Owned Since 2004" \
  --sheet-id YOUR_SHEET_ID --tab-name "RSA - Customizer Retirement"
```

Searching the **whole token** is the customizer discipline from `rules.md`
pre-flight #4 — matching text inside the braces would corrupt the token
instead of replacing it. Replacement length: 23 chars, safe in any slot.
Review, paste, post — and afterward,
[`change-history-checker`](../change-history-checker/) is the
authoritative record of what actually changed in the account (the tab
carries no timestamp and won't remember for you).
