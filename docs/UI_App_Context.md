# FanPulse AI — Application Context (for UI generation)

This document describes **what the application does and what it must display and let users do.** It intentionally contains no colors, typography, layout, or component-styling decisions — those are left entirely to the UI generation tool. Treat every section below as a functional requirement: if a data field or interaction is listed, the generated UI needs a place to show or trigger it.

---

## 1. What this application is

FanPulse AI is a **real-time marketing decision engine for brands and advertisers around live FIFA football matches.** It watches fan reactions as they happen, detects emotionally significant moments (goals, controversies, full-time, etc.), and turns each moment into a concrete, ready-to-use marketing recommendation: who to target, what to say, on which channel, for how long, and what return to expect — with the evidence behind every claim shown alongside it.

It is **not** a passive sentiment dashboard. Every screen that shows a metric should make it easy to get from "here's a number" to "here's the recommended action and why." Numbers without an explanation of where they came from are considered incomplete.

**Primary users the UI must serve:**
- **Brand marketer** — wants to find the right audience + moment + message + channel, and see projected ROI before "spending."
- **Agency / media buyer** — wants to allocate a budget across multiple matches and simulate what-if scenarios.
- **Content creator** — wants real-time trend/emotion signals and concrete content ideas (not ad campaigns).
- **Analyst** — wants to inspect the segments, model drivers, and evidence behind every recommendation.

The UI should let a user identify which persona/goal they have (or serve all of them from one flow) rather than assuming only one.

**Hard boundaries the UI must respect:**
- This tool never actually sends a push notification, posts to social media, or emails anyone. "Channel" (push / instagram / youtube / email) is always a **label** on a recommendation, describing where a human would deploy it — never a live send action. Do not design "Send now" buttons that imply real delivery; "Copy," "Export," or "Mark as used" style affordances are appropriate instead.
- There is no crowd-control, venue-operations, or logistics angle anywhere. The "demand forecast" feature is about ad/media budget allocation and audience attention, not stadium capacity planning.
- The system is explicitly demo/hackathon-scale: one match's data at a time is the common case, though multiple matches can exist concurrently.

---

## 2. Real-time behavior the UI must account for

- There is no WebSocket/push channel. All "live" data is obtained by **polling REST endpoints every 2–3 seconds.** The UI should be built around periodic refresh of live widgets (KPIs, feed, moments, campaigns) rather than assuming instantly-pushed updates — design for graceful incremental updates (e.g., new feed items appearing, counters ticking up) rather than jarring full-page reloads.
- A live match session should feel continuously "alive": counters, the sentiment timeline, the message feed, and the moment list all grow over time during a match.
- A "moment" (goal, red card, VAR controversy, full-time, other surge) can fire at any time without user action and should be able to visually announce itself (e.g., a new highlighted event) and trigger the automatic appearance of new campaign recommendation(s) tied to it — the UI should make this cause-and-effect obvious (this moment → these new recommendations).
- Some data is genuinely absent some of the time (e.g., not enough message volume yet, no forecast computed yet, no campaigns generated yet). The UI must have honest empty/low-confidence states rather than pretending data exists — never silently show a zero or placeholder number as if it were real.

---

## 3. Core data concepts the UI needs to represent

These are the entities that appear across screens. A UI tool should design components capable of displaying each, in whatever list/detail/card form fits.

### Match
A tournament fixture being tracked. Fields to display: home team, away team, kickoff time, tournament stage (group stage through final), venue city, venue capacity, live/upcoming/finished status, and (once computed) a **demand index** (0–100) and **sellout probability**. Users need to select/switch between matches if more than one exists.

### Live KPI snapshot (updates continuously during a live match)
Total mentions/messages seen so far, % positive / % negative / % neutral, the dominant emotion right now, an overall **excitement score** (0–100, a single composite "how hyped is this match right now" number), the most active country/region, and messages-per-minute. This is the "pulse" view of a match — likely the primary live dashboard.

### Sentiment timeline
A time series of sentiment composition (positive/negative/neutral %) and message volume in short time buckets across the match duration, with markers where moments (goals, etc.) occurred. Needs to communicate both the trend and the exact instant a notable event happened.

### Global fan emotion heatmap
Per-country breakdown: average sentiment (on a negative-to-positive scale), the dominant emotion in that country, and volume of mentions from that country. This is inherently geographic data — needs a way to compare countries at a glance and drill into one.

### Trending topics
A short ranked list of currently-trending keywords/hashtags/player names, each with a mention count and a trend direction (rising / falling / flat vs a few minutes ago).

### Live message feed
A scrolling/list feed of individual fan messages as they're classified, each showing: the text itself, its source, author (if available), inferred country, sentiment, emotion, and detected topics. This is the "raw evidence" view — it exists specifically so a user can verify that the aggregate numbers trace back to real messages. Messages may come from more than one source (see §6) and a source that is explicitly a simulation must be visibly labeled as such — never presented as if it were a real social post.

### Moments
A list of detected significant events during a match (goal, red card, VAR controversy, full-time, other surge), each with: when it was detected, which event type, a short auto-generated description (e.g., "Volume spike 4× with joy surge"), and the underlying momentum snapshot that triggered it (volume, dominant emotion, sentiment shift, top topics/countries at that moment). Moments are the trigger for new campaign recommendations — the UI should let a user jump from a moment to the campaign(s) it produced.

### Audience / demand forecast
Per match: a demand index (0–100), predicted attendance percentage, sellout probability, and a **feature-importance breakdown** (which factors — e.g., tournament stage, rivalry, rank gap — are driving the prediction, each with a weight). Critically, this forecast can be **re-computed live** mid-match when a big moment happens: the UI needs to show a before/after story — the baseline forecast, the new forecast, the point delta, and a plain-language description of what triggered the change (e.g., "recomputed after goal moment mo_0007"). This before/after contrast is a key selling point of the product and deserves explicit visual treatment (not just an updated number).

### Fan segments
Exactly five fan personas exist: **Superfans, Traveling Ultras, Casual Streamers, Deal-Seekers, Lapsed Fans.** For each: size (count and % share of the sample), average engagement score, average annual value, top countries, preferred contact channel, churn risk %, and a few short "defining traits" (human-readable bullet facts, e.g., "push opt-in 91%, high app sessions"). When a match is selected, each segment also shows a live "activity share" — how much of the current live conversation is attributable to that segment right now — so segments feel connected to what's happening live, not just static profiles. A model-quality indicator (silhouette score) and total sample size should be available (e.g., in a details/info affordance) but need not be prominent.

### Next-best-actions
A simple recommendation table/list: for a given segment × industry pairing, what channel, what type of campaign, what timing rule, and expected click-through rate, plus a short rationale sentence. This is a reference/browse view, distinct from the auto-generated campaign cards tied to live moments.

### Campaign recommendation card (the centerpiece output of the whole product)
This is the single most important "output" artifact in the app and deserves the richest treatment. Each card represents one complete, ready-to-use marketing recommendation and must show, together, never split across an unclear number of clicks:
- **What match and industry** it's for, and which fan **segment** it targets.
- **Which channel** it's meant for (push / Instagram / YouTube / email — a label, not a live send).
- **Timing**: a window length in minutes and when that window ends (these are time-sensitive — the UI should communicate urgency/expiry, e.g. a countdown or "expires at" indicator).
- **The generated marketing copy**: a headline, a body, a call-to-action, hashtags, and an alternate "B" variant of the same fields (for A/B-style comparison).
- **A full ROI projection** (see ROIResult below) attached to this specific campaign.
- **An evidence block** — this is a hard requirement, not optional supporting detail: what moment triggered this (with its stats), what the target segment's stats are, what the regional signal was, the full multiplier breakdown (arousal, emotion-brand-fit, moment-strength, segment-match, the resulting multiplier value), and which published benchmark the ROI numbers are grounded in (a citation string). A card without visible evidence should be treated as broken content, not a valid state.
- **A confidence score** (0–1) reflecting how much live data actually supports this recommendation — low confidence should look visibly different from high confidence, not just show a smaller number.
- Whether the copy came from **AI generation or a pre-written fallback template** (a flag) — this should be disclosed somewhere on the card (even subtly), since it affects how much weight a user should give the copy's specificity.
- Whether it was **auto-triggered by a live moment** or manually requested by the user, and if auto, a link back to the triggering moment.

New auto-generated cards can appear at any time during a live match (see §2) — the UI needs an inbox/stream-like pattern for these, not just a static list that requires a manual refresh to notice new arrivals.

Users must also be able to **manually request** a new campaign recommendation by choosing: a match, an industry, optionally a target segment, optionally a channel, optionally a budget, and optionally tying it to a specific existing moment.

### Content idea card (for the content-creator persona)
A distinct, lighter-weight recommendation type: a concrete content concept — format (e.g., "15s vertical reel"), an opening hook, a fuller concept description, suggested hashtags, and a "post within N minutes" urgency window — for a chosen platform (Instagram or YouTube). Same evidence-and-confidence philosophy as campaign cards, but the evidence here is about trending topics/timing rather than segment/ROI. Requested by choosing a match, a platform, and optionally a creator niche.

### ROI simulator result
Given an industry, channel, budget, and a timing choice (simulate at the current live moment vs. a quiet baseline), show the **entire funnel**, not just a final number: impressions → reach → clicks → conversions → revenue, plus the resulting ROAS and ROI%. Show the multiplier breakdown that produced the "live" numbers (same four factors as in campaign evidence). Critically, always show the **baseline comparison side-by-side** — same budget, no live-moment boost — so the value of timing is visually obvious as a contrast, not just implied by one number. Include the benchmark source citation and a confidence score. This is meant to be interactive/exploratory — a user should be able to change inputs and see the funnel recompute.

### Cross-match media planner result
Given a total budget, an industry, and a set of candidate matches, show how the budget should be split across those matches: for each match, its allocated budget, share % of the total, the match's demand index, expected ROAS, expected revenue, and a short rationale sentence explaining why it got that allocation (e.g., "highest demand index, rivalry fixture; capped at 60%"). Also show the overall expected blended ROAS for the whole plan. This is a comparison/allocation view — a table or proportional visual works better than isolated numbers.

### Industries
A fixed list of 15 advertiser industry categories the user chooses from whenever generating a campaign, simulating ROI, or browsing next-best-actions: Food Delivery & QSR, Sports Merch & Apparel, Beverages, Streaming/OTT, Content Creators, Sportswear & Fashion, Betting/iGaming, Gaming & Esports, Retail & E-commerce, Telecom & Mobile, Consumer Electronics, Financial/Fintech, Travel & Hospitality, Bars/Pubs & Venues, Automotive. Five of these (Food Delivery, Merch/Apparel, Beverages, Streaming/OTT, Content Creators) are the primary demo focus and have the richest data behind them — the rest are supported but thinner. One industry (Betting/iGaming) carries a **compliance flag** that the UI should surface as a visible notice/badge wherever that industry is selected (e.g., a regional-restriction disclaimer), since it's a regulated ad category.

---

## 4. Functional flows the UI needs to support

1. **Pick/switch a match** and land on a live "pulse" view combining the KPI snapshot, sentiment timeline, trending topics, and live message feed for that match, all auto-refreshing.
2. **Browse detected moments** for a match, see the stats behind each, and jump from a moment to the campaign card(s) it triggered.
3. **View the country/emotion heatmap** for a match and drill into any single country's numbers.
4. **View the current demand forecast** for a match, including its feature-importance drivers, and see it visually update (with a delta and trigger explanation) when a live re-forecast happens.
5. **Browse fan segments** (with live activity overlays when a match is selected) and the next-best-action reference table by industry.
6. **Watch a stream of auto-generated campaign cards** arrive as moments happen, each fully self-contained with copy + ROI + evidence + confidence.
7. **Manually generate** a new campaign card (choosing match, industry, and optional segment/channel/budget/moment) or a content idea card (choosing match, platform, optional niche).
8. **Run the ROI what-if simulator** interactively (industry, channel, budget, timing) and compare live-moment vs. baseline funnels.
9. **Run the cross-match media planner** (budget, industry, candidate matches) and see the resulting allocation and rationale per match.
10. **See system/data health**: whether ingestion is currently active/alive for a match, and which industries exist (with their starred/compliance-flag status) — useful for a settings/status area rather than the main flow.

---

## 5. Fixed vocabularies the UI will need to render as labels, filters, or selectors

- **Sentiment:** positive, negative, neutral
- **Emotion:** joy, anger, surprise, fear, disgust, sadness, neutral
- **Event/moment type:** goal, red card, VAR controversy, full time, kickoff, other surge
- **Fan segment:** superfans, traveling ultras, casual streamers, deal-seekers, lapsed fans
- **Channel (label only, never a live send):** push, Instagram, YouTube, email
- **Campaign archetype (drives what kind of recommendation a card represents):** celebration flash offer, consolation offer, commemorative drop, tune-in push, fan trip promo, watch-it-here, install/play, flash sale, brand awareness, content idea
- **Data source of a message (must be distinguishable in the feed, especially the simulated one):** Reddit, YouTube, news, replay (recorded demo fixture), simulated Twitter/X (explicitly a labeled simulation, never shown as real)
- **Match status:** upcoming, live, finished
- **Industries:** the 15 listed in §3, with 5 marked as primary/richest-data and 1 (betting/iGaming) carrying a compliance flag

---

## 6. Data-honesty cues the UI should preserve

The product's credibility depends on never implying more certainty or authenticity than actually exists. Whatever UI is generated should keep these distinctions visible rather than flattening them away:
- A confidence score exists on forecasts, campaigns, content ideas, and ROI results — it should influence how prominently/assertively a result is presented, not be a buried decimal.
- Campaign/content copy discloses whether it came from AI generation or a fallback template.
- The simulated social-media source is always labeled as simulated.
- Every campaign, content idea, forecast, and ROI result carries an evidence/rationale trail back to real measured data or a cited benchmark — this evidence should be reachable from the card itself, not hidden behind unrelated navigation.
- Empty or insufficient-data states (e.g., not enough live volume yet to compute momentum, no forecast yet) should read as legitimate "not enough data yet" states, not as errors or zeros.
