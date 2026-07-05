# FanPulse AI — API & Integration Contract
### Version 1.0.1 — FROZEN
*(1.0.1: Channel enum trimmed to `push | instagram | youtube | email`; `tiktok`/`display` removed; Channel-vs-Source note added.)*
*The single source of truth for every seam between the three workstreams. Code conforms to this document, never the other way around. Changes require human approval + a version bump + a simultaneous update of `backend/contracts/`.*

**The three contract surfaces:**
- **§B REST + §C WebSocket** — backend ⇄ (future frontend, smoke tests, Swagger)
- **§D Postgres + §E Redis** — W1 ingestion ⇄ W2 backend
- **§F Python interfaces** — W3 intelligence package ⇄ W2 backend
- **§A** shared enums/models/constants used by all of the above; **§G** W2-internal shapes documented for review

**Global conventions**
- All timestamps: ISO-8601 UTC with `Z` suffix (`2026-07-04T18:32:10Z`).
- All IDs: strings. Matches `m_001`, campaigns `c_0001`, fans `f_000001`, moments `mo_0001`, segments are slugs (§A.5).
- All percentages named `*_pct` are 0–100 floats; all rates/probabilities/scores named `ctr`, `cvr`, `fit`, `confidence`, `*_prob` are 0–1 floats. Money is `*_usd` floats. Never mix these up.
- JSON field names: `snake_case` everywhere.
- REST base path: `/api/v1`. Content type `application/json`.
- Errors (all non-2xx): `{ "error": { "code": "<UPPER_SNAKE>", "message": "<human readable>" } }`. Codes: `NOT_FOUND`, `VALIDATION_ERROR`, `LLM_UNAVAILABLE`, `INSUFFICIENT_DATA`, `RATE_LIMITED`, `INTERNAL`.
- Enum violations are integration bugs: any value outside §A enums must fail loudly (pydantic validation), never pass silently.

---

## §A — Shared enums, models & constants
*Transcribed verbatim into `backend/contracts/enums.py`, `models.py`, `constants.py` by W2 in Phase 0. All packages import from there — never redefine locally.*

### A.1 Sentiment
`positive | negative | neutral`

### A.2 Emotion (locked to the j-hartmann model's 7 outputs)
`joy | anger | surprise | fear | disgust | sadness | neutral`

### A.3 Source
`reddit | youtube | news | replay`

### A.4 Channel
`push | instagram | youtube | email`

> **Channel ≠ Source.** A *Source* (§A.3) is where we ingest fan messages FROM (real API integrations, W1's job). A *Channel* is where a recommended campaign WOULD be delivered BY the brand — it is purely a **label on recommendation cards** and a key in `benchmarks.csv`. FanPulse never integrates with, posts to, or sends anything on any channel. No channel APIs exist anywhere in this system.

### A.5 Segment slugs (fixed persona names — KMeans clusters are mapped onto these)
`superfans | traveling_ultras | casual_streamers | deal_seekers | lapsed_fans`

### A.6 Constants (`contracts/constants.py`)
```python
RANDOM_SEED = 42

# Arousal per emotion — used identically by W1 (excitement score) and W3 (multiplier M).
AROUSAL: dict[str, float] = {
    "joy": 0.90, "surprise": 0.85, "anger": 0.80, "fear": 0.60,
    "disgust": 0.50, "sadness": 0.30, "neutral": 0.10,
}

# Excitement score (0–100), computed by W1 for the KPI hash:
# excitement = 100 * (0.6 * volume_weighted_mean_arousal + 0.4 * clip(velocity_zscore / 4, 0, 1))

# Multiplier M (W3): M = clamp(1 + K * arousal * fit * moment_strength * segment_match, 0.7, 2.5)
MULTIPLIER_K = 2.0
MULTIPLIER_MIN, MULTIPLIER_MAX = 0.7, 2.5
CVR_LIFT_DAMPING = 0.5          # CVR_eff = CVR * (1 + (M - 1) * 0.5)

MOMENT_ZSCORE_THRESHOLD = 2.5   # §E.4
MOMENT_SENTIMENT_DELTA_PP = 10.0
MOMENT_COOLDOWN_SECONDS = 120
GEMINI_DEBOUNCE_SECONDS = 12
```

### A.7 Industry slugs (the final 15) & archetypes

| slug | display name | starred (demo focus) |
|---|---|---|
| `food_delivery` | Food Delivery & QSR | ★ |
| `merch_apparel` | Sports Merch & Licensed Apparel | ★ |
| `beverages` | Beverages | ★ |
| `streaming_ott` | Streaming / OTT / Broadcast | ★ |
| `content_creator` | Content Creators & Influencers | ★ |
| `sportswear_fashion` | Sportswear & Fashion | |
| `betting_igaming` | Betting / Fantasy / iGaming (`compliance_flag: true`, region-gated) | |
| `gaming_esports` | Gaming & Esports | |
| `retail_ecommerce` | Retail & E-commerce | |
| `telecom` | Telecom & Mobile | |
| `consumer_electronics` | Consumer Electronics | |
| `fintech` | Financial Services / Fintech | |
| `travel_hospitality` | Travel & Hospitality | |
| `pubs_venues` | Bars, Pubs & Viewing Venues | |
| `automotive` | Automotive | |

**Archetype enum:** `celebration_flash_offer | consolation_offer | commemorative_drop | tune_in_push | fan_trip_promo | watch_it_here | install_play | flash_sale | brand_awareness | content_idea`

**Event-tag enum (moments):** `goal | red_card | var_controversy | full_time | kickoff | surge_other`

### A.8 Core pydantic models (exact field names & types)

```python
class RawMessageIn(BaseModel):              # connector/replay output → NLP input
    external_id: str                        # source-native ID for dedupe
    match_id: str
    source: Source
    author: str | None
    text: str
    country: str | None                     # ISO-2 if known upstream (replay), else None
    created_at: datetime

class ClassifiedMessage(BaseModel):         # NLP output; feed items; WS new_message payload
    message_id: int
    match_id: str
    source: Source
    text: str
    author: str | None
    country: str | None
    sentiment: Sentiment
    sentiment_score: float                  # 0–1 model confidence
    emotion: Emotion
    emotion_score: float                    # 0–1
    topics: list[str]                       # ≤ 5, lowercase
    created_at: datetime

class MomentumSnapshot(BaseModel):          # Redis §E.3; input to reforecast & multiplier
    match_id: str
    volume_1m: int
    volume_5m: int
    velocity_zscore: float                  # vs trailing 10-min per-minute baseline
    dominant_emotion: Emotion
    arousal: float                          # 0–1, volume-weighted mean via AROUSAL map
    positive_pct: float
    sentiment_delta_pp: float               # positive_pct now vs 2 min ago
    top_topics: list[str]                   # ≤ 5
    top_countries: list[str]                # ≤ 5, ISO-2, by volume
    updated_at: datetime

class MomentEvent(BaseModel):               # §E.4 pub/sub payload; strategy-engine trigger
    moment_id: str
    match_id: str
    event_tag: EventTag
    detected_at: datetime
    momentum: MomentumSnapshot              # snapshot AT detection time
    description: str                        # e.g. "Volume spike 4.1σ with joy surge (+26pp)"

class MatchFeatures(BaseModel):             # forecast input (§F.1)
    match_id: str
    stage: int                              # 0 group … 5 final
    home_team: str
    away_team: str
    home_rank: int
    away_rank: int
    rank_gap: int
    rivalry_flag: bool
    host_involved: bool
    city_population_m: float
    venue_capacity: int
    day_of_week: int                        # 0 = Monday
    kickoff_hour_local: int
    buzz_index: float                       # 0–1; synthetic@train, live-computed@inference
```

---

## §B — REST endpoints
*Every endpoint below must exist, with response shapes exactly as shown. W2 implements; pydantic response models in `contracts/models.py` enforce shapes.*

### B.0 Health & reference
- `GET /api/v1/health` → `{ "status": "ok", "db": true, "redis": true, "ingestion_alive": true, "version": "1.0.0" }` (`ingestion_alive` = momentum key updated < 60s ago for any live match)
- `GET /api/v1/industries` → `{ "industries": [ { "slug": "food_delivery", "display_name": "Food Delivery & QSR", "starred": true, "compliance_flag": false }, ... ] }`

### B.1 Matches
- `GET /api/v1/matches` → `{ "matches": [Match, ...] }`
- `GET /api/v1/matches/{match_id}` → `Match`

```json
Match = {
  "match_id": "m_001", "home_team": "Brazil", "away_team": "Argentina",
  "kickoff_time": "2026-07-04T18:00:00Z", "stage": 4, "venue_capacity": 88000,
  "city": "Dallas", "status": "live",                    // upcoming | live | finished
  "demand_index": 87.4, "sellout_probability": 0.91      // null until forecast exists
}
```

### B.2 Live KPIs — `GET /api/v1/matches/{match_id}/kpis`
```json
{
  "match_id": "m_001", "total_mentions": 48213,
  "positive_pct": 71.4, "negative_pct": 9.8, "neutral_pct": 18.8,
  "top_emotion": "joy", "excitement_score": 92.0,
  "most_active_region": "BR", "mentions_per_min": 1240, "updated_at": "2026-07-04T18:32:10Z"
}
```

### B.3 Sentiment timeline — `GET /api/v1/matches/{match_id}/sentiment-timeline?window_s=30`
```json
{ "match_id": "m_001", "points": [
    { "ts": "2026-07-04T18:00:00Z", "positive_pct": 65.0, "negative_pct": 12.0,
      "neutral_pct": 23.0, "mentions": 1200, "top_emotion": "joy", "event_tag": null },
    { "ts": "2026-07-04T18:23:00Z", "positive_pct": 96.2, "negative_pct": 2.1,
      "neutral_pct": 1.7, "mentions": 3400, "top_emotion": "joy", "event_tag": "goal" } ] }
```

### B.4 Heatmap — `GET /api/v1/matches/{match_id}/heatmap`
```json
{ "match_id": "m_001", "updated_at": "2026-07-04T18:32:10Z", "countries": [
    { "country_code": "BR", "avg_sentiment": 0.94, "dominant_emotion": "joy", "mentions": 12000 },
    { "country_code": "DE", "avg_sentiment": -0.31, "dominant_emotion": "anger", "mentions": 3400 } ] }
```
`avg_sentiment` ∈ [−1, 1]: mean of (+score for positive, −score for negative, 0 for neutral).

### B.5 Topics, feed, moments
- `GET /api/v1/matches/{match_id}/topics` → `{ "match_id": "...", "topics": [ { "label": "messi", "mentions": 8210, "trend": "up" } ] }` (`trend`: `up|down|flat` vs 5 min ago; ≤ 10 topics)
- `GET /api/v1/matches/{match_id}/feed?limit=50` → `{ "match_id": "...", "messages": [ClassifiedMessage, ...] }` (newest first, `limit` ≤ 200)
- `GET /api/v1/matches/{match_id}/moments` → `{ "match_id": "...", "moments": [MomentEvent, ...] }` (newest first)

### B.6 Forecast (Feature 3)
- `GET /api/v1/matches/{match_id}/forecast` → current `AudienceForecast` (latest reforecast if any, else baseline):
```json
{
  "match_id": "m_001", "demand_index": 87.4, "predicted_attendance_pct": 97.2,
  "sellout_probability": 0.91,
  "feature_importance": [ { "feature": "stage", "importance": 0.34 },
                          { "feature": "rivalry_flag", "importance": 0.22 } ],
  "is_reforecast": true, "baseline_demand_index": 74.1, "delta_vs_baseline_pct": 17.9,
  "trigger_description": "Live buzz percentile 0.93 after goal moment mo_0007",
  "model_cv_mae": 0.041, "computed_at": "2026-07-04T18:33:00Z"
}
```
- `POST /api/v1/forecast/reforecast` body `{ "match_id": "m_001" }` → recomputes with the live momentum snapshot, persists, broadcasts `forecast_update` on WS, returns the new `AudienceForecast`. `409 INSUFFICIENT_DATA` if no momentum key exists.

### B.7 Campaigns (Feature 5)
- `POST /api/v1/campaigns/generate`
```json
// request — segment/channel optional; omitted ⇒ strategy engine chooses
{ "match_id": "m_001", "industry": "food_delivery",
  "target_segment": null, "channel": null,
  "trigger": "manual",                       // "manual" | "auto"
  "moment_id": "mo_0007", "budget_usd": 100000 }
```
```json
// response = CampaignCard (also the WS campaign_alert payload and the GET list item)
{
  "campaign_id": "c_0047", "match_id": "m_001", "industry": "food_delivery",
  "archetype": "celebration_flash_offer", "target_segment": "deal_seekers",
  "channel": "push", "window_minutes": 15,
  "window_ends_at": "2026-07-04T18:47:00Z", "trigger": "auto", "moment_id": "mo_0007",
  "copy": { "headline": "GOOOL means GO TIME 🍕", "body": "Brazil just scored — celebrate with 25% off your order for the next 15 minutes.",
            "cta": "Order now", "hashtags": ["#BRAvsARG", "#GoalDeal"],
            "variant_b": { "headline": "...", "body": "...", "cta": "..." } },
  "roi": { /* full ROIResult, §B.8 shape */ },
  "evidence": {
    "moment": "joy surge +26pp, velocity 4.1σ (mo_0007, goal)",
    "segment": "deal_seekers: 14,820 fans in sample (share 29.6%), avg engagement 71, preferred channel push",
    "regional": "top regions BR (12,000 mentions), AR (8,400)",
    "multiplier": { "M": 1.92, "arousal": 0.90, "emotion_brand_fit": 0.85,
                    "moment_strength": 0.80, "segment_match": 0.70, "k": 2.0 },
    "benchmark_source": "WordStream Google Ads benchmarks 2025 — food_delivery/push"
  },
  "confidence": 0.88, "llm_fallback": false, "created_at": "2026-07-04T18:32:40Z"
}
```
- `GET /api/v1/matches/{match_id}/campaigns` → `{ "campaigns": [CampaignCard, ...] }` (newest first)
- `POST /api/v1/content/generate` body `{ "match_id", "platform": "instagram"|"youtube", "creator_niche": "football_reactions" }` → `ContentIdeaCard`:
```json
{ "content_id": "ci_0012", "match_id": "m_001", "platform": "instagram",
  "archetype": "content_idea",
  "idea": { "format": "15s vertical reel", "hook": "React in the first 2 seconds to Messi's goal",
            "concept": "...", "hashtags": ["..."], "post_within_minutes": 20 },
  "evidence": { "trending": "topic 'messi' 8,210 mentions and rising; dominant emotion joy (0.9 arousal)",
                "regional": "peak audiences BR, AR", "timing": "engagement windows decay ~20 min post-moment" },
  "confidence": 0.84, "llm_fallback": false, "created_at": "..." }
```

### B.8 ROI (Feature 6)
- `POST /api/v1/roi/simulate`
```json
// request
{ "match_id": "m_001", "industry": "food_delivery", "channel": "push",
  "budget_usd": 100000, "timing": "now" }        // "now" (live momentum) | "baseline" (M = 1)
```
```json
// response = ROIResult
{
  "industry": "food_delivery", "channel": "push", "budget_usd": 100000,
  "multiplier": { "M": 1.92, "arousal": 0.90, "emotion_brand_fit": 0.85,
                  "moment_strength": 0.80, "segment_match": 0.70, "k": 2.0 },
  "funnel": { "cpm_usd": 6.0, "frequency": 2.5, "impressions": 16666667, "reach": 6666667,
              "ctr_baseline": 0.009, "ctr_effective": 0.0173, "clicks": 288000,
              "cvr_baseline": 0.03, "cvr_effective": 0.0438, "conversions": 12614,
              "aov_usd": 30.0, "revenue_usd": 378420 },
  "roas": 3.78, "roi_pct": 278.4,
  "baseline_comparison": { "roas": 1.35, "roi_pct": 35.0, "revenue_usd": 135000 },
  "benchmark_source": "WordStream Google Ads benchmarks 2025 — food_delivery/push",
  "confidence": 0.88, "computed_at": "..."
}
```
- `POST /api/v1/roi/media-plan` body `{ "budget_usd": 500000, "industry": "beverages", "match_ids": ["m_001","m_002","m_003"] }` →
```json
{ "total_budget_usd": 500000, "industry": "beverages",
  "allocations": [ { "match_id": "m_001", "budget_usd": 300000, "share_pct": 60.0,
                     "demand_index": 87.4, "expected_roas": 2.9, "expected_revenue_usd": 870000,
                     "rationale": "Highest demand index (87) and rivalry fixture; capped at 60%." } ],
  "expected_total_roas": 2.4 }
```
- `GET /api/v1/roi/benchmarks?industry=food_delivery` → `{ "rows": [ { "industry", "channel", "cpm_usd", "ctr", "cvr", "aov_usd", "frequency", "source", "source_url" } ] }`

### B.9 Fans (Feature 4)
- `GET /api/v1/fans/segments` → `{ "segments": [Segment, ...], "silhouette_score": 0.41, "n_fans": 50000 }`
```json
Segment = {
  "segment_id": "deal_seekers", "display_name": "Deal-Seekers",
  "size": 14820, "share_pct": 29.6, "avg_engagement_score": 71.2, "avg_annual_value_usd": 84.0,
  "top_countries": ["BR", "MX", "IN"], "preferred_channel": "push", "churn_risk_pct": 12.4,
  "defining_traits": ["push opt-in 91%", "high app sessions", "low avg spend", "offer-responsive"]
}
```
- `GET /api/v1/fans/segments/{segment_id}` → `Segment` + `"centroid_features": { "<feature>": <scaled value>, ... }`
- `GET /api/v1/fans/next-best-actions?industry=food_delivery` → `{ "actions": [ { "segment_id": "deal_seekers", "industry": "food_delivery", "channel": "push", "archetype": "celebration_flash_offer", "timing_rule": "within 15 min of a joy moment", "expected_ctr": 0.0162, "rationale": "91% push opt-in and 1.8× benchmark response to time-limited offers." } ] }` (`industry` omitted ⇒ all starred industries)
- `GET /api/v1/fans/active-now?match_id=m_001` → `{ "match_id": "m_001", "active_segments": [ { "segment_id": "deal_seekers", "activity_share_pct": 41.0, "basis": "country-volume overlap with segment geography" } ], "computed_at": "..." }`

### B.10 Replay control — `POST /api/v1/replay/control`
Body `{ "action": "start"|"stop"|"seek"|"speed", "match_id": "m_001", "speed": 4.0, "seek_t_offset": 1370 }` → `{ "accepted": true }`. W2 only publishes to Redis `replay:control` (§E.5); W1's worker executes.

---

## §C — WebSocket contract

Endpoint: `ws(s)://<host>/ws/matches/{match_id}`. All frames: `{ "event": "<type>", "data": { ... } }`.

| event | fires when | `data` shape |
|---|---|---|
| `kpi_update` | every 5–10 s | §B.2 body |
| `new_message` | each classified message | `ClassifiedMessage` |
| `topic_trend` | topics list changed (≤ 1/30 s) | §B.5 topics body |
| `moment_detected` | W1 detects a moment | `MomentEvent` |
| `campaign_alert` | auto-campaign persisted | `CampaignCard` (§B.7) |
| `forecast_update` | reforecast computed | `AudienceForecast` (§B.6) |

Client→server frames: none (read-only stream). Unknown event types must be ignored by clients, never crash them.

---

## §D — PostgreSQL schema (frozen)
*W2 owns the SQLAlchemy models + migrations. W1 writes to `raw_messages`, `nlp_results`, `sentiment_snapshots`, `country_sentiment`, `moments` via `ingestion/writer.py`. W2 writes the rest. Nobody else issues DDL.*

```sql
CREATE TABLE matches (
    id                TEXT PRIMARY KEY,
    home_team         TEXT NOT NULL,
    away_team         TEXT NOT NULL,
    kickoff_time      TIMESTAMPTZ NOT NULL,
    stage             INT NOT NULL DEFAULT 0,        -- 0 group … 5 final
    venue_capacity    INT NOT NULL DEFAULT 60000,
    city              TEXT,
    city_population_m REAL,
    home_rank         INT, away_rank INT,
    rivalry_flag      BOOLEAN DEFAULT FALSE,
    host_involved     BOOLEAN DEFAULT FALSE,
    status            TEXT NOT NULL DEFAULT 'upcoming'   -- upcoming | live | finished
);

CREATE TABLE raw_messages (
    id          BIGSERIAL PRIMARY KEY,
    external_id TEXT NOT NULL,
    match_id    TEXT REFERENCES matches(id),
    source      TEXT NOT NULL,                          -- §A.3
    author      TEXT,
    text        TEXT NOT NULL,
    country     TEXT,                                    -- ISO-2, nullable
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, external_id)
);

CREATE TABLE nlp_results (
    message_id      BIGINT PRIMARY KEY REFERENCES raw_messages(id),
    sentiment       TEXT NOT NULL,                       -- §A.1
    sentiment_score REAL NOT NULL,
    emotion         TEXT NOT NULL,                       -- §A.2
    emotion_score   REAL NOT NULL,
    topics          TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE sentiment_snapshots (
    id           BIGSERIAL PRIMARY KEY,
    match_id     TEXT REFERENCES matches(id),
    ts           TIMESTAMPTZ NOT NULL,
    positive_pct REAL, negative_pct REAL, neutral_pct REAL,
    mentions     INT,
    top_emotion  TEXT,
    event_tag    TEXT                                    -- §A.7 event tags, nullable
);
CREATE INDEX idx_snapshots_match_ts ON sentiment_snapshots (match_id, ts);

CREATE TABLE country_sentiment (
    id               BIGSERIAL PRIMARY KEY,
    match_id         TEXT REFERENCES matches(id),
    ts               TIMESTAMPTZ NOT NULL,
    country_code     TEXT NOT NULL,
    avg_sentiment    REAL,                               -- [-1, 1]
    dominant_emotion TEXT,
    mentions         INT
);
CREATE INDEX idx_country_match_ts ON country_sentiment (match_id, ts);

CREATE TABLE moments (
    id           TEXT PRIMARY KEY,                       -- mo_0001
    match_id     TEXT REFERENCES matches(id),
    event_tag    TEXT NOT NULL,
    detected_at  TIMESTAMPTZ NOT NULL,
    momentum     JSONB NOT NULL,                         -- MomentumSnapshot at detection
    description  TEXT
);

CREATE TABLE campaigns (
    id             TEXT PRIMARY KEY,                     -- c_0001
    match_id       TEXT REFERENCES matches(id),
    industry       TEXT NOT NULL,
    archetype      TEXT NOT NULL,
    target_segment TEXT NOT NULL,
    channel        TEXT NOT NULL,
    trigger        TEXT NOT NULL,                        -- manual | auto
    moment_id      TEXT REFERENCES moments(id),
    window_minutes INT,
    copy_json      JSONB NOT NULL,
    roi_json       JSONB NOT NULL,
    evidence_json  JSONB NOT NULL,
    confidence     REAL,
    llm_fallback   BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE content_ideas (
    id           TEXT PRIMARY KEY,                       -- ci_0001
    match_id     TEXT REFERENCES matches(id),
    platform     TEXT NOT NULL,
    idea_json    JSONB NOT NULL,
    evidence_json JSONB NOT NULL,
    confidence   REAL,
    llm_fallback BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE forecasts (
    id            BIGSERIAL PRIMARY KEY,
    match_id      TEXT REFERENCES matches(id),
    is_reforecast BOOLEAN NOT NULL DEFAULT FALSE,
    forecast_json JSONB NOT NULL,                        -- full AudienceForecast
    created_at    TIMESTAMPTZ DEFAULT now()
);
```

---

## §E — Redis contract

### E.1 Key inventory

| key | type | writer → reader | content |
|---|---|---|---|
| `match:{id}:kpis` | hash | W1 → W2 | fields = §B.2 body (flat strings; numbers stringified) |
| `match:{id}:heatmap` | string (JSON) | W1 → W2 | §B.4 body |
| `match:{id}:topics` | zset | W1 → W2 | member = topic label, score = mention count |
| `match:{id}:momentum` | string (JSON) | W1 → W2 (→ W3 via pydantic) | `MomentumSnapshot`, refreshed every 15 s |
| `match:{id}:feed` | list (capped 500, LPUSH+LTRIM) | W1 → W2 | JSON `ClassifiedMessage` per item |
| `match:{id}:events` | pub/sub channel | W1 publishes; W2 subscribes | §E.2 frames |
| `replay:control` | pub/sub channel | W2 publishes; W1 subscribes | §E.5 frames |
| `ingest:seen:{source}` | set | W1 only | dedupe external IDs |

### E.2 Events channel frames (`match:{id}:events`)
Same envelope as WebSocket: `{ "event": "...", "data": { ... } }`. W1 publishes `new_message` (ClassifiedMessage), `topic_trend`, and `moment_detected` (MomentEvent). W2 republishes to WS clients verbatim and additionally publishes `campaign_alert` / `forecast_update` to WS itself (not on this channel).

### E.3 MomentumSnapshot — the most-consumed payload
Exactly the `MomentumSnapshot` model in §A.8, serialized as JSON. W2 deserializes it and passes it (as the pydantic model) into W3's `reforecast()` and `simulate_roi()`. If the key is missing or `updated_at` is older than 60 s, W2 treats live signal as unavailable → `timing="now"` behaves as `"baseline"` and forecast endpoints return baseline (never crash, never invent).

### E.4 Moment detection rule & payload (locked)
- **Trigger:** per-minute message volume z-score ≥ **2.5** versus the trailing 10-minute mean/std, AND |`sentiment_delta_pp`| ≥ **10** over the last 2 minutes. Cooldown **120 s**.
- **Tag classification:** dominant emotion `joy` + positive delta → `goal`; dominant `anger` (or `disgust`) + topics intersecting {`var`, `referee`, `penalty`, `red card`} → `var_controversy` (or `red_card` if "red card" present); replay marker objects force the tag (`goal`, `full_time`, `kickoff`); otherwise `surge_other`.
- **Payload:** a `MomentEvent` (§A.8) — also written to the `moments` table by W1.

### E.5 Replay control frames (`replay:control`)
```json
{ "action": "start", "match_id": "m_001", "file": "replay_match_01.json", "speed": 1.0 }
{ "action": "speed", "match_id": "m_001", "speed": 4.0 }
{ "action": "seek",  "match_id": "m_001", "seek_t_offset": 1370 }
{ "action": "stop",  "match_id": "m_001" }
```

### E.6 Replay file schema (`data/replay/*.json`)
```json
{ "meta": { "match_id": "m_001", "captured_at": "2026-06-28T19:00:00Z",
            "description": "BRA vs ARG friendly, captured live via reddit+youtube" },
  "items": [
    { "t_offset": 0,    "external_id": "rd_abc1", "source": "reddit",  "author": "u/fan1",
      "text": "Kickoff! Vamos!!", "country": "BR" },
    { "t_offset": 1380, "marker": "goal" },
    { "t_offset": 1381, "external_id": "yt_x9",  "source": "youtube", "author": "carlos",
      "text": "GOOOOOL!!! 🔥🔥", "country": "AR" } ] }
```
Message items map to `RawMessageIn` with `source` preserved (analytics count them by their true origin; provenance metadata may add `via_replay` internally, but the §A.3 `replay` source value is reserved for the hand-written dev fixture only). Marker items only steer the moment detector's tag.

---

## §F — Internal Python interface: `intelligence` package (W3 → W2)
*W3 implements these exact signatures; W2 imports and calls them. All inputs/outputs are `contracts.models` types. Pure functions + committed artifacts; no I/O beyond reading `data/` and `artifacts/` at module load. All list/dict returns JSON-serializable via `.model_dump()`.*

### F.1 Forecast — `intelligence.forecast.predict`
```python
def predict_audience(features: MatchFeatures) -> AudienceForecast
def reforecast(features: MatchFeatures, momentum: MomentumSnapshot) -> AudienceForecast
def compute_live_buzz(momentum: MomentumSnapshot) -> float        # 0–1; formula in docstring
def get_model_metrics() -> dict                                    # {"cv_mae": ..., "n_train_rows": ...}
```
`AudienceForecast` = §B.6 response model. `reforecast` must populate `is_reforecast=True`, `baseline_demand_index`, `delta_vs_baseline_pct`, `trigger_description`.

### F.2 Segments — `intelligence.segments.predict`
```python
def get_segments() -> SegmentReport                # {"segments": [Segment], "silhouette_score": float, "n_fans": int}
def get_segment_detail(segment_id: str) -> SegmentDetail          # Segment + centroid_features
def get_next_best_actions(industry: str | None = None) -> list[NextBestAction]
def get_active_overlay(country_volumes: dict[str, int]) -> list[ActiveSegment]
    # country_volumes: ISO-2 → mention count (W2 extracts from the heatmap JSON)
def get_engagement_scores_summary() -> dict        # {"mean": float, "p90": float, "weights": {...}}
```
`Segment`, `NextBestAction`, `ActiveSegment` = §B.9 shapes. Engagement score: RFM-D, four 0–100 percentile subscores (Recency inverted `days_since_last_engagement`; Frequency `app_sessions_30d + matches_attended + social_shares_30d`; Monetary total spend; Digital `streaming_minutes_30d + email_open_rate + push_opt_in`), frozen weights 0.25/0.25/0.25/0.25.

### F.3 ROI — `intelligence.roi.api`
```python
def simulate_roi(request: ROIRequest,
                 momentum: MomentumSnapshot | None,     # None ⇒ baseline (M = 1.0)
                 target_segment: str | None = None) -> ROIResult
def compute_multiplier(momentum: MomentumSnapshot, industry: str,
                       target_segment: str | None) -> MultiplierBreakdown
def best_channel(industry: str, segment_id: str) -> Channel
def plan_media(budget_usd: float, industry: str,
               forecasts: list[AudienceForecast],
               momenta: dict[str, MomentumSnapshot | None]) -> MediaPlan
def get_benchmarks(industry: str | None = None) -> list[BenchmarkRow]
```
`ROIRequest` = §B.8 request model (W2 resolves `timing` into `momentum`/`None` before calling). `ROIResult`, `MultiplierBreakdown`, `MediaPlan`, `BenchmarkRow` = §B.8 shapes. Math: spec §6.1/§6.3 with §A.6 constants; `baseline_comparison` always populated; unknown (industry, channel) benchmark pair ⇒ raise `contracts.errors.BenchmarkNotFound` (W2 maps to `VALIDATION_ERROR`).

**Confidence (used by F.1/F.3 and surfaced on cards):** `confidence = clip(0.4·volume_support + 0.3·moment_recency + 0.3·segment_support, 0, 1)` where `volume_support = clip(volume_5m / 500, 0, 1)`, `moment_recency = clip(1 − age_min/30, 0, 1)` (1.0 if no moment required), `segment_support = clip(segment_size / 5000, 0, 1)`. Baseline mode: fixed 0.75 (benchmark-only figure).

---

## §G — W2-internal shapes (documented for cross-review; only W2 code touches them)

### G.1 CampaignBrief (strategy engine → RAG layer)
```python
class CampaignBrief(BaseModel):
    match_id: str; industry: Industry; archetype: Archetype
    target_segment: SegmentId; channel: Channel
    window_minutes: int; moment: MomentEvent | None
    emotion: Emotion; top_topics: list[str]; top_countries: list[str]
    roi: ROIResult; segment: Segment
    tone_notes: str                      # from playbook row
```

### G.2 Gemini output schema (strict JSON mode; reject/repair-or-fallback on parse failure)
```json
{ "headline": "string ≤ 60 chars", "body": "string ≤ 140 chars", "cta": "string ≤ 25 chars",
  "hashtags": ["≤ 4 items"],
  "variant_b": { "headline": "...", "body": "...", "cta": "..." } }
```
(Content flavour: `{ "format", "hook", "concept ≤ 280 chars", "hashtags", "post_within_minutes" }`.)

### G.3 Prompt template skeleton (`app/rag/prompts.py`)
```
SYSTEM: You are a senior performance-marketing copywriter. You write copy ONLY.
You never invent statistics; use only the numbers given. Output strict JSON per the schema.

CONTEXT (measured, do not alter):
- Moment: {moment.description} at {moment.detected_at}
- Audience: segment "{segment.display_name}" ({segment.size} fans, {segment.top_countries});
  dominant emotion {emotion} | trending: {top_topics}
- Offer window: {window_minutes} minutes | Channel: {channel} | Industry: {industry}

RETRIEVED GUIDANCE:
{k=4 knowledge-base snippets: framework, tone guide, 2 templates}

TASK: Write the campaign copy for archetype "{archetype}". {tone_notes}
OUTPUT JSON SCHEMA: {schema}
```

---

## §H — Contract tests (frozen alongside this document)
One test module per surface, written once from this doc, owned collectively, changed only with the contract:
- `tests/test_contract_momentum.py` — W1's Redis momentum/KPI/heatmap payloads parse into §A.8 models
- `tests/test_contract_moment.py` — replayed goal beat yields a valid `MomentEvent` with `event_tag="goal"`
- `tests/test_contract_f.py` — every §F signature exists, accepts fixture inputs, returns contract models (runs against stubs and real implementations identically)
- `tests/test_contract_rest.py` — every §B endpoint returns 200 + response-model-valid JSON against seed data
- `tests/test_purity.py` — `intelligence/` imports no fastapi/redis/sqlalchemy

*End of contract v1.0.0.*
