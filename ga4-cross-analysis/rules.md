# Decision Rules — GA4 Cross-Analysis

The judgment layer for the collection protocol: when this skill is the right tool, how to
read the settings output, and what an honest partial dataset looks like. Exact script
mechanics and the you-implement contracts live in
[`references/collection-contract.md`](references/collection-contract.md); interpretation
methodology deliberately lives elsewhere (routing below).

---

## Invariants

1. **Collection, not interpretation.** This skill's product is the structured dataset.
   Observations ("83% of GA4 conversions are Android WebView" next to "no device
   adjustments configured") belong in the output; verdicts about what they mean route to
   [ga4-campaign-cross-reference](../ga4-campaign-cross-reference/).
2. **Every JSON field has a source or stays empty.** The source map in the contract
   governs. Fields the shipped script can't produce (location names, radius, URL
   exclusions) are filled from the UI or your own scripts — or shipped as `null` with a
   note. A number with no source is a fabrication, even in a hurry.
3. **Read-only, both platforms.** The shipped script and all four contracts are pure
   queries. Nothing in this skill mutates a campaign, a property, or a sheet.
4. **Attribute claims to their platform.** Settings claims come from the Google Ads side;
   behavior claims come from GA4. "GA4 shows conversions outside the radius" is two
   claims from two sources — keep them separately sourced in the output so the consumer
   can verify each.
5. **The Step 4 shape is the interface.** Consuming skills and agents parse it. Extra
   fields are fine; renaming or restructuring the documented keys breaks consumers
   silently.

---

## Is cross-analysis the right tool?

| The ask | Right tool |
|---|---|
| One Google Ads metric ("what did the campaign spend last week?") | [google-ads-query](../google-ads-query/) — a single GAQL pull, no GA4 side needed |
| "Check this campaign's geo/bidding/device settings" | The shipped script alone — still this skill, settings side only |
| "Why is GA4 showing X when Ads is set to Y?" | Collect here, then [ga4-campaign-cross-reference](../ga4-campaign-cross-reference/) for hypothesis → verification → finding |
| "Leads are junk / no-shows / bots" | [ga4-lead-quality-investigation](../ga4-lead-quality-investigation/) — the full investigation; it auto-loads this skill as its collection step |
| "Build me the GA4 pull for this property" | The contract's GA4-side implementation notes — you're implementing, not running |

---

## Reading the settings output

What each block supports concluding — and where the trap is:

- **Bid strategy:** a missing target line under `TARGET_CPA`/`TARGET_ROAS` does **not**
  mean no target exists — portfolio-held targets are invisible to this script. Only three
  strategy types ever get a detail line; `MAXIMIZE_CONVERSIONS` never shows its optional
  CPA cap here.
- **Geo:** the printed values are IDs — resolve them before telling anyone what the
  campaign targets. `PRESENCE` vs `AREA_OF_INTEREST` is the single highest-leverage line
  in the output: under `AREA_OF_INTEREST`, conversions from distant cities can be
  working-as-configured (people *interested in* the targeted area), not evidence of
  broken targeting.
- **URL expansion:** only meaningful for Performance Max. On any other campaign type the
  line always reads `Enabled` — ignore it there.
- **Devices:** `No bid adjustment` covers both "no adjustment set" and "device fully
  opted out" (the zero-modifier fallback in the contract). If GA4 shows zero desktop
  users, check the UI before concluding organic device mix.
- **Networks:** raw booleans. `Search Partners: True` next to GA4 referral oddities is an
  observation worth carrying into the output — not a verdict.

---

## False alarms

| Looks like | Actually |
|---|---|
| `URL Expansion: Enabled` on a Search campaign | The field is PMax-scoped; the line is noise on other types |
| `No bid adjustment` on every device | Possibly true, possibly a full opt-out rendered through the zero-modifier fallback — UI check decides |
| `No location targeting found (targeting all locations)` printed above an Excluded Locations list | Consistent: positive targeting is all-locations, minus the exclusions — not a parsing bug |
| Shell reports success but the campaign wasn't found | Not-found prints `ERROR:` and still **exits 0** — read the console, not the exit code |
| Two `BASIC SETTINGS` blocks for one name | A removed campaign shares the name; later sections describe the **last** match |
| GA4 conversions ≠ Ads conversions for the same campaign | Different attribution and counting models — a modeling difference, not automatically breakage; route to interpretation |
| `Proximity targeting detected` with no radius shown | Script cap — the radius value isn't printed; get it from the UI |
| GA4 cities outside the targeted area under `AREA_OF_INTEREST` | Expected behavior for interest-based targeting — flag for interpretation, don't pre-declare a config bug |

---

## Partial data is honest data

The common real state: the shipped script runs today; the GA4-side scripts aren't
implemented yet. Proceed — with the gap declared:

- Collect the settings side fully. Ship the JSON with `google_ads` populated and the
  `ga4` object absent or `null`, and say so in the summary.
- What you can still support: settings verification ("the campaign targets X under
  PRESENCE, budget $Y, no device adjustments").
- What you cannot: any behavioral claim (landing pages, cities, hours, engagement).
  Don't approximate GA4 numbers from the Ads UI's analytics widgets — different counting,
  unsourced field.

**Escalation default:** when a field has no legitimate source in your environment, ship
the dataset with the gap declared rather than filling it. A consumer can work around a
declared gap; an invented value poisons every downstream conclusion.
