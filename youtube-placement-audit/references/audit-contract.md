# Audit Contract — what the two scripts actually do

> **Source of truth:** `scripts/youtube_placement_audit.py` (the audit) and
> `scripts/youtube_channel_extractor.py` (the extractor). Every claim below
> is derived from those files; if either changes, this contract and the
> CHANGELOG must change with it. Line references point at the named script.

## The flag taxonomy (audit `:47-84`)

`FLAGGED_KEYWORDS` ships **27 keywords across 6 reason labels**:

| Reason label | Count | Keywords |
|---|---|---|
| Kids content | 15 | toy, child, pokemon, doll, cartoon, nursery, peppa pig, disney, muppets, jim henson, story time, storytime, roblox, minecraft, fortnite |
| Adult content | 4 | xxx, sexy, ` sex ` (space-padded — see below), onlyfans |
| Gaming content | 3 | gaming, ninja, twitch |
| Spam | 1 | 1-800 |
| Spam/Clickbait | 2 | viral, prank |
| Legal | 2 | dui, bail bonds |

Plus two non-keyword flags: **Null/Empty placement** (blank or
whitespace-only name, checked first `:121-122`) and **Non-English content**
(the script check below).

### Matching semantics (`:116-133`)

- **Substring, case-insensitive.** `toy` matches "Toyota", `doll` matches
  "Dollar", `dui` matches "Duisburg", `viral` matches "antiviral",
  `child` matches "children" (that one's intended). The review pass exists
  because of exactly this — rules.md carries the trap table.
- **One reason per placement, first hit wins.** The keyword dict is walked
  in its declared order (kids first, legal last); the reason string is
  `<label>: '<keyword>'`. A placement matching both `toy` and `gaming`
  reports Kids content.
- **Keyword beats non-English.** The non-Latin check runs only when no
  keyword matched (`:130-131`) — a Cyrillic channel with "minecraft" in
  the name lands in the keyword tab, not the NEA tab.
- **The ` sex ` padding** (`:68`): matches only with a space on BOTH
  sides. "Sussex Home Tours" is safe — but so is a name that merely *ends*
  in the bare word, since there's no trailing space. Deliberate
  word-isolation with a known edge, not a bug.

### Non-English detection (`:87-113`) — script, not language

`NON_LATIN_SCRIPTS` lists **24 Unicode script names**: CYRILLIC, ARABIC,
HEBREW, CJK, HIRAGANA, KATAKANA, HANGUL, DEVANAGARI, THAI, GREEK,
ARMENIAN, GEORGIAN, BENGALI, TAMIL, TELUGU, KANNADA, MALAYALAM, GUJARATI,
PUNJABI, TIBETAN, MYANMAR, KHMER, LAO, SINHALA. Each alphabetic character
is looked up by Unicode name (`:106`); one character from any listed
script flags the whole placement.

- **Latin-script languages are invisible to this check.** Spanish, French,
  German, Vietnamese — é is `LATIN SMALL LETTER E WITH ACUTE`, no listed
  script in the name, no flag. "Non-English Alphabet" in the tab name is
  literal: alphabet, not language. Foreign-language content in Latin
  script never reaches the NEA tab (rules.md owns what to do about that).
- Emoji and symbols aren't alphabetic — skipped entirely.
- The `except ValueError` fallback (`:110-112`) is unreachable: the
  two-argument `unicodedata.name(char, '')` returns the default instead of
  raising, so the `ord > 127` branch never runs. Dead code, no behavior.

## Audit script — selection and queries

- **Account walk** (`:160-187`): `customer_client` under `--mcc`, managers
  excluded, **status ENABLED only** (paused/canceled accounts never
  audited). `--filter` is a case-insensitive substring on the descriptive
  name; results sort alphabetically; `--limit N` takes the first N *after*
  filter and sort — so it's the alphabetical head, not a random sample.
- **Three GAQL queries per account**, all date-scoped `LAST_N_DAYS`
  (`--days`, default 30):
  1. `performance_max_placement_view`, placement types YOUTUBE_VIDEO +
     YOUTUBE_CHANNEL (`:196-206`). **Impressions only** — the resource
     doesn't expose clicks/cost/conversions, so those are written as 0
     (`:218-220`). Rows label as campaign type `PMAX`, placement type
     `PMAX-YOUTUBE_VIDEO` / `PMAX-YOUTUBE_CHANNEL`.
  2. + 3. `detail_placement_view` once per placement type (`:226-241`) —
     Display, Demand Gen, and Video campaigns, full metrics
     (cost converted from micros `:254`). Campaign type is the channel
     enum name (`DISPLAY`, `DEMAND_GEN`, `VIDEO`); placement type
     title-cased (`Youtube Video` / `Youtube Channel`).

### The silent-swallow trap (`:222-223`, `:257-258`)

Each of the three queries is individually wrapped in
`except Exception: pass`. A query that fails — permissions, API version,
anything — contributes zero rows **with no error line**. An account whose
queries all fail prints `No YouTube placements`, indistinguishable from a
genuinely clean account. The per-account handler in `main()`
(`:452-457`, the `Skipped (no access)` / `Error:` lines) only catches
exceptions raised *outside* those inner wraps, so it fires rarely. The
working tell is comparative: sibling accounts running the same campaign
types return placements while one account reads empty — treat that as a
failed account, not a clean one (rules.md triage).

## Audit script — sheet output (`:267-345`)

- **A run with zero flags writes nothing** (`:271-273`): it prints
  `No flagged YouTube placements found.` and returns — existing tabs keep
  the *previous* run's rows. The `Run Date` column (date-only) is the
  staleness tell.
- Tab split (`:276-277`): rows whose reason is exactly `Non-English
  content` → `Bad - YouTube - NEA`; **everything else — including
  Null/Empty — → `Bad - YouTube`**. Both tabs sort by impressions
  descending.
- **13 columns** (`:292-296`): Placement Name, Placement URL, Account
  Name, CID, Campaign, Campaign Type, Placement Type, Flag Reason,
  Impressions, Clicks, Cost, Conversions, Run Date.
- Per-tab write (`:330-340`): existing tab → `clear()` then rewrite from
  A1; missing tab → created. **A tab with zero rows this run is skipped
  entirely — including the clear** (`:331-333`): keyword flags with no NEA
  rows leaves the NEA tab holding last month's data. Check `Run Date`
  per tab, not per sheet.
- Gates: `--test` prints the preview and writes nothing; otherwise an
  interactive `y/n` unless `--force`.
- Console: 70-char `=` banners; per-account `[i/N] name (id)` blocks;
  a results block with keyword/NEA counts and top-5-by-impressions lists.
  On Windows, stdout is reconfigured to UTF-8 (`:353-354`) so non-Latin
  placement names print instead of crashing.

## Extractor — what feeds the channel tabs

- **API key** (`:53-66`): `--api-key` wins; else `youtube_api_key` from
  the `--creds` yaml; neither → error. Sheets access reuses the yaml's
  OAuth values (`:69-82`).
- **Only rows whose Placement URL contains `/video/` are read**
  (`:124-125`). Video ID = the URL segment after `/video/`, query string
  stripped (`:127`). **Channel-type rows (`/channel/` URLs) are skipped —
  flagged channels never appear in the Channels-to-Negate tabs.** They're
  already channels: pull them straight from the Bad tabs when building
  the exclusion list (rules.md).
- Per-video aggregation across rows (`:129-146`): impressions/clicks
  summed as ints, cost tolerates `$` and commas, flag reasons and account
  names collect as sets, the display name truncates to 60 chars.
- **Channel lookup** (`:159-190`): `videos().list` in batches of 50 (the
  YouTube API cap, `:46`). A failed batch prints a warning and the run
  continues — those 50 videos silently drop out of the aggregation.
  Videos the API doesn't return are deleted/private; they're counted and
  excluded (`:357-359`).
- **Aggregation by channel** (`:197-224`): metrics summed, first 5 sample
  video names kept (first 3 written, `:251`), sorted by flagged-video
  count descending. `Accounts Affected` is a **count**, not names
  (`:250`).
- **Channel tabs** (`:227-276`): 11 columns (Channel Name, Channel URL,
  Channel ID, Flagged Videos, Total Impressions, Total Clicks, Total
  Cost, Flag Reasons, Accounts Affected, Sample Videos, Run Date — this
  Run Date carries a time, unlike the audit tabs). Cost renders as
  `$N.NN`; the write uses `USER_ENTERED`, so numbers arrive as numbers
  and `$` strings as currency. Existing tab → cleared then rewritten;
  missing → created; per-tab `y/n` confirm unless `--force`.
- **Job selection** (`:326-338`): default both tabs; `--nea-only` skips
  the keyword job, `--keywords-only` skips the NEA job. **Passing both
  flags selects zero jobs** — the run prints DONE having processed
  nothing. `--limit` caps how many video IDs get looked up (applied after
  reading, `:349-351`).

## What neither script does

Neither script touches Google Ads state. The audit reads placements and
writes a sheet; the extractor reads the sheet, calls the YouTube Data API,
and writes the sheet. **Placement exclusions are applied by you, in the
UI or Editor** — nothing here mutates an account.
