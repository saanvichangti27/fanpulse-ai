# FanPulse AI — Product Specification & Application Context
### Primary context document for the AI build agents
*Read together with `Work_Distribution.md` (who builds what, where) and `API_Contract.md` (frozen interfaces). The three documents are the complete instruction set: this one tells you WHAT the application is and WHY each part exists; the other two tell you HOW it is divided and WHERE the seams are.*

**Document precedence if anything conflicts:** `API_Contract.md` > `Work_Distribution.md` > this document. Anything in the old Build Bible that contradicts these three is superseded.

**How to use this document as an agent:** every feature you build must trace back to a section here. If you find yourself building something this document does not describe, stop — you are out of scope. If this document is ambiguous about a value or shape, the contract resolves it; if the contract is silent too, surface the question to the humans rather than inventing.

---

## 1. What the application is

**FanPulse AI is a marketing decision engine for brands and advertisers operating around FIFA events.** It ingests live fan reactions and historical/behavioural data, and outputs specific, evidence-backed marketing decisions — who to target, what to say, when, on which channel, and what return to expect.

It is explicitly **not** a sentiment dashboard. A dashboard reports *"Brazil fans are 96% positive."* This system outputs:

> *"Brazil sentiment jumped +26pp to 96% joy after the 78th-minute goal. The **deal_seekers** segment in BR (340k fans, avg engagement 71, preferred channel push) historically responds to time-limited offers in high-emotion windows. **Action:** food-delivery flash campaign, push + Instagram, 15-minute window, projected ROAS 2.3× vs 0.8× baseline. Evidence attached."*

Every output must have that shape: **decision + target + timing + predicted return + evidence trail.** The canonical structured form is the `CampaignCard` (contract §B.7).

### 1.1 The two product theses (everything serves these)

1. **Glass-box marketing:** no recommendation is ever shown without its evidence — the measured moment, the segment stats, the multiplier breakdown, the benchmark source. This is a hard invariant (§9.1), not a styling choice.
2. **Timing is worth money:** advertising into a peak fan-emotion moment measurably outperforms advertising at a quiet moment. The system detects those moments live and quantifies the difference (§6).

### 1.2 Hard scope boundaries (guardrails)

- **Marketing only.** No logistics, crowd control, venue staffing, or physical event operations, ever. The demand forecast (Feature 3) exists as an *audience/attention signal for media planning*, not for crowd planning.
- **Primary users are brands, advertisers, agencies, and content creators** — not FIFA operations. FIFA's commercial team is just one possible advertiser.
- **No channel integrations.** Channels (push, instagram, youtube, email) are *labels on recommendation cards* and keys in `benchmarks.csv`. The system never sends a push notification, never posts anywhere. See contract §A.4 note.
- **No frontend in the current phase.** Swagger UI, `scripts/dev_console.html`, and smoke tests are the only UI-adjacent artifacts (Work Distribution §0.4).
- **The only external APIs in the entire system:** Reddit (PRAW), YouTube Data API v3, NewsAPI/GNews, and Google Gemini. Adding any other external dependency is out of scope.

### 1.3 Users

| Persona | What they use the system for |
|---|---|
| **Brand marketer** (primary) | Find the right segment + moment + message + channel; see projected ROI before spending |
| **Agency / media buyer** (primary) | Allocate budget across matches and moments; run what-if simulations |
| **Content creator** (primary) | Real-time trend/emotion signals + concrete content-idea recommendations |
| **Analyst** (supporting) | Inspect the segments, drivers, and evidence behind every recommendation |

---

## 2. Data strategy — what is real, what is replayed, what is synthetic

This split is deliberate and must be preserved exactly. Do not "improve" it by faking a real layer or wiring a live API where synthetic data is specified.

| Layer | Source | Rationale |
|---|---|---|
| Live social/engagement text | **Real, live** — Reddit, YouTube live chat, news APIs | The credibility core: the NLP pipeline must demonstrably handle real, messy, multilingual fan text. Reddit is always active, so a genuinely live feed is always demoable. |
| The demo "goal moment" | **Real, captured, time-shifted** — the Replay Engine streams fan messages captured earlier from the same real APIs during an actual match, on a controlled clock | Solves *timing*, not authenticity: live sport won't score on cue during a 2-minute demo, and venue wifi can die. This is a DVR of real reactions, **not** invented data. Replayed messages keep their true source (`reddit`/`youtube`) — the `replay` source value is reserved for the hand-written dev fixture only (contract §E.6). |
| Historical attendance/audience stats | **Real, public** — Kaggle FIFA World Cup datasets, Wikipedia attendance tables | Grounds the demand model (§6.4) in real observed outcomes. |
| Ad-performance baselines (CPM/CTR/CVR/AOV) | **Real, published** — industry benchmark reports, cited per row in `data/benchmarks/benchmarks.csv` | Makes every ROI figure defensible (§6.2). |
| Ticket-sales curves | **Synthetic** (documented generation formulas) | Real data is FIFA-private with no public API. Legitimately simulated. |
| Fan CRM profiles | **Synthetic** — 50k rows, persona-first generation (Work Distribution §5.2) | Personal data, no public source. The generation technique is documented and seeded; the persona label is dropped before clustering so segmentation honestly re-discovers structure. |

**Rule for agents:** never generate fake data for a layer marked *real*, and never call live APIs for a layer marked *synthetic*. If a real source is unavailable at runtime, degrade gracefully (log + continue) — do not substitute fabricated values.

---

## 3. System pipeline — stage-by-stage inputs and outputs

```
STAGE 0  SOURCES            STAGE 1  INGEST         STAGE 2  NLP ENRICH        STAGE 3  AGGREGATE        STAGE 4  DECIDE           STAGE 5  SERVE
─────────────────           ──────────────          ──────────────────         ─────────────────         ────────────────         ──────────────
Reddit / YouTube  ─┐        fetch → clean →         sentiment (RoBERTa)        roll up per: match,       audience forecast (ML)   REST + WebSocket
News APIs          ├──────► dedupe → geo-tag ─────► emotion (DistilRoBERTa)──► minute, country,     ───► segment activation  ───► (Swagger / dev
Replay engine     ─┤        → normalise →           topics/entities (KeyBERT)  segment, topic            campaign generation       console / smoke
(real, captured)   │        queue                   → geo inference            → snapshots + KPIs        ROI / media planning      tests; frontend
Synthetic CRM /   ─┘                                                           → momentum + moments      (§6, §7)                  comes later)
benchmarks (batch)
```

| Stage | Input | Processing | Output (storage) | Owner |
|---|---|---|---|---|
| **0 Sources** | — | Poll Reddit/YouTube/news every 15–30s; replay engine streams captured JSON on its clock; synthetic CRM + benchmark tables loaded at startup | `RawMessageIn` objects; static reference tables | W1 (live/replay), W3 (datasets) |
| **1 Ingest** | Raw payloads | Clean, dedupe by `(source, external_id)`, infer country (contract-priority heuristics), attach `match_id` | `raw_messages` rows (contract §D) | W1 |
| **2 NLP** | Cleaned messages | Local CPU models, loaded once at startup, batch inference: sentiment (`cardiffnlp/twitter-roberta-base-sentiment-latest`), emotion (`j-hartmann/emotion-english-distilroberta-base`, 7 labels per contract §A.2), topics/entities (KeyBERT + roster watchlist) | `nlp_results` rows; `ClassifiedMessage` objects | W1 |
| **3 Aggregate** | Classified stream | 15s tick: sentiment %s, dominant emotion, volume & **velocity**, per country/topic; **momentum snapshot**; **moment detection** (velocity z-score ≥ 2.5 + sentiment swing ≥ 10pp, rule locked in contract §E.4) | `sentiment_snapshots`, `country_sentiment`, `moments` rows; Redis keys §E.1; `moment_detected` pub/sub events | W1 |
| **4 Decide** | Aggregates + synthetic CRM + benchmarks + match features | Four engines: audience forecast incl. live re-forecast (§6.4); segmentation + engagement scoring + NBA (Feature 4); deterministic strategy engine + RAG copy generation (§7); ROI funnel + multiplier + media planner (§6) | `campaigns`, `content_ideas`, `forecasts` rows; `campaign_alert`/`forecast_update` events | W3 (math/models), W2 (strategy/RAG/orchestration) |
| **5 Serve** | Aggregates + decisions | REST endpoints (contract §B) + WebSocket fanout (contract §C) | JSON over HTTP/WS | W2 |

**Architecture invariant:** ingestion writes only to Postgres/Redis; the intelligence package is pure functions; the API is the only reader that assembles everything. No component ever imports another workstream's internals (Work Distribution §1).

---

## 4. The six features

Each feature is specified as **Input → Analysis → Output → Decision produced → Evidence shown**. The Evidence line is mandatory in the implementation: it is the glass-box invariant (§9.1).

### Feature 1 · Live Fan Sentiment, Emotion & Moment Detection — *owner W1*

- **Input:** live + replayed fan messages, continuously.
- **Analysis:** per-message sentiment/emotion/topic classification (local models); rolling aggregation of %s, dominant emotion, volume and velocity; **moment detector** — a spike in volume combined with an emotion swing is classified as a match event (goal, var_controversy, red_card, full_time, surge_other) using the locked rule in contract §E.4. Moments are detected *from the data*; there is no manual trigger button.
- **Output:** KPI snapshot (mentions, sentiment %s, top emotion, excitement score per the frozen formula in contract §A.6, most-active region), sentiment timeline, trending topics, live classified feed, `MomentumSnapshot` (contract §A.8 — the most-consumed payload in the system), `MomentEvent`s.
- **Decision produced:** *"a high-emotion moment is happening now"* — the trigger for Features 5 and 6 and for re-forecasting in Feature 3.
- **Evidence shown:** the raw classified messages themselves (feed endpoint + WS), so every aggregate is traceable to real text.

### Feature 2 · Global Fan Emotion Heatmap (data layer) — *owner W1 (data), W2 (serving)*

- **Input:** geo-tagged classified messages (country inference heuristics per Work Distribution §3.2c).
- **Analysis:** per-country average sentiment ∈ [−1, 1], dominant emotion, mention volume, refreshed each aggregation tick.
- **Output:** the heatmap payload (contract §B.4). The map rendering itself is future frontend work; this phase delivers the data and endpoint only.
- **Decision produced:** *where* fan energy is concentrated → regional targeting input for Feature 5 (`top_countries`, `SegmentMatch`) and audience sizing for §6.
- **Evidence shown:** per-country drill-down numbers.

### Feature 3 · Audience & Demand Forecasting with a live feedback loop — *owner W3*

- **Input (static):** match features per contract §A.8 `MatchFeatures` — stage, team ranks, rank gap, rivalry flag, host involvement, city population, venue capacity, day/time — trained against **real** historical attendance (target: `attendance_pct`).
- **Input (dynamic — the differentiator):** `buzz_index` ∈ [0,1]. At training time it is synthesized by the documented formula (Work Distribution §5.3) because historical rows have no social data; at inference time it is computed from the **real live** `MomentumSnapshot` (`compute_live_buzz`, contract §F.1). Both formulas live in docstrings — this transparency is deliberate and must be preserved.
- **Model:** XGBoost regressor (sklearn GBR fallback), 5-fold CV, metrics committed to `artifacts/metrics.json`. Feature importances are part of the API response — real ones from the model, never hardcoded.
- **Output:** `AudienceForecast` (contract §B.6): demand index 0–100, sell-out probability, feature importances, and on re-forecast the `delta_vs_baseline_pct` + `trigger_description`.
- **Decision produced:** *which matches get the ad budget* (feeds the media planner, §6), and the live story: a dramatic result measurably raises projected knockout-fixture demand.
- **Evidence shown:** feature-importance panel + before/after delta with the triggering moment named.
- **Acceptance behaviour:** a goal-level momentum snapshot must move the reforecast by **+5 to +20 demand points** (Work Distribution §5.6). If the model is insensitive to buzz, that is a bug.

### Feature 4 · Fan Segmentation & Engagement Scoring — *owner W3*

- **Input:** the synthetic 50k-row fan CRM (`data/synthetic/fans.csv`, schema and persona-first generation technique locked in Work Distribution §5.2) + live country-volume data for the activity overlay.
- **Analysis:** StandardScaler → KMeans (k chosen by silhouette from 3–8; expected 5) → clusters mapped by centroid rules onto the five fixed persona slugs (contract §A.5: `superfans`, `traveling_ultras`, `casual_streamers`, `deal_seekers`, `lapsed_fans`). Per-fan **engagement score**: RFM-D, four 0–100 percentile subscores weighted 0.25 each (contract §F.2).
- **Output:** `Segment` objects (size, share, avg engagement, avg value, top countries, preferred channel, churn risk, defining traits); **Next-Best-Action matrix** per (segment × industry); **active-now overlay** computed from live country volumes.
- **Decision produced:** *who* every campaign targets and who to contact first.
- **Evidence shown:** segment cards carry defining traits + score composition; the overlay names its basis ("country-volume overlap with segment geography").

### Feature 5 · AI Marketing & Content Recommendation Engine — *owner W2*

The core of the product. Two strictly separated layers (full architecture in §7):

- **Input:** match context + a `MomentEvent` (auto path) or manual request + target industry (§8) + segment data (F4) + regional signal (F2) + ROI math (F6).
- **Analysis:** **Layer 1, the deterministic strategy engine**, decides WHO / WHEN / WHERE / WHAT-TYPE from data + the playbook — no LLM involvement. **Layer 2, the retrieval-augmented copy engine (Gemini)**, writes only the words, grounded in retrieved marketing knowledge + live trending topics, under a strict JSON schema.
- **Output:** `CampaignCard` (contract §B.7) — segment, channel, window, generated copy with A/B variant, full `ROIResult`, confidence, and the complete evidence block. Second flavour: `ContentIdeaCard` for creators (`content_idea` archetype, contract §B.7).
- **Decision produced:** the complete, ready-to-execute marketing action.
- **Evidence shown:** the `evidence` block is a required, non-empty field — moment stats, segment stats, regional stats, multiplier breakdown, benchmark citation.
- **Auto path:** `moment_detected` → strategy engine for the configured industries → persist → `campaign_alert` on WS. Debounced per contract §A.6 constants; on any LLM failure, serve a KB template with `llm_fallback: true` — never an unresolved error in the recommendation path.

### Feature 6 · ROI Prediction & Media-Spend Planner — *owner W3 (math), W2 (endpoints)*

- **6a What-If Simulator:** `(industry, channel, budget, timing)` in → full `ROIResult` out, including the funnel breakdown at the live multiplier **and** the baseline comparison side-by-side (contract §B.8). The before/after contrast is the product thesis quantified — both modes must always be computed.
- **6b Cross-Match Media Planner:** total budget + industry + candidate matches in → allocation across matches proportional to `demand_index × expected_M`, greedy, 60% single-match cap, with per-match expected returns and a rationale string per allocation.
- **Evidence shown:** every intermediate funnel number (impressions, reach, clicks, conversions), every multiplier factor, and the benchmark source string. Nothing is a bare final number.

---

## 5. Why the design is shaped this way (context agents need for good judgement)

- **The hackathon problem statement** ("Fan Behavior and Engagement Intelligence for FIFA Events") asks for: demand prediction before/during matches (→ F3), engagement-pattern understanding (→ F1/F2), AI segmentation (→ F4), personalized offers/content (→ F5 + F4 NBA), heatmaps/trends (→ F2/F1), and marketing recommendations (→ F5/F6). Crowd/venue operations appear in the statement but are **deliberately scoped out** — the demand forecast satisfies that objective in its marketing interpretation. Do not re-introduce ops features.
- **The demo constraint shapes engineering:** the judged demo is ~2 minutes and must survive a dead network. Hence: local NLP models (no inference API), the replay engine (moment lands on cue), Gemini debounce + pre-generated fallback cards, and everything demoable from replay alone. Robustness under a wifi cut is a feature, not an accident — the "kill the wifi" test in W1's Definition of Done exists for this.
- **Differentiators to protect** (if a shortcut would weaken one of these, don't take it): (1) evidence trails on every output; (2) the live emotion→forecast loop; (3) data-driven moment detection with auto-fired campaigns; (4) the deterministic strategy layer — the system must never look like "sentiment piped into an LLM prompt"; (5) benchmark-grounded ROI with visible math.

---

## 6. ROI and prediction computation — the exact specification

Nothing in this section may be replaced by placeholder or random values. Every number is either (a) industry-standard funnel arithmetic, (b) a published benchmark with a citation, or (c) a measured live signal passed through a documented, bounded formula.

### 6.1 Funnel model

Chain: `Budget → Impressions → Reach → Clicks → Conversions → Revenue → ROAS/ROI`.

| Step | Formula |
|---|---|
| Impressions | `Impressions = (Budget / CPM) × 1000` |
| Reach | `Reach = Impressions / Frequency` |
| Clicks | `Clicks = Impressions × CTR_eff` |
| Conversions | `Conversions = Clicks × CVR_eff` |
| Revenue | `Revenue = Conversions × AOV` |
| Return | `ROAS = Revenue / Budget` · `ROI = ROAS − 1` |

Definitions: **CPM** cost per 1,000 impressions; **Frequency** average exposures per person; **CTR** click-through rate; **CVR** conversion (purchase) rate among clickers; **AOV** average order value. This is the standard media-plan arithmetic reported by all ad platforms — the structure needs no defense, only the parameters do.

### 6.2 Parameters — `data/benchmarks/benchmarks.csv`

Keyed by `(industry, channel)`, columns per Work Distribution §5.4: `industry, channel, cpm_usd, ctr, cvr, aov_usd, frequency, source, source_url`. Values come from published benchmark reports (WordStream/LocaliQ Google Ads benchmarks, Meta/YouTube ad benchmark reports, Statista/eMarketer CPM data, industry AOV studies). **Every row must carry a real citation**; where a niche pair has no published figure, interpolate from the nearest category and mark `source="interpolated"`. An unknown pair at runtime raises `BenchmarkNotFound` (contract §F.3) — never a silent default.

### 6.3 The engagement multiplier `M` (the "hype dial")

Thesis: ads shown into a peak-emotion moment outperform the same ads at a quiet moment. `M` scales the benchmark rates:

```
M       = clamp( 1 + K · Arousal · EmotionBrandFit · MomentStrength · SegmentMatch , 0.7 , 2.5 )   # K = 2.0
CTR_eff = CTR_baseline × M
CVR_eff = CVR_baseline × (1 + (M − 1) × 0.5)      # hype lifts clicks more than purchase intent
```

Constants live in `contracts/constants.py` (§A.6) — import them, never re-declare. All four factors are **measured**, each ∈ [0,1]:

| Factor | Source |
|---|---|
| `Arousal` | `AROUSAL[momentum.dominant_emotion]` from the shared constant table (same table W1 uses for the excitement score — they must never diverge) |
| `EmotionBrandFit` | `data/benchmarks/emotion_brand_fit.csv` lookup (industry × emotion → 0–1, hand-built matrix with rationale column, all 15 × 7 populated) |
| `MomentStrength` | `clip(momentum.velocity_zscore / 4, 0, 1)` |
| `SegmentMatch` | overlap of live-active countries with the target segment's geography/affinity (formula documented in `multiplier.py`) |

Interpretation anchors: quiet moment → `M ≈ 1` (benchmark performance); peak goal moment → `M ≈ 1.8–2.2`; hard bounds [0.7, 2.5] guarantee no absurd outputs. Baseline mode (`timing="baseline"` or missing/stale momentum) forces `M = 1.0`.

**Epistemic status (also state this in the repo README):** the funnel formulas are industry-universal; the benchmark values are published and cited; the emotion→performance *relationship* is established research (Berger & Milkman 2012, *Journal of Marketing Research*; Nielsen ad-context studies); the *coefficients* of `M` are our own transparent, conservatively-bounded model of that relationship. Label it exactly that way — a declared modelling choice with hard bounds is more credible than fake precision.

### 6.4 Audience/demand model

Trained on real public historical data (Kaggle FIFA World Cup matches + Wikipedia attendance), target `attendance_pct`, features per contract §A.8 `MatchFeatures`. The `buzz_index` feature: synthesized at training time via the documented formula (`0.40·stage_norm + 0.25·rivalry + 0.20·(1 − rank_gap_norm) + 0.15·host_involved + N(0, 0.05)`, clipped [0,1]); computed at inference time from real live momentum (`0.6·volume_percentile + 0.4·norm_velocity`, clipped). CV metrics committed and exposed via the API (`model_cv_mae`).

### 6.5 Numeric acceptance case (treat as a test fixture)

Food-delivery, push, **$100,000**, benchmark row `CPM=6, freq=2.5, CTR=0.009, CVR=0.03, AOV=30`:

- **Baseline (`M=1.0`):** 16.67M impressions → 6.67M reach → 150k clicks → 4,500 conversions → $135,000 revenue → **ROAS 1.35**.
- **Goal moment (`M≈1.92`** from Arousal 0.90, Fit 0.85, MomentStrength 0.80, SegmentMatch 0.70, K 2.0): CTR_eff 1.73%, CVR_eff 4.38% → ≈288k clicks → ≈12,600 conversions → ≈$378k revenue → **ROAS ≈ 3.7**.

`intelligence/roi` must reproduce these within rounding (W3 Definition of Done). The baseline-vs-moment contrast — same budget, timing roughly triples the return — is the quantified product thesis.

### 6.6 Confidence scores

Data-support scores, never random: `confidence = clip(0.4·volume_support + 0.3·moment_recency + 0.3·segment_support, 0, 1)` with the component formulas in contract §F.3. Baseline-mode confidence is fixed at 0.75. Low data must produce visibly low confidence — do not floor it cosmetically.

---

## 7. Recommendation engine architecture (Feature 5 internals)

**Prime invariant: the LLM never makes marketing decisions and never produces numbers. Strategy is deterministic; the LLM only writes copy.**

### 7.1 Layer 1 — Strategy Engine (deterministic, auditable)

Input: a `MomentEvent` (auto) or a manual generate request. Output: a `CampaignBrief` (contract §G.1). Steps (Work Distribution §4.3c):

1. **WHO** — rank segments by `industry_affinity × country_overlap_with_active_regions × avg_engagement_score`; honor an explicitly requested segment.
2. **WHEN** — window from the playbook archetype, anchored at the moment timestamp.
3. **WHERE** — best benchmark-ROI channel for (industry × segment preference) via `intelligence.roi.api.best_channel`.
4. **WHAT-TYPE** — archetype from the **playbook**: a hand-curated `(emotion × industry) → archetype` table in `app/strategy/playbook.py` covering all 15 industries × 7 emotions (weak fits fall back to `brand_awareness`). Representative rows: joy × food_delivery → `celebration_flash_offer` (15-min window); sadness/anger × food_delivery → `consolation_offer`; joy × merch_apparel → `commemorative_drop`; pre-match anticipation × streaming_ott → `tune_in_push`; joy × travel_hospitality → `fan_trip_promo`.
5. Attach `ROIResult` (live + baseline) and assemble the evidence block from the momentum snapshot, segment stats, and multiplier breakdown.

### 7.2 Layer 2 — Copy engine (retrieval-augmented Gemini)

1. **Retrieve** from the curated knowledge base (`app/rag/knowledge_base/`, 25–40 markdown entries with YAML frontmatter `{archetype, industry, channel, type}`): the archetype's copywriting framework (AIDA/PAS), the industry tone guide, 2–3 example templates — plus the **live** trending topics/entities so copy references the actual moment and players. Baseline retrieval = deterministic frontmatter filtering (top-k 4); optional upgrade = local `all-MiniLM-L6-v2` vector similarity (only after everything else works).
2. **Generate** with Gemini (`gemini-2.5-flash`, strict JSON mode, schema in contract §G.2): headline, body ≤140 chars, CTA, hashtags, one B-variant. The prompt (contract §G.3) instructs: *use only the numbers provided; never invent statistics.*
3. **Guardrails:** server-side debounce (≥12s between calls, contract §A.6); response cache keyed `(match, archetype, industry, segment)`; on any failure → filled KB template with `llm_fallback: true`. The recommendation path must never surface an unresolved LLM error.

### 7.3 Content flavour (creators)

Same two layers with `archetype="content_idea"` and platform `instagram | youtube`: retrieval pulls the top trending topic + format best-practices; output is a concrete concept (format, hook, concept, hashtags, `post_within_minutes`) grounded in the live trend data. Serves `POST /content/generate`.

---

## 8. Industries (final list — slugs are contract §A.7, do not rename)

Starred (★) industries are the demo focus and must have complete playbook rows, KB templates, and benchmark rows first; the rest need at least benchmark + playbook coverage.

| slug | display | ★ | Event relevance → what FanPulse gives them |
|---|---|---|---|
| `food_delivery` | Food Delivery & QSR | ★ | Match-watching = peak ordering; goal spikes → moment-timed flash offers |
| `merch_apparel` | Sports Merch & Apparel | ★ | Wins drive impulse buys → "commemorate the moment" drops |
| `beverages` | Beverages | ★ | Core watch-along consumption → region+emotion-targeted ads |
| `streaming_ott` | Streaming / OTT | ★ | Tune-in and sign-up windows → pre-match pushes by segment |
| `content_creator` | Content Creators | ★ | Attention monetisation → real-time content-idea recommendations (§7.3) |
| `sportswear_fashion` | Sportswear & Fashion | | Peak brand attention → segment+moment brand campaigns |
| `betting_igaming` | Betting / iGaming | | Major sports-ad category → **`compliance_flag: true`, region-gated**; the flag must surface on every card |
| `gaming_esports` | Gaming & Esports | | Hype → install/engagement campaigns |
| `retail_ecommerce` | Retail & E-commerce | | Big-moment flash-sale culture → emotion-triggered promos |
| `telecom` | Telecom & Mobile | | Event sponsors, data upsell → audience-targeted offers |
| `consumer_electronics` | Consumer Electronics | | Big matches drive TV upgrades → pre-tournament campaigns |
| `fintech` | Financial / Fintech | | Sponsor category → segment-targeted acquisition |
| `travel_hospitality` | Travel & Hospitality | | Traveling fans → `fan_trip_promo` to traveling_ultras |
| `pubs_venues` | Bars, Pubs & Venues | | Screening promos → geo+fixture-timed `watch_it_here` (advertising only — no venue ops) |
| `automotive` | Automotive | | Long-standing partner category → brand campaigns to high-value segments |

---

## 9. System-wide invariants (every agent enforces these)

1. **Glass-box:** every `CampaignCard`, `ContentIdeaCard`, `ROIResult`, `AudienceForecast`, and `NextBestAction` carries a populated evidence/rationale field tracing to measured data, a citation, or a model artifact. An output without evidence is a contract violation.
2. **No invented numbers:** every numeric output derives from the funnel math, a cited benchmark, a trained model artifact, or a measured live signal — through the documented formulas. `random()` appears nowhere outside seeded synthetic-data generation.
3. **LLM boundary:** Gemini writes copy/ideas only. It never selects segments, channels, windows, or numbers, and its outputs are schema-validated before use.
4. **Enum discipline:** all sentiments, emotions, sources, channels, segments, industries, archetypes, event tags come from `contracts/enums.py`. Out-of-enum values fail loudly.
5. **Determinism:** `RANDOM_SEED = 42` for all stochastic steps; model artifacts and datasets are committed; any agent can reproduce any other's outputs.
6. **Graceful degradation, never fabrication:** dead connector → log and continue; missing momentum → baseline mode; Gemini down → template fallback flagged `llm_fallback: true`; missing benchmark → explicit error. The system degrades honestly; it never fills gaps with made-up data.
7. **Scope:** no logistics/ops features, no channel integrations, no extra external APIs, no frontend this phase (§1.2).

---

## 10. Build priorities (what matters most when trading off)

Tier order from Work Distribution §6 applies; within it, protect value in this order:

1. **The demo spine:** replay → NLP → aggregates → moment fires → auto campaign card with evidence + real Gemini copy. If this chain works end-to-end, the product exists.
2. **The differentiators (§5):** live re-forecast loop, grounded ROI with baseline contrast, deterministic strategy layer, evidence trails.
3. **Coverage:** all endpoints contract-valid, all 15 industries minimally covered, content-creator flavour.
4. **Polish:** vector-RAG upgrade, extra connectors, richer KB.

Simplicity rules under pressure: KMeans over anything fancier; XGBoost/GBR over deep models; keyed retrieval before vectors; pre-trained NLP only (zero training). The impressive complexity here is *orchestration* — the loop, the evidence, the moment automation — not model sophistication.
