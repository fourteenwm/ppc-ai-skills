# Website Extraction Prompt

Use this prompt with WebFetch for each website (client + competitors).

---

## Usage

```
WebFetch URL with this prompt to extract structured competitive intelligence.
Returns XML format for consistent cross-competitor analysis.
```

---

## The Prompt

```
You are a competitive intelligence analyst helping a marketing agency understand how businesses in a specific market position themselves.

Your task is to analyze a competitor's website and extract key messaging, positioning, and marketing elements. This analysis will be combined with 5 other competitor profiles to create a comprehensive market landscape report for a client.

The goal is to help our client understand:
- What claims are "table stakes" in their market (everyone says it)
- What opportunities exist (claims no one is making)
- Where they sit relative to competitors on price, quality, and emotional positioning
- What their competitors do well that they should learn from
- What gaps exist that they could own

When analyzing the website, look beyond the obvious. Read between the lines. Notice what's emphasized and what's buried. Pay attention to the emotional tone, not just the facts. Consider what a prospective customer would take away from 30 seconds on this site.

---

Analyze this website thoroughly and return your findings in the following XML format:

<competitor_profile>
  <business_name></business_name>
  <headline>The main hero text from the homepage - the first thing visitors see</headline>
  <value_proposition>Their core promise or tagline - what they want to be known for</value_proposition>

  <services>
    <service></service>
    <service></service>
    <service></service>
    <service></service>
    <service></service>
  </services>

  <trust_signals>
    <signal>Certifications, accreditations, memberships, awards</signal>
    <signal></signal>
    <signal></signal>
  </trust_signals>

  <unique_claims>
    <claim>What do they claim that feels distinctive?</claim>
    <claim></claim>
  </unique_claims>

  <proof_points>
    <point>Specific numbers: years in business, customers served, success rates</point>
    <point></point>
    <point></point>
  </proof_points>

  <social_proof>
    <review_count>Number of Google/Facebook reviews if visible, or "Not displayed"</review_count>
    <star_rating>If displayed</star_rating>
    <testimonial_themes>What do customers praise most in testimonials?</testimonial_themes>
  </social_proof>

  <risk_reversal>
    How do they reduce perceived risk? Guarantees, free consultations, "no obligation",
    money-back promises, warranties, trial periods
  </risk_reversal>

  <lead_capture>
    What free offers or lead magnets do they use? Free guides, assessments,
    consultations, downloads, newsletters
  </lead_capture>

  <emotional_triggers>
    What emotions does their messaging target? Fear, aspiration, urgency,
    exclusivity, belonging, safety, status, convenience
  </emotional_triggers>

  <objection_handling>
    What concerns do they preemptively address? Price justification,
    "why us vs competitors", common fears or hesitations
  </objection_handling>

  <call_to_action>The primary CTA text - what action do they want visitors to take?</call_to_action>

  <pricing_signals>
    Any visible prices, payment plans, "from $X", financing options,
    or "None visible" if pricing is hidden
  </pricing_signals>

  <locations>Number and type of locations</locations>
  <hours>Operating hours summary, especially if distinctive</hours>
  <target_audience>Who do they seem to be speaking to? Demographics, psychographics, situation</target_audience>

  <positioning tier="Premium | Mid-range | Budget">
    One sentence explaining why you placed them at this tier based on
    messaging, imagery, and pricing signals
  </positioning>

  <tone>
    The emotional voice of the brand: Professional, Friendly, Clinical,
    Aspirational, Luxury, Down-to-earth, Technical, Warm, Corporate, etc.
  </tone>

  <strongest_message>
    In one sentence: What is the single most compelling thing about
    this business based on their website?
  </strongest_message>

  <gaps>
    What's notably absent from their messaging? What questions would a
    prospect still have after visiting this site?
  </gaps>
</competitor_profile>

Be thorough and specific. Extract actual text and numbers where possible, not vague summaries. No commentary outside the XML. No offers to help further.
```

---

## What This Extracts

| Element | Purpose | Used In |
|---------|---------|---------|
| `business_name` | Identification | All outputs |
| `headline` | Primary messaging | Messaging matrix |
| `value_proposition` | Core promise | Positioning analysis |
| `services` | What they offer | Service comparison |
| `trust_signals` | Credibility elements | Trust gap analysis |
| `unique_claims` | Differentiation | Whitespace identification |
| `proof_points` | Quantified evidence | Specificity analysis |
| `social_proof` | Review/testimonial data | Social proof gap |
| `risk_reversal` | Risk reduction tactics | Conversion gap |
| `lead_capture` | Lead magnet offers | Tactical gap |
| `emotional_triggers` | Emotional positioning | Emotional landscape map |
| `objection_handling` | Preemptive concerns | Objection gap |
| `call_to_action` | Primary CTA | CTA analysis |
| `pricing_signals` | Price transparency | Pricing strategy |
| `locations`, `hours` | Operational details | Local analysis |
| `target_audience` | Who they speak to | Audience analysis |
| `positioning` | Market tier | Positioning map |
| `tone` | Brand voice | Tone comparison |
| `strongest_message` | Key takeaway | Executive summary |
| `gaps` | Missing elements | Opportunity identification |

---

## Example Output

```xml
<competitor_profile>
  <business_name>Smith Auto Repair</business_name>
  <headline>Honest Auto Repair You Can Trust</headline>
  <value_proposition>Family-owned since 1985, we treat your car like our own</value_proposition>

  <services>
    <service>Oil changes</service>
    <service>Brake repair</service>
    <service>Engine diagnostics</service>
    <service>Transmission service</service>
    <service>A/C repair</service>
  </services>

  <trust_signals>
    <signal>ASE Certified Technicians</signal>
    <signal>BBB A+ Rating</signal>
    <signal>AAA Approved Auto Repair</signal>
  </trust_signals>

  <unique_claims>
    <claim>Same-day service on most repairs</claim>
    <claim>Free loaner cars available</claim>
  </unique_claims>

  <proof_points>
    <point>38 years in business</point>
    <point>Over 50,000 cars serviced</point>
    <point>4.9 star Google rating</point>
  </proof_points>

  <social_proof>
    <review_count>847 Google reviews</review_count>
    <star_rating>4.9/5</star_rating>
    <testimonial_themes>Honest pricing, quick turnaround, friendly staff</testimonial_themes>
  </social_proof>

  <risk_reversal>
    "We'll explain everything before we start. No surprises on your bill."
    Free estimates on all repairs.
  </risk_reversal>

  <lead_capture>
    Free vehicle inspection with any service
    Newsletter signup for maintenance reminders
  </lead_capture>

  <emotional_triggers>
    Trust (honest, transparent), Safety (certified), Convenience (same-day),
    Belonging (family-owned, community)
  </emotional_triggers>

  <objection_handling>
    FAQ section addresses: "Will you try to upsell me?" (No, we show you the problem first)
    "How do I know I'm getting a fair price?" (We provide written estimates)
  </objection_handling>

  <call_to_action>Schedule Your Appointment Online</call_to_action>

  <pricing_signals>
    Oil change from $39.95
    Free estimates
    Financing available through Synchrony
  </pricing_signals>

  <locations>2 locations in Austin metro area</locations>
  <hours>Mon-Fri 7am-6pm, Sat 8am-4pm, Closed Sunday</hours>
  <target_audience>Austin families and professionals who want reliable, honest auto repair without dealership prices</target_audience>

  <positioning tier="Mid-range">
    Positioned as affordable alternative to dealerships with emphasis on trust and transparency rather than lowest price
  </positioning>

  <tone>Friendly, Down-to-earth, Trustworthy</tone>

  <strongest_message>
    38 years of family ownership and 847 five-star reviews prove they deliver on their "honest repair" promise
  </strongest_message>

  <gaps>
    No mention of warranty on repairs
    No emergency/after-hours service mentioned
    No mobile/at-home repair option
    Doesn't address how long repairs typically take
  </gaps>
</competitor_profile>
```

---

## Usage Notes

1. **Run in parallel** - Launch 6 Task agents simultaneously for all URLs
2. **Handle failures** - If WebFetch fails, note which URL and retry or skip
3. **Validate XML** - Check that all fields are populated before proceeding
4. **Extract actual text** - Use quotes from the website, not paraphrases
