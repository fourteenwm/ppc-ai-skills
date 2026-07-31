---
name: competitor-analysis-v2
description: Comprehensive competitive analysis combining website intelligence, 22-attribute ad copy framework, automated screenshots via Playwright, and verification rigor. Auto-invoke when user says "analyze competitors", "competitor report", "competitive intelligence", "market positioning analysis", or "client gift". Outputs Strategic Client Gift OR tactical Ads Angle Brief.
allowed-tools: [Bash, Read, Write, WebFetch, WebSearch, Task]
---

# Competitor Analysis v2

**Purpose:** An 8-phase competitive analysis of a client plus up to 5 competitors —
website intelligence, optional 22-attribute ad scoring, automated screenshots, gap
identification, and mandatory client verification — producing a strategic **Client
Gift** (10-15 page PDF), a tactical **Ads Angle Brief** (1 page), or both.

**Credentials Required:** None. The whole workflow runs on Playwright plus web fetches.
Competitor ad copy for the optional ad-scoring phase comes from a SERP tool or is
pasted in — no Google Ads API access needed.

**This skill deliberately does NOT:**
- See competitor spend, impression share, or auction data — public surfaces only;
  decline asks that need them
- Put Google Ads mechanics in the Client Gift, or hand the Ads Brief to a client
- Ship a claim without client-website verification — Phase 6 gates both outputs
- Build the final RSAs — the brief's 30-char angle sketches feed
  [`ad-copy-generation-framework`](../ad-copy-generation-framework/) and
  [`rsa-single-account`](../rsa-single-account/)
- Monitor competitors over time — every run is a dated snapshot

---

## When to Use This Skill

| Use case | Output |
|----------|--------|
| White-label deliverable for a partner agency's clients | Client Gift + Ads Brief |
| Relationship/retention tool for your own managed accounts | Client Gift (as a gift) |
| Positioning input before an ad copy build | Ads Brief |

**Ask the user at the start** which output they want (for white-label partner work,
"Both" is the usual answer; for a relationship gift, "Client Gift" alone). The choice
decides which prompts run — the run table is in
`references/workflow-contract.md` § Which prompts run, per output.

---

## The 8-Phase Workflow

The seven files in `prompts/` are the methodology authority for their stages — this
SKILL routes to them and never restates their scoring criteria. Four of them carry
internal phase labels from the framework's v1 numbering; **translate via the contract's
numbering table** rather than trusting a prompt's label against the phases below.

### Phase 1: Gather Inputs

```
- Client name + URL
- Industry/market
- 5 competitor URLs (or request search assistance)
- Output type: "Client Gift" | "Ads Brief" | "Both"
```

Competitor selection is a judgment call with its own rules — who earns one of the five
slots, what to exclude, why an honest 3 beats a padded 5: `rules.md` § Which
competitors earn a slot. If the user has no list: WebSearch 8-10 candidates, present
with brief descriptions, get approval on 5.

### Phase 2: Capture Screenshots (MANDATORY)

```bash
node .claude/skills/competitor-analysis-v2/scripts/screenshot.cjs \
  https://client.com \
  https://competitor1.com https://competitor2.com https://competitor3.com \
  https://competitor4.com https://competitor5.com \
  --output /tmp/competitor-report/screenshots
```

Client URL first — index 1 is the client everywhere downstream. Full URLs only (a
schemeless URL is silently dropped). Check the `Screenshots captured: X/Y` line, not
the exit code. Prerequisite: `npm install playwright`. Capture mechanics, retry
behavior, and the `screenshots.json` metadata contract:
`references/workflow-contract.md` § screenshot.cjs.

### Phase 3: Extract Website Content (Parallel)

Launch 6 parallel Task agents, one per URL (client + 5 competitors):

```
- subagent_type: "general-purpose"
- prompt: "Use WebFetch to analyze [URL]. Use this extraction prompt:
  [paste from prompts/website-extraction.md]. Return only the XML output."
```

Serial fetching takes 5-6 minutes; parallel completes in ~1. Output: one 21-field XML
profile per site (schema owned by `prompts/website-extraction.md`). An empty field on a
JS-heavy site can be a fetch artifact — cross-check the screenshot before recording it
as a gap (`rules.md` § Screenshot reads).

### Phase 4: Analyze Competitor Ads (If Available)

If SERP results or pasted ads exist: run `prompts/strategic-analysis.md` (attributes
1-15, 45 points) and `prompts/tactical-scan.md` (attributes 16-22, 21 points) per
competitor ad, then feed scores to Phase 5. If no ads: skip, note "Ad analysis not
performed (no competitor ads provided)" — website analysis is sufficient for the
Client Gift.

### Phase 5: Gap Identification

Run `prompts/gap-identification.md` — messaging matrix, positioning map, emotional
landscape, strategic/tactical gap tests (table stakes vs differentiators vs
whitespace). Blank scaffolds live in `prompts/analysis-framework.md`. This phase
identifies opportunities, never recommendations — that distinction is the prompt's own
critical rule.

### Phase 6: Client Verification (MANDATORY)

Run `prompts/client-verification.md`: scrape the client site, build the verified
capabilities inventory, map every gap to ✅ can-fill / ❌ cannot-verify with source
citations. **No recommendation survives without verification — this phase gates both
outputs and is non-negotiable.** It is the
[`ad-copy-verification-standard`](../ad-copy-verification-standard/) in action.

### Phase 7: Generate Output(s)

- **Client Gift** (10-15 pages, for the CLIENT, zero Google Ads mechanics) — structure
  owned by `templates/client-gift.md` (15 sections, cover through summary). Tone:
  strategic, insight-driven, no jargon.
- **Ads Angle Brief** (1 page, for the PRACTITIONER) — structure owned by
  `templates/ads-angle-brief.md` (7 sections: positioning axis through ad-to-page
  rules). Angle development runs `prompts/angle-development.md` on verified gaps only;
  angle-choice judgment (verification strength beats gap value, compliance demotions,
  small-sample phrasing) is `rules.md` § Angle selection.

### Phase 8: PDF Generation (For Client Gift)

Build HTML with embedded CSS from `templates/template.css`, place screenshots, render
positioning maps as CSS grids, then:

```javascript
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + process.cwd() + '/[client]-competitor-report.html', { waitUntil: 'networkidle' });
  await page.pdf({
    path: '[client]-competitor-report.pdf',
    format: 'A4',
    printBackground: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' }
  });
  await browser.close();
})();
```

---

## Quality Checklist

Before delivery:
- [ ] All 6 screenshots captured successfully (`X/Y` line, `screenshots.json`)
- [ ] Website content extracted for all 6 URLs (thin fetches cross-checked)
- [ ] Client verification completed (Phase 6)
- [ ] All recommendations have source citations
- [ ] Client Gift has NO Google Ads mechanics
- [ ] Ads Brief uses ONLY verified angles; "Cannot Recommend" list intact
- [ ] Positioning maps are accurate
- [ ] Property management client → Fair Housing check on every angle

---

## Files in This Skill

| File | Role |
|---|---|
| `SKILL.md` | This workflow — identity, phases, routing |
| `rules.md` | Judgment: competitor selection, screenshot reads, angle choice, false alarms, escalation |
| `examples.md` | Three worked reads: full engagement, gift-only PM run, the declined ask |
| `references/workflow-contract.md` | Authority map, the v1→v2 numbering translation table, line-derived screenshot.cjs mechanics |
| `prompts/website-extraction.md` | Phase 3 authority — extraction prompt + 21-field XML schema |
| `prompts/strategic-analysis.md` | Phase 4 authority — attributes 1-15 criteria + bands *(internal label "Phase 1" = v1)* |
| `prompts/tactical-scan.md` | Phase 4 authority — attributes 16-22 flags + bands *(internal label "Phase 2" = v1)* |
| `prompts/gap-identification.md` | Phase 5 authority — matrix, maps, gap tests |
| `prompts/client-verification.md` | Phase 6 authority — the verification law *(internal label "Phase 4" = v1)* |
| `prompts/angle-development.md` | Post-Phase-6 authority — angle structure + priorities *(internal label "Phase 5" = v1)* |
| `prompts/analysis-framework.md` | Blank scaffolds for Phase 5 outputs |
| `scripts/screenshot.cjs` | Playwright capture — the skill's only code |
| `templates/client-gift.md`, `templates/ads-angle-brief.md`, `templates/template.css` | Output structure + PDF styling |
| `sales/service-page-copy.md` | Copy for selling this as a service (page copy, emails, testimonial capture) — business asset, not a runtime input |

## After a Run

Nothing lands in the skill folder. The run's footprint, all in your chosen output
location: the screenshot PNGs plus `screenshots.json` (ISO `capturedAt`, per-URL
success/retried — the record of what ran and what's missing), and the deliverables
(`[client]-competitor-report.html` → `.pdf`, the brief's markdown). Date the
deliverables; every run is a snapshot, and the next one starts fresh.

## When to Load Other Skills

| Load | When |
|---|---|
| [`ad-copy-verification-standard`](../ad-copy-verification-standard/) | Always — Phase 6 is this standard; install it alongside |
| [`ad-copy-generation-framework`](../ad-copy-generation-framework/) | After the brief, to turn verified angles into full RSA copy (23 elements) |
| [`rsa-single-account`](../rsa-single-account/) | When the brief feeds a full single-account RSA build |
| [`fair-housing-compliance`](../fair-housing-compliance/) | Before writing any angle or recommendation for a property-management / housing client |
| [`markdown-to-sheets-presenter`](../markdown-to-sheets-presenter/) | When the client wants the scoring matrices and gap tables as a formatted Google Sheet alongside (or instead of) the PDF |

---

## Example Usage

**"Run competitor analysis for Smith Auto Repair"** → ask which output → Both → client
URL + 5 competitor URLs (or search flow) → full 8-phase run → Client Gift PDF + Ads
Brief markdown.

**"Create a client gift for Example Property"** → Client Gift only → phases 1-3, 5-8
(Phase 4 skipped unless ads are provided) → strategic PDF, delivered with the
property-management framing from `sales/service-page-copy.md`.

---

## Installation

```bash
mkdir -p .claude/skills/competitor-analysis-v2/scripts \
         .claude/skills/competitor-analysis-v2/prompts \
         .claude/skills/competitor-analysis-v2/templates \
         .claude/skills/competitor-analysis-v2/sales \
         .claude/skills/competitor-analysis-v2/references
for f in SKILL.md README.md rules.md examples.md \
         references/workflow-contract.md scripts/screenshot.cjs \
         prompts/website-extraction.md prompts/strategic-analysis.md \
         prompts/tactical-scan.md prompts/gap-identification.md \
         prompts/client-verification.md prompts/angle-development.md \
         prompts/analysis-framework.md templates/client-gift.md \
         templates/ads-angle-brief.md templates/template.css \
         sales/service-page-copy.md; do
  curl -o ".claude/skills/competitor-analysis-v2/$f" \
    "https://raw.githubusercontent.com/fourteenwm/ppc-ai-skills/main/competitor-analysis-v2/$f"
done
```

---

## Version History

- **v2.0** (2026-01) - Merged the 22-attribute ad analysis framework and the strategic competitor report into a single 8-phase workflow
- **v1.0** (2025-12) - Original 22-attribute ad copy analysis framework
