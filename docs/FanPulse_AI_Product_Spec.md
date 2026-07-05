# FanPulse AI — Product Definition & Feature Spec
### The "what it is and how it works" document (companion to the Build Bible)
*Anchored to Hackathon Problem Statement 5: "Fan Behavior and Engagement Intelligence for FIFA Events"*

---

## 0. What this document is

The Build Bible answers *how do we build it*. This document answers the questions that actually win a hackathon:

- **What is the product**, precisely, and who uses it
- **How it works end-to-end** — what data goes in and what comes out at every stage
- **The features**, each defined as an *input → analysis → decision*, not just a chart
- **How the numbers are actually computed** — the ROI/prediction math, with real data behind it (§6)
- **How the AI actually decides** what marketing and content to recommend (§7)
- **The exact industries** we serve (§8)
- **The USPs** — why this beats the ten other sentiment dashboards in the room
- **A direct map** from the problem statement to a feature that satisfies it

Read sections 1–7 before building anything. The rest is reference.

> **Scope boundary (read first):** FanPulse AI is a **marketing intelligence platform for brands and advertisers.** We do **not** build logistics, crowd control, venue staffing, or any physical event operations. Every feature exists to drive a *marketing* decision — who to target, what to say, when, on which channel, and what it will return.

---

## 1. The reframe: from "sentiment dashboard" to "marketing decision engine"

The single most important idea in this document:

> **FanPulse AI is not a dashboard that shows fan sentiment. It is a marketing decision engine that turns fan behaviour into specific, evidence-backed campaign decisions — and shows its work for every one of them.**

A sentiment dashboard says *"Brazil fans are 96% positive right now."* That is fluff. Every team will build that.

A decision engine says:

> *"Brazil sentiment just jumped +26 points to 96% joy after the 78th-minute goal. The **Deal-Seeker** segment in Brazil is 340k people who historically convert at ~4.5% on time-limited push offers during a high-emotion moment. **Recommended action:** fire the food-delivery flash campaign now, to this segment, on push + Instagram, projected ROAS 2.3× (vs 0.8× at a normal moment). Window closes in ~15 min."*

Same underlying sentiment number. The difference is the **decision, the target, the timing, the predicted return, and the evidence trail** attached to it. That is the whole product.

### 1.1 One-liner
FanPulse AI turns live and historical fan behaviour into audience forecasts, fan segments, and evidence-backed marketing and content decisions for the brands that advertise around FIFA events — before, during, and after every match.

---

## 2. Who it's for

The primary user is the **brand / advertiser / agency / content creator** who wants to market around a FIFA event. FIFA's own commercial team is just *one* such advertiser (selling and enabling its sponsors) — not our main persona, and we do none of their event operations.

| Persona | Who they are | What they open the app to do |
|---|---|---|
| **Brand marketer** (primary) | Growth/performance marketers at brands that advertise around football (food delivery, apparel, beverages, streaming, telecom…) | Find the right fan segment + moment + message + channel, and know the projected ROI *before* spending |
| **Agency / media buyer** (primary) | Runs campaigns for multiple brands | Allocate spend across matches and moments to the highest-ROI windows; simulate budgets |
| **Content creator / influencer** (primary) | Creators who monetise attention around football | Get real-time trend, emotion, and content-idea signals to post timely, growth-driving content |
| **Analyst** (supporting) | Brand/agency data team | Explore the segments, engagement drivers, and evidence behind every recommendation |

> The brand/industry selector from the old plan stays — it makes the demo richer (different copy and ROI per industry). Framed correctly, it's "pick your brand vertical, get your campaign."

---

## 3. The data strategy — real vs. synthetic, and the replay-engine question answered

You raised the sharpest question in the brief: *if we're going to demo off a synthetic replay engine anyway, what's the point of connecting real APIs? Is the spirit of the app in the data collection or the analysis?*

### 3.1 The answer

**The spirit of the app is in the analysis and the decisions. But the real APIs are non-negotiable, and the replay engine is not a synthetic substitute for them — they do two different jobs.**

1. **Real-time ingestion from real APIs is genuinely part of the product and runs live.** Reddit (r/soccer, team subs), YouTube live chat, and news are ingested *live*. This proves the hard, credible thing: that your NLP pipeline works on real, messy, multilingual fan text — not clean fake rows. Reddit is *always* active, so you can always show a genuinely live feed. **You are not faking data collection. You do it for real.**

2. **The replay engine is a DVR, not a data-faker.** Its input is **real data you captured earlier from those same APIs during an actual live match**, saved to JSON with timestamps. It exists to solve *timing*, not *authenticity*: a live match won't score a goal at 0:45 of your 2-minute demo slot, and the room's wifi may die. The replay engine re-plays a *real* captured match on a controlled clock so the goal moment lands exactly when your narrative needs it. **It is time-shifted real data, not invented data.**

3. **Synthetic data is used only where the real data is legally private and has no free public source** — ticketing logs, individual fan CRM profiles, campaign-performance history. Nobody can fault you for synthesising FIFA's private ticket sales; that data is *supposed* to be private.

The honest three-way split:

| Layer | Source in our build | Why this choice is correct |
|---|---|---|
| Live social/engagement text | **Real** — Reddit, YouTube live chat, news APIs, live | The credible core; the pipeline must handle real messy text |
| The "goal moment" you demo | **Real, captured, time-shifted** via the replay engine | Live sport won't perform on cue; wifi may die; this is a DVR of real reactions |
| Historical attendance / audience stats | **Real** — public FIFA/Kaggle/Wikipedia datasets | These exist publicly and ground the demand model (§6.4) |
| Marketing benchmarks (CPM/CTR/CVR/AOV) | **Real** — published industry benchmark data | This is what makes ROI *grounded, not random* (§6) |
| Ticketing sales logs & live sales curve | **Synthetic** | Private FIFA data, no public API — legitimately simulated |
| Fan CRM profiles (demographics, spend, clickstream) | **Synthetic** | Personal data, no public source — legitimately simulated |

### 3.2 The line that neutralises the objection in front of judges

> *"Our social ingestion is live and real — here's a live Reddit feed classifying right now. For the match-moment demo we replay a real match we captured earlier, so the goal lands on cue and the demo survives a wifi drop. The only data we simulate is what's genuinely private in the real world — ticket sales and fan profiles — and even our ROI numbers are built on published industry ad benchmarks, not random values."*

### 3.3 Capture the replay once, early
Run your real Reddit/YouTube connectors during *any* live football match before or in hour 2–3 of the hackathon, dump the classified messages to `data/replay_data.json` with `t_offset` timestamps, and tag the three narrative beats (goal, controversy, full-time). Now the demo is real data on a deterministic clock. (Build Bible §4.)

---

## 4. How it works — end-to-end pipeline, with data in/out at every stage

Follow one fan message and one match through the system.

```
STAGE 0  SOURCES            STAGE 1  INGEST         STAGE 2  NLP ENRICH        STAGE 3  AGGREGATE        STAGE 4  DECIDE           STAGE 5  SERVE
─────────────────           ──────────────          ──────────────────         ─────────────────         ────────────────         ──────────────
Reddit / YouTube  ─┐        fetch → clean →         sentiment (RoBERTa)        roll up per: match,       audience forecast (ML)   REST + WebSocket
News APIs          ├──────► dedupe → geo-tag ─────► emotion (DistilRoBERTa)──► minute, country,     ───► segment activation  ───► React dashboard
Replay engine     ─┤        → normalise →           topics/entities (KeyBERT)  segment, topic            campaign generation      (6 pages)
(real, captured)   │        queue                   → geo inference            → snapshots + KPIs        ROI / media planning
Synthetic CRM /   ─┘                                                                                     (§6, §7)
benchmarks (batch)
```

| Stage | Input | What happens | Output (and where it's stored) |
|---|---|---|---|
| **0 · Sources** | — | Live polling of Reddit/YouTube/news every 15–30s; replay engine streams captured JSON on its clock; synthetic CRM + real benchmark tables loaded once at startup | Raw text + metadata; static reference tables |
| **1 · Ingestion** | Raw source payloads | Clean, deduplicate, language-note, infer country (subreddit, YouTube geo, flag emoji, language), attach `match_id` | `raw_messages` rows in Postgres |
| **2 · NLP enrichment** | One cleaned message | Local models classify sentiment (pos/neg/neu + score), emotion (joy/anger/fear/…), topics & entities (players, "VAR"), all on CPU, no network | `nlp_results` rows |
| **3 · Aggregation** | Stream of classified messages | Roll up % sentiment, dominant emotion, mention **volume & velocity** (how "moments" are detected), per country, topic, segment; snapshots every 15–30s | `sentiment_snapshots`, `country_sentiment`, Redis KPI cache; **moment tags** (goal, red_card, full_time) inferred from spikes |
| **4 · Decision layer** | Aggregates + synthetic CRM + real benchmarks | Four engines fire: (a) **audience/demand forecast** incl. the live sentiment feature (§5 F3); (b) **fan segmentation & scoring** (F4); (c) **strategy engine + RAG campaign/content generation** (§7); (d) **ROI / media-spend model** (§6) | `campaigns`, `predictions` rows; Redis pub/sub |
| **5 · Serve** | Aggregates + decisions | FastAPI exposes the REST contract; WebSocket fans out `kpi_update`, `new_message`, `topic_trend`, `campaign_alert` live | JSON to the React dashboard |

**The rule that keeps 3 people unblocked:** ingestion/NLP write *only* to Postgres/Redis; API and frontend talk *only* through the frozen contract (Build Bible §3, §5).

---

## 5. The features (each defined as a decision, not a chart)

Each feature is **Input → Analysis → Output → the Decision it produces → the Evidence it shows**. The "Evidence" line is the anti-fluff mechanism — every output carries the data trail that justifies it.

---

### Feature 1 · Live Fan Sentiment, Emotion & Moment Detection
*The real-time engine. The beating heart of the demo.*

- **Input:** live + replayed fan messages, continuously.
- **Analysis:** per-message sentiment + emotion + topic classification (local models); aggregation into rolling %s, dominant emotion, mention **volume and velocity**. A **moment detector** watches for spikes: sudden volume jump + emotion swing = a match event. The data triggers it — no manual "trigger goal" button.
- **Output:** live KPI strip (mentions, +/−/neutral %, top emotion, excitement score, most-active region), emotion timeline, trending-topics ticker.
- **Decision it produces:** *"A high-emotion moment is happening now"* — the trigger that wakes up Features 5 and 6.
- **Evidence shown:** the raw classified messages scrolling live — real text → real classification → real aggregate.

**Why it's not fluff:** velocity-based moment detection turns sentiment into a *timing signal* for marketing.

---

### Feature 2 · Global Fan Emotion Heatmap
*Highest visual-impact-per-dev-hour feature.*

- **Input:** geo-tagged classified messages.
- **Analysis:** per-country average sentiment, dominant emotion, mention volume, live.
- **Output:** a choropleth map (React-Leaflet + OpenStreetMap, no API key) that flashes green where joy spikes, red where anger concentrates; click a country to drill down.
- **Decision it produces:** *where* fan attention/energy is concentrated → which regional audiences to target.
- **Evidence shown:** hover a country → its live sentiment, top emotion, message count.

**Why it's not fluff:** per-country volumes feed directly into which segments Feature 5 activates and into audience size for the ROI model.

---

### Feature 3 · Audience & Ticket-Demand Forecasting — *with a live feedback loop* (a standout USP)
*The problem statement explicitly asks to "predict ticket demand before and during matches." We do — and read it as an **attention/audience** signal for advertisers: high-demand match = high-attention match = where ad ROI is highest.*

- **Input (static):** match features — team FIFA rankings, ranking gap (closeness), stage (group/R16/QF/SF/final), rivalry flag, host-nation involvement, city population/tourism, day/time; **real** historical attendance/audience data + **synthetic** ticket-sales curves.
- **Input (dynamic — the USP):** the **live social signal** from Feature 1 — current mention volume and sentiment momentum per fanbase.
- **Model:** gradient-boosted regressor (XGBoost / sklearn), trained on the real-historical + synthetic feature table (§6.4).
- **Output:** predicted demand/audience per match, **sell-out / high-attention probability**, a demand curve, and a **feature-importance panel** ("driven most by rivalry + host involvement").
- **Decision it produces:** *"Match X will be the biggest audience — concentrate ad spend here. Match Y is under-indexing — either skip it or target its niche segment cheaply."*
- **The live loop (demo gold):** as group-stage results land and sentiment spikes, the model **re-forecasts knockout demand in real time.** *"Argentina's dramatic 3–2 in the last 20 minutes raised projected quarter-final attention +18%."* Most teams do a static one-shot prediction; the closed loop from live emotion back into the forecast is a genuine differentiator.
- **Evidence shown:** feature-importance bars + before/after forecast delta with the triggering event labelled.

---

### Feature 4 · Fan Segmentation & Engagement Scoring
*Answers "which fan segments are most active?" and "who responds to which offer?"*

- **Input:** **synthetic** fan CRM (age, country, favourite team, matches attended, tickets bought, avg spend, merch history, app sessions, email open rate, push opt-in, days-since-last-engagement, streaming minutes) **+ real** live engagement behaviour overlaid by geography/team.
- **Analysis:** KMeans clustering into **named personas** + an **engagement score** per fan (RFM-style: recency, frequency, monetary, digital activity).
- **Output:** named segments with size, value, channel preference, geography, churn risk — e.g. **Superfans**, **Traveling Ultras**, **Casual Streamers**, **Deal-Seekers**, **Lapsed Fans** — plus a live overlay: *which segment is loudest in the feed right now.*
- **Decision it produces:** a **Next-Best-Action matrix** — per segment, the recommended channel + offer + timing.
- **Evidence shown:** segment cards with defining traits + score breakdown + the "who's active now" overlay.

**Why it's not fluff:** segments are the *addressable targets* Feature 5 points campaigns at, and the score ranks who to contact first.

---

### Feature 5 · AI Marketing & Content Recommendation Engine (the core USP)
*Where §1's headline sentence gets generated. Full mechanism in §7.*

- **Input:** current match context + a detected moment (F1) + a target segment (F4) + a chosen industry (§8) + regional signal (F2).
- **Analysis:** a **deterministic strategy engine** decides *who / when / where / what-type* (from data + a marketing playbook), then a **retrieval-augmented LLM (Gemini)** writes the *copy* — grounded in the real numbers and retrieved marketing knowledge, never free-styling strategy. See §7.
- **Output:** a **campaign card** — target segment · channel · timing window · generated copy · predicted CTR/ROAS (§6) · confidence · **and the evidence trail** ("triggered because BR sentiment spiked +26pp to joy; Deal-Seeker BR = 340k; joy↔food fit high; projected ROAS 2.3× vs 0.8× baseline").
- **Two flavours:** **commercial campaigns** (the flashy auto-fired offer) and **content recommendations** (for creators / brand channels — answers "what content drives engagement?": *"Goal-celebration reels from Brazil drive 3× the engagement of pre-match analysis; post a 15s reel now"*).
- **Decision it produces:** the complete, ready-to-execute marketing action.
- **Evidence shown:** the evidence trail on every card. **No recommendation appears without showing why.**

**Guardrail:** debounce generation to ≤1 Gemini call / 10–15s; pre-generate 2–3 cards before the demo as a cache fallback (Build Bible risk register).

---

### Feature 6 · ROI Prediction & Media-Spend Planner
*The "will this actually pay off?" feature. Numbers are grounded funnel math, not random — full method in §6.*

- **6a · What-If ROI Simulator:** industry + budget slider in → predicted reach, clicks, conversions, revenue, **ROAS/ROI** out, updating live as the slider or the live moment changes. Decision: *"$100k on food-delivery into this goal moment returns ~2.3×; the same spend at a dead moment returns 0.8× — time it right."*
- **6b · Cross-Match Media Planner:** given a total budget and the audience forecasts (F3), recommend how to **split spend across matches and moments** to maximise total ROI. Decision: *"Put 60% on the two knockout fixtures with the highest projected attention and emotional intensity."*
- **Evidence shown:** the full funnel breakdown (every CPM/CTR/CVR/AOV assumption and the engagement multiplier) — see §6.5.

**Why it's not fluff:** this is the answer to "how should brands plan marketing?" — with math a marketer recognises and trusts.

---

## 6. How ROI and the predicted numbers are actually computed (no random numbers)

This section exists because you said, correctly: *we can't simulate random numbers without proof.* We don't. Every ROI figure is **standard marketing-funnel math**, parameterised by **real published ad benchmarks**, and modulated by a **multiplier computed from the live sentiment data**. Nothing is `random()`.

### 6.1 The marketing funnel model (this is how real marketers model a campaign)

```
Budget → Impressions → Reach → Clicks → Conversions → Revenue → ROAS / ROI
```

The formulas:

| Step | Formula |
|---|---|
| Impressions | `Impressions = (Budget / CPM) × 1000` |
| Reach | `Reach = Impressions / Frequency` |
| Clicks | `Clicks = Impressions × CTR_eff` |
| Conversions | `Conversions = Clicks × CVR_eff` |
| Revenue | `Revenue = Conversions × AOV` |
| Return | `ROAS = Revenue / Budget`  ·  `ROI = ROAS − 1` |

- **CPM** = cost per 1,000 impressions · **CTR** = click-through rate · **CVR** = conversion rate · **AOV** = average order value · **Frequency** = avg times a person sees the ad.

### 6.2 Where the baseline parameters come from — a real benchmark table (the "proof")

We ship a `benchmarks.csv` keyed by **(industry × channel)** with baseline values taken from **published, citeable industry benchmarks** (WordStream/Google Ads industry benchmarks, Meta/YouTube/TikTok ad benchmarks, Statista/eMarketer CPM reports, industry AOV reports). Example rows (illustrative — cite your actual sources in the repo):

| industry | channel | CPM ($) | CTR | CVR | AOV ($) |
|---|---|---|---|---|---|
| food_delivery | push | 6 | 0.9% | 3.0% | 30 |
| food_delivery | instagram | 10 | 0.8% | 2.4% | 30 |
| apparel/merch | instagram | 12 | 0.7% | 1.8% | 75 |
| streaming | youtube | 9 | 1.1% | 5.0% | 12 |
| beverages | instagram | 8 | 0.6% | 1.2% | 15 |

Because these are real benchmarks, the *baseline* ROI is already defensible before FanPulse adds anything. **This table is our evidence base — commit it with sources in comments.**

### 6.3 The FanPulse Engagement Multiplier (the actual IP — grounded, not random)

The whole thesis of the product is: **advertising into a peak fan-emotion moment performs measurably better than advertising at a dead moment.** We quantify that with a multiplier `M` applied to the baseline click/convert rates:

```
CTR_eff = CTR_baseline × M
CVR_eff = CVR_baseline × (1 + (M − 1) × 0.5)      # emotion lifts clicks more than it lifts purchase intent

M = clamp( 1 + K · Arousal · EmotionBrandFit · MomentStrength · SegmentMatch , 0.7 , 2.5 )
```

Every input to `M` is **measured from the live pipeline**, not guessed:

| Factor | Range | Where it comes from |
|---|---|---|
| **Arousal** | 0–1 | Emotional intensity from the live emotion model — high-arousal emotions (excitement, joy, anger) score high, calm/neutral score low |
| **EmotionBrandFit** | 0–1 | Lookup: how well the current dominant emotion matches the industry's ideal trigger (joy↔food/celebration = high; anger↔comfort food = medium; joy↔insurance = low). A small hand-built, defensible matrix |
| **MomentStrength** | 0–1 | Normalised mention **velocity** from Feature 1 — how big the spike is right now |
| **SegmentMatch** | 0–1 | Overlap between the currently-active audience (F2/F4) and the industry's target segment |
| **K** | constant | Calibrated so a neutral moment → `M ≈ 1` (ads perform at benchmark) and a peak goal moment → `M ≈ 1.8–2.2` |

**Why this is legitimate and not made up:** it operationalises a well-established finding in marketing research — high-arousal emotional context increases engagement and transmission (e.g., Berger & Milkman, *"What Makes Online Content Viral"*, and the broad "contextual/emotional targeting lift" literature). We're not inventing a relationship; we're applying a known one with transparent, bounded coefficients. Cite one or two of these in the repo and you can defend it to any judge.

### 6.4 The audience/demand model (Feature 3) — also real data

- **Target (real):** historical FIFA match attendance / audience figures — public (Kaggle FIFA World Cup datasets, Wikipedia attendance tables).
- **Features (real + engineered):** team rankings, ranking gap, stage, rivalry, host involvement, city size, day/time.
- **Live feature (real):** current social volume + sentiment momentum from Feature 1.
- **Model:** XGBoost/sklearn regressor trained on that table. Feature importances give the explainability panel for free.
- The only synthetic part is the *shape* of the intra-window sales curve, which is cosmetic to the demo.

### 6.5 Worked example (this is your demo slide — same budget, timing decides everything)

Food-delivery brand, **$100,000** budget, push channel.

**Advertising at a normal (dead) moment, `M = 1.0`:**
- Impressions `= 100,000/6 × 1000 = 16.7M` → Reach `= 6.7M` (freq 2.5)
- Clicks `= 16.7M × 0.9% = 150k` → Conversions `= 150k × 3.0% = 4,500`
- Revenue `= 4,500 × $30 = $135,000` → **ROAS 1.35× (ROI +35%)**

**Advertising into the goal moment, `M ≈ 1.9`** (Arousal 0.9, Fit 0.85, MomentStrength 0.8, SegmentMatch 0.7, K≈2.0):
- CTR_eff `= 0.9% × 1.9 = 1.71%`; CVR_eff `= 3.0% × 1.45 = 4.35%`
- Clicks `= 16.7M × 1.71% = 285k` → Conversions `= 285k × 4.35% = 12,400`
- Revenue `= 12,400 × $30 = $372,000` → **ROAS 3.72× (ROI +272%)**

Same brand, same budget — **timing into the emotional peak roughly triples the return.** That single comparison, built entirely from published benchmarks × a measured live multiplier, *is* the product thesis, quantified and defensible. (Tune the benchmark constants to whatever your cited sources say; the structure is what matters.)

### 6.6 Confidence scores (also not random)
`confidence = weighted average of:` volume of real messages supporting the current emotion read, strength/recency of the moment, and how well-populated the target segment is. Low data → low confidence, shown honestly. It's a data-support score, not a die roll.

---

## 7. How the AI decides — strategy engine + retrieval-augmented copy (the RAG question, answered)

You asked: *how does the LLM know what suggestions to give? Is it RAG?* Here is the exact architecture. The key idea: **the marketing *decision* is made by a deterministic, data-driven engine — not the LLM. The LLM only writes the words.** This is what makes the output trustworthy and explainable (the "glass-box" property), and yes, the copy step is retrieval-augmented.

### 7.1 Two layers

**Layer 1 — Strategy Engine (deterministic; decides WHO / WHEN / WHERE / WHAT-TYPE).**
Consumes the live analytics + the ROI model + a **Playbook**, and outputs a structured **Campaign Brief**:

- **WHO** → the highest-engagement-score, best-fit segment active right now (Feature 4).
- **WHEN** → the timing window from moment detection + a decay rule (emotional windows fade — e.g. 15 min post-goal).
- **WHERE** → the channel with the best benchmark ROI for that segment × industry (§6 table).
- **WHAT-TYPE** → a **campaign archetype** looked up from the Playbook: a curated `(emotion × industry) → archetype + offer structure + channel + window` table. Examples:

| Emotion (live) | Industry | Archetype |
|---|---|---|
| joy / excitement | food_delivery | Celebration flash offer, push+IG, 15-min window |
| anger / disappointment | food_delivery | "Drown your sorrows" consolation offer, 30-min window |
| joy | apparel / merch | "Commemorate the moment" limited drop |
| anticipation (pre-match) | streaming | "Don't miss kickoff — sign up now" tune-in push |
| joy / pride | travel | "Follow your team" fan-trip promo |

This Playbook is small, hand-built from real marketing principles, and fully explainable. **This is where the strategy lives — deterministic and auditable.**

**Layer 2 — Copy/Content Engine (LLM = Gemini; decides the WORDS only, via RAG).**
Given the Brief, it produces the creative:

1. **Retrieve** from a curated **Marketing Knowledge Base** the entries relevant to this Brief:
   - copywriting frameworks for the archetype (AIDA, PAS…)
   - the industry's brand-tone guidelines
   - high-performing example templates for that archetype × channel
   - the **live trending topics/entities** from Feature 1 (so copy references the *actual* moment/player)
2. **Augment & generate:** `Brief + retrieved snippets + strict output schema → Gemini → JSON {headline, body (≤140 chars), CTA, hashtags, 2 variants}`.
3. The LLM **never invents strategy or numbers** — it executes a brief with retrieved knowledge. That's *how it knows what good marketing looks like*: it's constrained by real data + retrieved playbook, not free-styling.

### 7.2 Is it RAG? Yes — and here's the honest version for a hackathon

- **Retrieval corpus** = the Marketing Knowledge Base (a few dozen curated entries: frameworks, tone guides, templates, the emotion→archetype playbook) **+** the live trend data.
- **Retrieval method — pick your ambition:**
  - **Baseline (recommended):** filtered key lookup — `(industry, emotion, channel)` selects the archetype and template rows. Deterministic, instant, trivially defensible. *"Structured retrieval."*
  - **Upgrade (if time):** semantic vector retrieval using the local `all-MiniLM-L6-v2` embeddings (already in the stack) over the KB. This is a **true, fully-local, free vector-RAG** — say "RAG" with a straight face.
- **Generation** = Gemini, constrained to copywriting with a strict JSON schema.

So: **a retrieval-augmented generation pipeline where a deterministic strategy layer makes the marketing decisions and a retrieval-grounded LLM writes the execution.** The "proof the suggestions are good" is that the strategy is computed from data + an established playbook, and the ROI attached is benchmark-grounded (§6).

### 7.3 Content suggestions (for creators and brand channels)
Same pipeline, archetype = "content idea." Retrieval pulls the top trending topic/entity + format best-practices → Gemini proposes concrete concepts: *"15s vertical reel — [dominant emotion] reaction to [top player]; hook in first 2s; post within 20 min while [topic] peaks in [region]."* Grounded in the real, live trend data — a creator's version of the campaign card.

---

## 8. The industries we serve (final list)

Every industry below genuinely spikes in commercial relevance around major football events. The build ships a **brand-vertical selector**; each vertical carries its own benchmark row (§6.2) and Playbook archetypes (§7.1). Focus the demo on the **top 5 (★)** and let the rest be selectable.

| # | Industry | Why football events benefit them | What FanPulse gives them |
|---|---|---|---|
| 1 ★ | **Food delivery & QSR** (Domino's, Uber Eats, McDonald's) | Match-watching = peak snacking/ordering; goal moments = order spikes | Moment-timed flash offers to Deal-Seeker/at-home segments |
| 2 ★ | **Sports merch & licensed apparel** (jerseys, scarves) | Wins/goals drive impulse "commemorate it" buys | "Limited drop" campaigns fired on joy/pride moments |
| 3 ★ | **Beverages** — beer/alcohol + soft/energy drinks | Core match-watching consumption; huge event advertisers | Region + emotion-targeted celebration/anticipation ads |
| 4 ★ | **Streaming / OTT / broadcasters** | Want sign-ups + tune-in around fixtures | Pre-match "don't miss kickoff" + tune-in pushes by segment |
| 5 ★ | **Content creators & influencers** | Monetise attention; ride the engagement wave | Real-time trend/emotion signals + content-idea recs (§7.3) |
| 6 | **Sportswear & fashion** (Nike, Adidas, Puma; fashion tie-ins) | Peak brand attention during events | Segment + moment-targeted brand campaigns |
| 7 | **Betting / fantasy sports / iGaming** *(compliance-flagged)* | One of the largest sports-ad categories | Pre-match/anticipation offers — **with a responsible-advertising flag & region gating** |
| 8 | **Gaming & esports** (EA FC, mobile/fantasy games) | Football hype converts directly to game installs | Moment-timed install/engagement campaigns |
| 9 | **Retail & e-commerce** | Flash-sale culture around big moments | Emotion-triggered time-limited promos |
| 10 | **Telecom & mobile carriers** | Major event sponsors; data/streaming upsell | Audience-targeted plan/upsell campaigns |
| 11 | **Consumer electronics** (TVs, audio) | Big matches drive big-screen upgrade purchases | Pre-tournament "upgrade for the final" campaigns |
| 12 | **Financial services / fintech / payments** | Sponsors + fans transacting around events | Segment-targeted acquisition offers |
| 13 | **Travel & hospitality** (airlines, booking platforms) | Fans travel to/around matches | "Follow your team" fan-trip promos to Traveling-Ultra segment |
| 14 | **Bars, pubs & viewing venues** | Advertise screenings/promos to nearby fans | Geo + fixture-timed "watch it here" promos *(advertising only — no venue ops)* |
| 15 | **Automotive** | Long-standing FIFA-partner category | Brand campaigns to high-value engaged segments |

> **Betting note:** include it because it's honestly one of the biggest real sports advertisers, but ship it behind a **responsible-advertising / region-gating flag** so the demo shows you thought about compliance — judges notice that maturity.

---

## 9. What makes it win — the USPs, ranked

1. **Glass-box marketing — every recommendation shows its evidence and its math.** No black-box "here's an ad." Each card carries *why now / why them / why this*, plus the funnel breakdown behind the ROI. The strongest possible answer to "is this fluff?"
2. **ROI grounded in real benchmarks × a measured live multiplier (§6).** The numbers aren't invented; they're published ad benchmarks modulated by real sentiment — and the worked example (same budget, timing triples the return) *is* the pitch.
3. **The closed loop: live emotion → live audience forecast (§5 F3).** Almost everyone does static prediction; the loop is genuinely novel.
4. **A real strategy engine, not just an LLM wrapper (§7).** Deterministic, data-driven decisions + RAG-grounded copy. Most teams will pipe sentiment straight into "ChatGPT, write an ad" — you have an auditable strategy layer.
5. **Moment-aware automation.** The system detects moments from the sentiment stream itself and auto-fires the right action per segment — timing driven by data, not a button.
6. **Demo-proof by design.** Live real ingestion + a DVR of real captured reactions + entirely free/local infra. Pull the wifi and it keeps running.

---

## 10. Judge-alignment map — problem statement → feature

| Problem statement asks for… | Delivered by |
|---|---|
| Predict ticket demand **before and during** matches | Feature 3 (static forecast + **live re-forecast loop**) |
| Understand engagement patterns across social/digital | Features 1 + 2 |
| Segment fans by behaviour/preferences/activity | Feature 4 |
| Personalize communication, offers, content | Feature 5 (strategy + RAG) + Feature 4 (Next-Best-Action) |
| *Which matches will have the highest demand?* | Feature 3 |
| *Which fan segments are most active online?* | Feature 4 × Feature 1 overlay |
| *What content drives the most engagement?* | Feature 5 content recommendations (§7.3) |
| *How should organizers plan marketing?* | Feature 5 + Feature 6 (ROI & media planner) |
| *Which fans respond to specific offers?* | Feature 4 + Feature 5 |
| Dashboard of fan behaviour trends | The whole app |
| Demand predictions | Feature 3 |
| Fan segment classification | Feature 4 |
| Engagement heatmaps & trend charts | Features 2 + 1 |
| Personalized marketing/content recommendations | Feature 5 |

> **Deliberate scope note:** the problem statement also mentions *crowd planning and venue operations.* We consciously scope that **out** — FanPulse is a marketing platform, not an operations tool. We satisfy the demand-forecasting objective by reading it as an **audience/attention signal for media planning**, which is the marketing-relevant interpretation. State this boundary confidently; a focused product beats a diffuse one.

---

## 11. The app — pages the user sees

| Page | Persona | Shows |
|---|---|---|
| **Home / Command Center** | All | Tournament overview, upcoming matches with predicted audience, the day's top recommendations, replay control |
| **Live Match** | Marketer / creator | Feature 1 KPI strip + emotion timeline + trending topics + live classified feed; the heatmap (F2); campaign alerts fire here |
| **Marketing / Campaigns** | Marketer / agency | Feature 5 campaign cards with evidence trails; industry selector; content-recommendation cards |
| **Fan Intelligence** | Analyst / marketer | Feature 4 segment cards, engagement scores, Next-Best-Action matrix, "who's active now" overlay |
| **Predictions** | Marketer / agency | Feature 3 audience forecasts + feature-importance + the live re-forecast |
| **ROI Studio / Media Planner** | Marketer / agency | Feature 6a what-if slider with the full funnel breakdown; Feature 6b cross-match spend allocation |

---

## 12. Scope realism — build tiers so you ship something that wins

**Tier 0 — the demo spine (must exist):**
- Replay engine streaming real captured data on a clock
- Local NLP (sentiment + emotion) → aggregation → live KPI + timeline
- Live heatmap
- One end-to-end campaign card with an evidence trail (Feature 5, baseline strategy engine + Gemini)
- The 6-page dashboard shell, deployed to a public URL

**Tier 1 — the USPs that win:**
- Audience forecast **with the live re-forecast loop** (Feature 3) — prioritise the loop
- Fan segments + engagement score + Next-Best-Action (Feature 4)
- **ROI simulator with the real funnel math + benchmark table + engagement multiplier (§6)** — this is what makes the ROI defensible; do not skip it
- Moment detection driving auto-fired campaigns (F1 → F5)

**Tier 2 — depth if time remains:**
- Cross-match media planner (Feature 6b)
- Semantic vector-RAG upgrade for copy (§7.2) instead of the keyed lookup
- Content-recommendation flavour of Feature 5 (the creator view)
- A second/third live connector beyond Reddit

**Safe to keep simple under time pressure:** segmentation = KMeans on a synthetic table; audience/ROI models = small gradient-boosted/funnel math; NLP = pre-trained (zero training); RAG = keyed lookup before vectors. The complexity that *reads* as impressive — the live loop, the grounded ROI, the strategy engine, the evidence trails — is orchestration, not heavy ML. Achievable in the timeframe.

---

## 13. The 30-second "why we win" summary (memorise this)

> *"Everyone else built a dashboard that tells you fans are happy. We built the marketing decision engine that tells a brand **what to do about it** — which fan segment to target, what to say to them, when, on which channel, and what it will return — and it shows the math behind every call. Our ROI isn't made up: it's real published ad benchmarks multiplied by an engagement lift we measure live from fan emotion, and we can prove that timing a campaign into a goal moment roughly triples its return. The strategy is decided by data and a marketing playbook — the AI just writes the copy, grounded in what's actually trending. It runs on real live social data and survives a wifi cut. It's not a hackathon demo — it's the first version of software a brand's marketing team could use on Monday."*
