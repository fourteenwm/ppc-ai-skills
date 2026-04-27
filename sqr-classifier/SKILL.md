---
name: sqr-classifier
description: Classify search terms by intent. Auto-invoke when user provides search terms to classify, asks for search term analysis, or wants to identify negative keyword candidates.
---

# SQR Classifier

Classify search terms into intent categories for Google Ads accounts.

## When to Use

- User provides a list of search terms to classify
- User asks to analyze search queries from a campaign
- User wants to identify negative keyword candidates
- User provides a CSV or paste of search term data

## Classification Categories

Classify each search term into exactly ONE of these categories:

### High Intent
The searcher is actively looking for the product or service the business offers.

**Signals:**
- Contains service/product keywords matching the business
- Includes location terms relevant to the business area
- Shows purchase intent ("near me," "cost," "hire," "best," specific product names)
- Matches the business's core offerings

### Low Intent
Related to the business's industry but unlikely to convert. The searcher may be a current customer, a job seeker, or someone in early research.

**Signals:**
- Current customer queries (login, pay bill, contact, hours)
- Job-seeking terms (careers, hiring, salary, jobs at)
- Competitor brand names (searching for a specific competitor, not the business)
- Tangentially related but not a buying signal
- Review/comparison queries without purchase intent

### Informational
Research or educational queries. The searcher wants to learn something, not buy.

**Signals:**
- "How to," "what is," "why does," "can I"
- General industry questions
- DIY or self-service intent
- Average/typical/benchmark queries
- Forum or Reddit-seeking queries

### Off-Brand
Completely unrelated to the business. These should be added as negative keywords immediately.

**Signals:**
- Different industry entirely
- Wrong product/service category
- Wrong geographic area (if geo-specific business)
- Misspellings that match unrelated terms
- Adult, illegal, or irrelevant content

## Classification Rules

1. **Context is required.** Always ask what the business does and where it operates before classifying. A term like "pool maintenance" is High Intent for a pool company and Off-Brand for an apartment complex.

2. **When in doubt between High and Low Intent, choose Low Intent.** False positives (keeping a bad term) cost more than false negatives (losing a marginal term). Conservative classification protects budget.

3. **Brand terms are always High Intent** if they match the business's own brand name. Competitor brand terms are Low Intent.

4. **Location matters.** "Apartments in Austin" is High Intent for an Austin property. The same query is Off-Brand for a property in Denver.

5. **One category per term.** Do not assign multiple categories. Pick the most accurate one.

6. **Classify the intent, not the word.** "Cheap apartments" has High Intent even though "cheap" seems negative — the searcher wants an apartment.

## Output Format

Present results as a table:

| Search Term | Category | Reasoning |
|-------------|----------|-----------|
| [term] | [High Intent / Low Intent / Informational / Off-Brand] | [One sentence explaining why] |

After the table, provide a summary:
- **High Intent:** X terms (X%) — keep these
- **Low Intent:** X terms (X%) — monitor, consider negatives for high-spend terms
- **Informational:** X terms (X%) — usually negative unless targeting top-of-funnel
- **Off-Brand:** X terms (X%) — add as negative keywords immediately

## Batch Processing

For large lists (100+ terms):
1. Process in batches of 50
2. Show results after each batch
3. Ask if the user wants to continue or adjust the classification criteria
4. At the end, provide the full summary

## What NOT to Do

- Do NOT classify without knowing the business type and location
- Do NOT use pattern matching or regex — use judgment for each term
- Do NOT mark brand terms as Off-Brand just because they contain a competitor name
- Do NOT auto-generate negative keyword lists without user review
- Do NOT assume the business offers services that haven't been confirmed
