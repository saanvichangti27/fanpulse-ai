# FanPulse AI — API & Integration Contract
### Version 3.0.0 — FROZEN
*(3.0.0: hackathon-minimal architecture. One FastAPI process + one SQLite file. No WebSocket (clients poll REST), no LiveStore, no aggregator tick — analytics are computed by SQL at request time. Moment detection is one 10s background loop. Features unchanged.)*

*The single source of truth for every seam between the three workstreams. Code conforms to this document, never the other way around. Changes require human approval + a version bump.*

**Contract surfaces:** §B REST (backend ⇄ future frontend/smoke test) · §D SQLite schema + §E in-process interfaces (W1 ⇄ W2) · §F intelligence functions (W3 ⇄ W2) · §A shared definitions · §G W2-internal shapes · §H verification.

**Global conventions**
- Timestamps ISO-8601 UTC (`Z`). IDs are strings (`m_001`, `c_0001`, `mo_0001`, `ci_0001`); segments are slugs (§A).
- `*_pct` = 0–100 floats · `ctr`/`cvr`/`fit`/`confidence`/`*_prob` = 0–1 floats · money = `*_usd` floats. Never mix.
- `snake_case` JSON. Base path `/api/v1`.
- Errors (non-2xx): `{ "error": { "code": "NOT_FOUND|VALIDATION_ERROR|LLM_UNAVAILABLE|INSUFFICIENT_DATA|INTERNAL", "message": "..." } }`.
- All enums live in the single file `backend/contracts.py`; out-of-enum values fail pydantic validation loudly.

---

## §A — Shared enums, models & constants
*W2 transcribes this section verbatim into `backend/contracts.py` in Phase 0, then it is frozen. Everyone imports from it; nothing is redefined locally.*

### A.1 Enums

- **Sentiment:** `positive | negative | neutral`
- **Emotion** (the j-hartmann model's 7 outputs): `joy | anger | surprise | fear | disgust | sadness | neutral`
- **Source:** `reddit | youtube | news | replay`
- **Channel:** `push | instagram | youtube | email`
  > **Channel ≠ Source.** A *Source* is where fan messages are ingested FROM (real APIs). A *Channel* is where a recommended campaign WOULD be delivered BY the brand — purely a **label** on cards and a key in `benchmarks.csv`. FanPulse never posts or sends anything anywhere.
- **Segments:** `superfans | traveling_ultras | casual_streamers | deal_seekers | lapsed_fans`
- **Event tags:** `goal | red_card | var_controversy | full_time | kickoff | surge_other`
- **Archetypes:** `celebration_flash_offer | consolation_offer | commemorative_drop | tune_in_push | fan_trip_promo | watch_it_here | install_play | flash_sale | brand_awareness | content_idea`

### A.2 Industries (15 slugs; ★ = demo focus, full playbook + cited benchmark rows required; unstarred need one interpolated benchmark row + the `brand_awareness` playbook fallback)

★ `food_delivery` · ★ `merch_apparel` · ★ `beverages` · ★ `streaming_ott` · ★ `content_creator` ·
`sportswear_fashion` · `betting_igaming` (`compliance_flag: true`) · `gaming_esports` · `retail_ecommerce` · `telecom` · `consumer_electronics` · `fintech` · `travel_hospitality` · `pubs_venues` · `automotive`

### A.3 Constants

```python
RANDOM_SEED = 42

# Arousal per emotion — used identically by W1 (excitement score) and W3 (multiplier M).
AROUSAL = { "joy": 0.90, "surprise": 0.85, "anger": 0.80, "fear": 0.60,
            "disgust": 0.50, "sadness": 0.30, "neutral": 0.10 }

# Excitement score (0–100), computed inside get_kpis():
# excitement = 100 * (0.6 * volume_weighted_mean_arousal + 0.4 * clip(volume_ratio / 3, 0, 1))

# Multiplier M (W3): M = clamp(1 + K * arousal * fit * moment_strength * segment_match, 0.7, 2.5)
MULTIPLIER_K = 2.0
MULTIPLIER_MIN, MULTIPLIER_MAX = 0.7, 2.5
CVR_LIFT_DAMPING = 0.5           # CVR_eff = CVR * (1 + (M - 1) * 0.5)

# Moment rule (checked by the 10 s background loop):
# volume_1m >= 3 * trailing 5-min per-minute average  AND  abs(sentiment_delta_pp) >= 10
MOMENT_VOLUME_RATIO = 3.0
MOMENT_SENTIMENT_DELTA_PP = 10.0
MOMENT_COOLDOWN_SECONDS = 120

MOMENTUM_MIN_MESSAGES_5M = 10    # fewer ⇒ get_momentum() returns None ⇒ baseline mode
GEMINI_DEBOUNCE_SECONDS = 12
```

### A.4 Core pydantic models

```python
class RawMessageIn(BaseModel):            # connector/replay output → NLP input
    external_id: str; match_id: str; source: Source
    author: str | None; text: str
    country: str | None                   # ISO-2 if known upstream (replay), else None
    created_at: datetime

class ClassifiedMessage(BaseModel):       # one messages row; feed items
    message_id: int; match_id: str; source: Source
    text: str; author: str | None; country: str | None
    sentiment: Sentiment; sentiment_score: float
    emotion: Emotion; emotion_score: float
    topics: list[str]                     # ≤ 5, lowercase
    created_at: datetime

class MomentumSnapshot(BaseModel):        # computed on demand; input to reforecast & multiplier
    match_id: str
    volume_1m: int; volume_5m: int
    volume_ratio: float                   # volume_1m / max(trailing 5-min per-minute avg, 1)
    dominant_emotion: Emotion
    arousal: float                        # volume-weighted mean via AROUSAL
    positive_pct: float
    sentiment_delta_pp: float             # positive_pct now vs 2 min ago
    top_topics: list[str]                 # ≤ 5
    top_countries: list[str]              # ≤ 5, ISO-2, by volume
    computed_at: datetime

class MomentEvent(BaseModel):             # moments row; on_moment callback payload
    moment_id: str; match_id: str; event_tag: EventTag
    detected_at: datetime
    momentum: MomentumSnapshot            # snapshot AT detection time
    description: str                      # e.g. "Volume spike 4.1x with joy surge (+26pp)"

class MatchFeatures(BaseModel):           # forecast input (§F.1)
    match_id: str; stage: int             # 0 group … 5 final
    home_team: str; away_team: str
    home_rank: int; away_rank: int; rank_gap: int
    rivalry_flag: bool; host_involved: bool
    city_population_m: float; venue_capacity: int
    day_of_week: int; kickoff_hour_local: int
    buzz_index: float                     # 0–1; synthetic@train, live-computed@inference
```

Response models for every §B endpoint also live in `contracts.py`, mirroring the JSON below exactly.

---

## §B — REST endpoints
*All endpoints W2. There is **no WebSocket**: anything "live" is obtained by polling these endpoints every 2–3 s (`/kpis`, `/feed`, `/campaigns`, `/moments`). Hot values are computed at request time by W1's analytics functions (§E.1).*

### B.0 Health & reference
- `GET /api/v1/health` → `{ "status": "ok", "db": true, "ingestion_alive": true, "version": "3.0.0" }` (`ingestion_alive` = any message inserted < 60 s ago)
- `GET /api/v1/industries` → `{ "industries": [ { "slug", "display_name", "starred", "compliance_flag" } ] }`

### B.1 Matches
- `GET /api/v1/matches` → `{ "matches": [Match] }` · `GET /api/v1/matches/{match_id}` → `Match`
```json
Match = { "match_id": "m_001", "home_team": "Brazil", "away_team": "Argentina",
  "kickoff_time": "2026-07-04T18:00:00Z", "stage": 4, "venue_capacity": 88000,
  "city": "Dallas", "status": "live",
  "demand_index": 87.4, "sellout_probability": 0.91 }      // null until forecast exists
```

### B.2 Live KPIs — `GET /api/v1/matches/{match_id}/kpis`
```json
{ "match_id": "m_001", "total_mentions": 48213,
  "positive_pct": 71.4, "negative_pct": 9.8, "neutral_pct": 18.8,
  "top_emotion": "joy", "excitement_score": 92.0,
  "most_active_region": "BR", "mentions_per_min": 1240, "computed_at": "..." }
```

### B.3 Timeline — `GET /api/v1/matches/{match_id}/sentiment-timeline`
30-second buckets computed by SQL over `messages`; a bucket containing a moment carries its tag.
```json
{ "match_id": "m_001", "points": [
  { "ts": "...", "positive_pct": 65.0, "negative_pct": 12.0, "neutral_pct": 23.0,
    "mentions": 1200, "top_emotion": "joy", "event_tag": null },
  { "ts": "...", "positive_pct": 96.2, "negative_pct": 2.1, "neutral_pct": 1.7,
    "mentions": 3400, "top_emotion": "joy", "event_tag": "goal" } ] }
```

### B.4 Heatmap — `GET /api/v1/matches/{match_id}/heatmap`
```json
{ "match_id": "m_001", "computed_at": "...", "countries": [
  { "country_code": "BR", "avg_sentiment": 0.94, "dominant_emotion": "joy", "mentions": 12000 } ] }
```
`avg_sentiment` ∈ [−1, 1]: mean of (+score positive, −score negative, 0 neutral).

### B.5 Topics, feed, moments
- `GET .../topics` → `{ "topics": [ { "label": "messi", "mentions": 8210, "trend": "up|down|flat" } ] }` (vs 5 min ago; ≤ 10)
- `GET .../feed?limit=50` → `{ "messages": [ClassifiedMessage] }` (newest first, ≤ 200)
- `GET .../moments` → `{ "moments": [MomentEvent] }` (newest first)

### B.6 Forecast (Feature 3)
- `GET /api/v1/matches/{match_id}/forecast` → latest `AudienceForecast`:
```json
{ "match_id": "m_001", "demand_index": 87.4, "predicted_attendance_pct": 97.2,
  "sellout_probability": 0.91,
  "feature_importance": [ { "feature": "stage", "importance": 0.34 } ],
  "is_reforecast": true, "baseline_demand_index": 74.1, "delta_vs_baseline_pct": 17.9,
  "trigger_description": "Live buzz 0.93 after goal moment mo_0007",
  "model_mae": 0.041, "computed_at": "..." }
```
- `POST /api/v1/forecast/reforecast` `{ "match_id" }` → recompute with live momentum, persist, return. `409 INSUFFICIENT_DATA` if momentum is None.

### B.7 Campaigns (Feature 5)
- `POST /api/v1/campaigns/generate` — request (segment/channel optional ⇒ strategy engine chooses):
```json
{ "match_id": "m_001", "industry": "food_delivery", "target_segment": null,
  "channel": null, "trigger": "manual", "moment_id": "mo_0007", "budget_usd": 100000 }
```
Response = `CampaignCard` (also the GET list item):
```json
{ "campaign_id": "c_0047", "match_id": "m_001", "industry": "food_delivery",
  "archetype": "celebration_flash_offer", "target_segment": "deal_seekers",
  "channel": "push", "window_minutes": 15, "window_ends_at": "...",
  "trigger": "auto", "moment_id": "mo_0007",
  "copy": { "headline": "GOOOL means GO TIME 🍕",
            "body": "Brazil just scored — 25% off your order for the next 15 minutes.",
            "cta": "Order now", "hashtags": ["#BRAvsARG"],
            "variant_b": { "headline": "...", "body": "...", "cta": "..." } },
  "roi": { /* ROIResult, §B.8 */ },
  "evidence": {
    "moment": "joy surge +26pp, volume 4.1x baseline (mo_0007, goal)",
    "segment": "deal_seekers: 1,480 fans in sample (29.6%), avg engagement 71, prefers push",
    "regional": "top regions BR (12,000 mentions), AR (8,400)",
    "multiplier": { "M": 1.86, "arousal": 0.90, "emotion_brand_fit": 0.85,
                    "moment_strength": 0.80, "segment_match": 0.70, "k": 2.0 },
    "benchmark_source": "WordStream Google Ads benchmarks 2025 — food_delivery/push" },
  "confidence": 0.88, "llm_fallback": false, "created_at": "..." }
```
- `GET /api/v1/matches/{match_id}/campaigns` → `{ "campaigns": [CampaignCard] }` (newest first — the demo polls this to catch auto-fired cards)
- `POST /api/v1/content/generate` `{ "match_id", "platform": "instagram"|"youtube", "creator_niche" }` → `ContentIdeaCard`:
```json
{ "content_id": "ci_0012", "match_id": "m_001", "platform": "instagram",
  "archetype": "content_idea",
  "idea": { "format": "15s vertical reel", "hook": "React in the first 2 seconds to Messi's goal",
            "concept": "...", "hashtags": ["..."], "post_within_minutes": 20 },
  "evidence": { "trending": "'messi' 8,210 mentions rising; dominant emotion joy (0.9 arousal)",
                "regional": "peak audiences BR, AR", "timing": "windows decay ~20 min post-moment" },
  "confidence": 0.84, "llm_fallback": false, "created_at": "..." }
```

### B.8 ROI (Feature 6)
- `POST /api/v1/roi/simulate` — `{ "match_id", "industry", "channel", "budget_usd", "timing": "now"|"baseline" }` → `ROIResult`:
```json
{ "industry": "food_delivery", "channel": "push", "budget_usd": 100000,
  "multiplier": { "M": 1.86, "arousal": 0.90, "emotion_brand_fit": 0.85,
                  "moment_strength": 0.80, "segment_match": 0.70, "k": 2.0 },
  "funnel": { "cpm_usd": 6.0, "frequency": 2.5, "impressions": 16666667, "reach": 6666667,
              "ctr_baseline": 0.009, "ctr_effective": 0.0173, "clicks": 288000,
              "cvr_baseline": 0.03, "cvr_effective": 0.0438, "conversions": 12614,
              "aov_usd": 30.0, "revenue_usd": 378420 },
  "roas": 3.78, "roi_pct": 278.4,
  "baseline_comparison": { "roas": 1.35, "roi_pct": 35.0, "revenue_usd": 135000 },
  "benchmark_source": "WordStream Google Ads benchmarks 2025 — food_delivery/push",
  "confidence": 0.88, "computed_at": "..." }
```
- `POST /api/v1/roi/media-plan` — `{ "budget_usd", "industry", "match_ids": [...] }` →
```json
{ "total_budget_usd": 500000, "industry": "beverages",
  "allocations": [ { "match_id": "m_001", "budget_usd": 300000, "share_pct": 60.0,
                     "demand_index": 87.4, "expected_roas": 2.9, "expected_revenue_usd": 870000,
                     "rationale": "Highest demand index (87), rivalry fixture; capped at 60%." } ],
  "expected_total_roas": 2.4 }
```

### B.9 Fans (Feature 4)
- `GET /api/v1/fans/segments?match_id=m_001` — with `match_id`, each segment carries the live-activity overlay:
```json
{ "segments": [ { "segment_id": "deal_seekers", "display_name": "Deal-Seekers",
    "size": 1480, "share_pct": 29.6, "avg_engagement_score": 71.2, "avg_annual_value_usd": 84.0,
    "top_countries": ["BR","MX","IN"], "preferred_channel": "push", "churn_risk_pct": 12.4,
    "defining_traits": ["push opt-in 91%", "high app sessions", "offer-responsive"],
    "activity_share_pct": 41.0 } ],
  "silhouette_score": 0.41, "n_fans": 5000 }
```
- `GET /api/v1/fans/next-best-actions?industry=food_delivery` → `{ "actions": [ { "segment_id", "industry", "channel", "archetype", "timing_rule", "expected_ctr", "rationale" } ] }` (`industry` omitted ⇒ all starred)

### B.10 Replay control — `POST /api/v1/replay/control`
`{ "action": "start"|"stop", "match_id": "m_001", "file": "replay_match_01.json", "speed": 4.0 }` → `{ "accepted": true }`. Plain in-process call into the `ReplayController` (§E.2).

---

## §C — Realtime strategy: polling, not WebSocket
There is deliberately **no WebSocket, no SSE, no pub/sub**. The future frontend (and `dev poll loop` scripts) poll `/kpis`, `/feed`, `/moments`, `/campaigns` every 2–3 seconds — at demo scale this is visually indistinguishable from push and removes an entire class of integration bugs. Do not add a push channel.

---

## §D — SQLite schema (frozen)
*Single file `backend/fanpulse.db`. SQLAlchemy models in `app/models_db.py` (W2 owns), `Base.metadata.create_all()` at startup — no migrations, no Alembic. W1 writes `messages` and `moments`; W2 writes the rest. Six tables total.*

```sql
CREATE TABLE matches (
    id TEXT PRIMARY KEY,
    home_team TEXT NOT NULL, away_team TEXT NOT NULL,
    kickoff_time TEXT NOT NULL,                      -- ISO-8601 UTC
    stage INTEGER NOT NULL DEFAULT 0,                -- 0 group … 5 final
    venue_capacity INTEGER NOT NULL DEFAULT 60000,
    city TEXT, city_population_m REAL,
    home_rank INTEGER, away_rank INTEGER,
    rivalry_flag INTEGER DEFAULT 0, host_involved INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'upcoming'          -- upcoming | live | finished
);

-- One row per fan message: raw + classification merged. THE core table;
-- kpis/timeline/heatmap/topics/momentum are all SQL over this at read time.
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL,
    match_id TEXT REFERENCES matches(id),
    source TEXT NOT NULL, author TEXT, text TEXT NOT NULL,
    country TEXT,                                     -- ISO-2, nullable
    sentiment TEXT NOT NULL, sentiment_score REAL NOT NULL,
    emotion TEXT NOT NULL, emotion_score REAL NOT NULL,
    topics_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    UNIQUE (source, external_id)
);
CREATE INDEX idx_messages_match_created ON messages (match_id, created_at);

CREATE TABLE moments (
    id TEXT PRIMARY KEY,
    match_id TEXT REFERENCES matches(id),
    event_tag TEXT NOT NULL, detected_at TEXT NOT NULL,
    momentum_json TEXT NOT NULL, description TEXT
);

CREATE TABLE campaigns (
    id TEXT PRIMARY KEY,
    match_id TEXT REFERENCES matches(id),
    industry TEXT NOT NULL, archetype TEXT NOT NULL,
    target_segment TEXT NOT NULL, channel TEXT NOT NULL,
    trigger TEXT NOT NULL, moment_id TEXT REFERENCES moments(id),
    window_minutes INTEGER,
    copy_json TEXT NOT NULL, roi_json TEXT NOT NULL, evidence_json TEXT NOT NULL,
    confidence REAL, llm_fallback INTEGER DEFAULT 0, created_at TEXT NOT NULL
);

CREATE TABLE content_ideas (
    id TEXT PRIMARY KEY,
    match_id TEXT REFERENCES matches(id),
    platform TEXT NOT NULL,
    idea_json TEXT NOT NULL, evidence_json TEXT NOT NULL,
    confidence REAL, llm_fallback INTEGER DEFAULT 0, created_at TEXT NOT NULL
);

CREATE TABLE forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id TEXT REFERENCES matches(id),
    is_reforecast INTEGER NOT NULL DEFAULT 0,
    forecast_json TEXT NOT NULL, created_at TEXT NOT NULL
);
```

---

## §E — In-process interfaces (W1 → W2)

### E.1 Analytics functions — `ingestion/analytics.py` (W1 implements; W2's endpoints call them)
All are plain synchronous functions running SQL over `messages`/`moments` via a passed session. Return `None`/`[]` when there is no data — never raise for emptiness.

```python
def get_kpis(session, match_id: str) -> KpiSnapshot | None          # §B.2 shape
def get_timeline(session, match_id: str, bucket_s: int = 30) -> list[TimelinePoint]   # §B.3
def get_heatmap(session, match_id: str) -> HeatmapPayload | None    # §B.4
def get_topics(session, match_id: str) -> list[TopicItem]           # §B.5
def get_momentum(session, match_id: str) -> MomentumSnapshot | None
    # None when volume_5m < MOMENTUM_MIN_MESSAGES_5M ⇒ W2 uses baseline mode
    # (M = 1.0, forecast without live buzz, 409 on reforecast). Never crash, never invent.
def get_country_volumes(session, match_id: str) -> dict[str, int]   # for the segment overlay
```

### E.2 Ingestion service — `ingestion/service.py` (W1 implements; W2 starts at app startup)

```python
async def run_ingestion(session_factory, sources: list[str],
                        on_moment: Callable[[MomentEvent], Awaitable[None]]) -> None
    """One asyncio task: poll sources → classify locally → INSERT messages rows.
    Every 10 s: get_momentum() → moment rule (§A.3) → INSERT moments row →
    await on_moment(event) (errors in the callback are caught and logged — a failing
    callback must never stop ingestion). All connector/API errors: log and continue."""

class ReplayController:
    def start(self, match_id: str, file: str, speed: float = 1.0) -> None
    def stop(self, match_id: str) -> None
```

Moment tag heuristics: dominant `joy` + positive delta → `goal`; dominant `anger`/`disgust` + topics ∩ {var, referee, penalty, red card} → `var_controversy`/`red_card`; replay marker items force their tag; else `surge_other`. Cooldown 120 s.

### E.3 Replay file schema (`data/replay/*.json`)

```json
{ "meta": { "match_id": "m_001", "captured_at": "...", "description": "..." },
  "items": [
    { "t_offset": 0,    "external_id": "rd_abc1", "source": "reddit", "author": "u/fan1",
      "text": "Kickoff! Vamos!!", "country": "BR" },
    { "t_offset": 1380, "marker": "goal" },
    { "t_offset": 1381, "external_id": "yt_x9", "source": "youtube", "author": "carlos",
      "text": "GOOOOOL!!! 🔥🔥", "country": "AR" } ] }
```
Message items keep their true source; the `replay` source value is reserved for the hand-written dev fixture. Marker items only steer the moment tag.

---

## §F — Intelligence package interface (W3 → W2)
*Pure functions + committed artifacts. Inputs/outputs are `contracts.py` models. No FastAPI, no DB, no async; only reads `data/` and `artifacts/` at module load. sklearn only (no xgboost). All randomness seeded with `RANDOM_SEED`.*

### F.1 Forecast — `intelligence.forecast`
```python
def predict_audience(features: MatchFeatures) -> AudienceForecast          # §B.6 shape
def reforecast(features: MatchFeatures, momentum: MomentumSnapshot) -> AudienceForecast
def compute_live_buzz(momentum: MomentumSnapshot) -> float
    # clip(0.6 * volume_percentile + 0.4 * clip(volume_ratio / 3, 0, 1), 0, 1)
```
`reforecast` populates `is_reforecast=True`, `baseline_demand_index`, `delta_vs_baseline_pct`, `trigger_description`. Sanity: goal-level momentum moves the forecast **+5..+20 demand points**.

### F.2 Segments — `intelligence.segments`
```python
def get_segments() -> SegmentReport            # {"segments":[Segment], "silhouette_score", "n_fans"}
def get_active_overlay(country_volumes: dict[str, int]) -> dict[str, float]   # segment_id → activity_share_pct
def get_next_best_actions(industry: str | None = None) -> list[NextBestAction]
```
KMeans k=5 on the 5,000-row synthetic CRM; clusters mapped to the §A segment slugs by centroid rules. Engagement score: RFM-D, four 0–100 percentile subscores (Recency, Frequency, Monetary, Digital), weights 0.25 each.

### F.3 ROI — `intelligence.roi`
```python
def simulate_roi(request: ROIRequest, momentum: MomentumSnapshot | None,   # None ⇒ M = 1.0
                 target_segment: str | None = None) -> ROIResult
def compute_multiplier(momentum: MomentumSnapshot, industry: str,
                       target_segment: str | None) -> MultiplierBreakdown
def best_channel(industry: str, segment_id: str) -> Channel
def plan_media(budget_usd: float, industry: str, forecasts: list[AudienceForecast],
               momenta: dict[str, MomentumSnapshot | None]) -> MediaPlan
```
Math per spec §6 with §A.3 constants; `MomentStrength = clip(volume_ratio / 3, 0, 1)`; `baseline_comparison` always populated. Unknown (industry, channel) benchmark pair ⇒ raise `BenchmarkNotFound` (in `contracts.py`; W2 maps to `VALIDATION_ERROR`).

**Confidence:** `clip(0.4*volume_support + 0.3*moment_recency + 0.3*segment_support, 0, 1)`; `volume_support = clip(volume_5m/500, 0, 1)`, `moment_recency = clip(1 − age_min/30, 0, 1)` (1.0 when no moment involved), `segment_support = clip(segment_size/500, 0, 1)`. Baseline mode: fixed 0.75.

**Acceptance case (must reproduce within rounding):** food_delivery/push, $100k, benchmark row `CPM=6, freq=2.5, CTR=0.009, CVR=0.03, AOV=30` → baseline ROAS **1.35**; `M≈1.86` (arousal .90, fit .85, strength .80, match .70) → ROAS **≈ 3.6**.

---

## §G — W2-internal shapes (documented for review; only W2 touches them)

### G.1 Playbook (replaces the old knowledge-base directory)
One python dict in `app/strategy/playbook.py`:
```python
PLAYBOOK[(emotion, industry)] = {
    "archetype": Archetype, "window_minutes": int, "channel_default": Channel,
    "tone_notes": str,                 # 1–2 sentences of copywriting guidance
    "template": str,                   # example copy with {slots} — ALSO the llm_fallback
}
# Full rows for the 5 starred industries × 7 emotions; every other industry:
# one ("*", industry) → brand_awareness fallback row.
```

### G.2 CampaignBrief (strategy engine → Gemini step)
```python
class CampaignBrief(BaseModel):
    match_id: str; industry: Industry; archetype: Archetype
    target_segment: SegmentId; channel: Channel; window_minutes: int
    moment: MomentEvent | None; emotion: Emotion
    top_topics: list[str]; top_countries: list[str]
    roi: ROIResult; segment: Segment; tone_notes: str
```

### G.3 Gemini call
Strict JSON output `{ "headline" ≤60, "body" ≤140, "cta" ≤25, "hashtags" ≤4, "variant_b": {headline, body, cta} }` (content flavour: `{format, hook, concept ≤280, hashtags, post_within_minutes}`). Prompt = system line ("senior performance-marketing copywriter; copy ONLY; never invent statistics; use only the numbers given; output strict JSON") + measured context (moment description, segment stats, emotion, trending topics, window, channel, industry) + the playbook row's `tone_notes` and `template` as guidance. Debounce ≥ 12 s; cache by `(match, archetype, industry, segment)`; **any failure → fill the playbook `template`'s slots and return it with `llm_fallback: true`.** The recommendation path never surfaces an unresolved error.

---

## §H — Verification
One integration gate: **`scripts/smoke_test.py`** — from a cold start (delete `fanpulse.db`): boot app → seed → `POST /replay/control start` (dev fixture, high speed) → within 90 s assert: every §B endpoint returns 200 with response-model-valid JSON; ≥ 1 moment with `event_tag="goal"`; ≥ 1 campaign with non-empty `evidence` and `roi.baseline_comparison`; the §F.3 acceptance case reproduces. Green smoke test on `main` = integrated.

*End of contract v3.0.0.*
