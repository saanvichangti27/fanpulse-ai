# FanPulse AI — Work Distribution
### The build plan for three parallel workstreams, designed for AI-agent execution
*Companion to `FanPulse_AI_Product_Spec.md` (the WHAT) and `API_Contract.md` (the interfaces). Read all three before building.*

---

## 0. How to use this document (instructions for the AI agents)

You are one of three build agents. Each agent owns **exactly one workstream** below and must:

1. Build **only** inside your owned directories (§2 ownership map). Never edit another workstream's files.
2. Treat `docs/API_Contract.md` and `backend/contracts/` as **frozen law**. If your work seems to require a contract change, STOP and surface it to the humans — do not silently change a field name, enum value, table column, or function signature.
3. Build against the **stubs and fixtures** specified for your workstream (§each person's section) so you never wait on another workstream.
4. **No frontend work.** The project is backend-first for now. The only UI-adjacent deliverables are: FastAPI's auto-generated Swagger UI (`/docs`), a single static `scripts/dev_console.html` WebSocket dump page (owned by Saanvi, ~50 lines, unstyled), and CLI smoke-test scripts. Do not install Node, React, or any frontend tooling.
5. Meet your **Definition of Done** checklist before declaring your workstream complete.

**Precedence if documents conflict:** `API_Contract.md` > this document > `FanPulse_AI_Product_Spec.md` > the old Build Bible. The Build Bible's hour-by-hour schedule and its frontend/deployment sections are **superseded** — ignore them.

---

## 1. The three workstreams at a glance

| Workstream | Owner | Scope (spec §5 feature numbers) | Primary output boundary |
|---|---|---|---|
| **W1 · Ingestion & Live Intelligence** | **R S Raksha** | Feature 1 entirely (connectors, NLP, aggregation, moment detection) + Replay Engine + the data behind Feature 2's heatmap | Writes to Postgres tables + Redis keys per contract §D/§E. Never exposes an API. |
| **W2 · Backend, Database & Recommendation Engine** | **Saanvi C** | FastAPI app, DB schema/migrations/seeds, WebSocket, all REST endpoints + Feature 5 entirely (strategy engine, playbook, RAG knowledge base, Gemini copy generation) | Serves the REST/WS contract §B/§C. Reads what W1 writes; imports what W3 delivers. |
| **W3 · Predictive Intelligence** | **Raksha S** | Feature 3 (audience/demand forecast model + live re-forecast), Feature 4 (synthetic fan CRM, segmentation, engagement scoring, NBA matrix), Feature 6 (ROI funnel math, engagement multiplier, media planner) + all synthetic/benchmark datasets | Delivers the pure-Python `backend/intelligence/` package implementing the function signatures in contract §F, plus trained model artifacts and datasets. Never writes FastAPI code. |

**Who talks to whom, and only through what:**

```
W1 (Raksha R)                      W2 (Saanvi)                        W3 (Raksha S)
ingestion worker  ──writes──►  Postgres + Redis  ◄──reads/serves──  FastAPI app
                              (contract §D, §E)        │
                                                       │ imports (contract §F)
                                                       ▼
                                             intelligence/ package
                                          (models, ROI math, segments)
```

- W1 and W2 integrate **only** through the database schema and Redis keys/channels. W1 never imports W2's app code (except the SQLAlchemy models module, read-only — see §4.2).
- W3 and W2 integrate **only** through the Python function signatures in contract §F. W3's package has **zero** knowledge of FastAPI, Redis, or the DB — it takes pydantic models in and returns pydantic models out.
- W1 and W3 never integrate directly. W3's live inputs (momentum, moment events) arrive as pydantic models passed in by W2, which reads them from Redis.

This is what makes the three streams safe to build in parallel by independent agents: every seam is a frozen, typed contract.

---

## 2. Repository structure & ownership map

Everything below is created in this repo. **Ownership column is absolute** — an agent may read anything but write only what it owns.

```
fanpulse-ai/
├── docs/                                  # shared, frozen (humans only edit)
│   ├── FanPulse_AI_Product_Spec.md
│   ├── Work_Distribution.md               # this file
│   └── API_Contract.md
├── backend/
│   ├── contracts/                         # OWNER: Saanvi (created FIRST, then frozen)
│   │   ├── __init__.py
│   │   ├── enums.py                       # every enum in contract §A, verbatim
│   │   ├── models.py                      # every pydantic model in contract §A–§F, verbatim
│   │   └── constants.py                   # arousal map, excitement formula weights, etc. (§A.6)
│   ├── app/                               # OWNER: Saanvi
│   │   ├── main.py                        # FastAPI entrypoint + startup wiring
│   │   ├── config.py                      # env loading (pydantic-settings)
│   │   ├── db.py                          # engine/session factory
│   │   ├── models_db.py                   # SQLAlchemy models == contract §D verbatim
│   │   ├── migrations/                    # Alembic
│   │   ├── seed.py                        # fixture seeding (matches, sample rows for all tables)
│   │   ├── redis_io.py                    # typed helpers for every Redis key in contract §E
│   │   ├── routers/
│   │   │   ├── matches.py                 # matches, kpis, timeline, heatmap, topics, feed, moments
│   │   │   ├── fans.py                    # segments, NBA, active-now
│   │   │   ├── campaigns.py               # campaign + content generation & listing
│   │   │   ├── predictions.py             # forecast, reforecast
│   │   │   ├── roi.py                     # simulate, media-plan, benchmarks, industries
│   │   │   └── replay.py                  # replay control passthrough (publishes to Redis)
│   │   ├── ws.py                          # WebSocket endpoint + Redis pub/sub fanout
│   │   ├── strategy/
│   │   │   ├── engine.py                  # deterministic strategy engine (spec §7.1)
│   │   │   └── playbook.py                # (emotion × industry) → archetype table, in code
│   │   └── rag/
│   │       ├── knowledge_base/            # *.md KB entries (frameworks, tone guides, templates)
│   │       ├── retriever.py               # keyed retrieval (baseline); optional vector upgrade
│   │       ├── prompts.py                 # Gemini prompt templates (contract §G.3)
│   │       └── gemini_client.py           # wrapper: debounce, cache, strict-JSON parse, fallback
│   ├── ingestion/                         # OWNER: Raksha R
│   │   ├── __init__.py
│   │   ├── config.py                      # its own env loading (API keys, poll intervals)
│   │   ├── connectors/
│   │   │   ├── base.py                    # Connector ABC: fetch() -> list[RawMessageIn]
│   │   │   ├── reddit_connector.py
│   │   │   ├── youtube_connector.py
│   │   │   └── news_connector.py
│   │   ├── replay/
│   │   │   ├── capture.py                 # runs live connectors, dumps data/replay/*.json
│   │   │   └── replay_engine.py           # streams captured JSON on a clock, obeys replay:control
│   │   ├── nlp/
│   │   │   ├── pipeline.py                # sentiment + emotion + topics, local models, batch API
│   │   │   └── geo.py                     # country inference heuristics
│   │   ├── aggregate/
│   │   │   ├── aggregator.py              # snapshots, country rollups, topics, KPIs, momentum
│   │   │   └── moment_detector.py         # velocity z-score + emotion-swing rule (contract §E.4)
│   │   ├── writer.py                      # ALL DB/Redis writes go through this one module
│   │   └── run_worker.py                  # entrypoint: python -m ingestion.run_worker
│   ├── intelligence/                      # OWNER: Raksha S
│   │   ├── __init__.py
│   │   ├── data_gen/
│   │   │   ├── gen_fans.py                # synthetic fan CRM generator (§5.2 of this doc)
│   │   │   ├── gen_history.py             # historical match table builder + buzz_index synth
│   │   │   └── build_benchmarks.py        # validates/loads benchmarks.csv
│   │   ├── forecast/
│   │   │   ├── features.py                # MatchFeatures -> model feature vector
│   │   │   ├── train.py                   # trains XGBoost, saves artifacts/
│   │   │   ├── predict.py                 # implements contract §F.1
│   │   │   └── artifacts/                 # model.json, feature_importance.json (committed)
│   │   ├── segments/
│   │   │   ├── train.py                   # KMeans fit, persona naming, saves artifacts/
│   │   │   ├── engagement.py              # RFM-D engagement score (contract §F.2)
│   │   │   ├── nba.py                     # next-best-action matrix
│   │   │   ├── predict.py                 # implements contract §F.2
│   │   │   └── artifacts/                 # kmeans.pkl, scaler.pkl, segment_profiles.json
│   │   └── roi/
│   │       ├── funnel.py                  # funnel math (spec §6.1)
│   │       ├── multiplier.py              # engagement multiplier M (spec §6.3, contract §F.3)
│   │       ├── planner.py                 # cross-match media planner
│   │       └── api.py                     # implements contract §F.3 (single import surface)
│   ├── tests/                             # each owner adds tests for their own package
│   ├── requirements.txt                   # shared; additions announced in team chat
│   └── .env.example
├── data/
│   ├── replay/                            # OWNER: Raksha R — captured real match reactions
│   │   └── replay_match_01.json
│   ├── synthetic/                         # OWNER: Raksha S
│   │   └── fans.csv
│   ├── historical/                        # OWNER: Raksha S
│   │   └── matches_history.csv
│   └── benchmarks/                        # OWNER: Raksha S
│       ├── benchmarks.csv                 # real published values + source citations
│       └── emotion_brand_fit.csv
└── scripts/                               # OWNER: Saanvi
    ├── seed_all.py                        # DB migrate + seed + load intelligence artifacts
    ├── smoke_test.py                      # end-to-end: replay 60s → assert API responses
    └── dev_console.html                   # bare WS event dump page (the ONLY html file allowed)
```

**Shared-file rules:**
- `backend/contracts/` is written **once** by Saanvi in Phase 0 (transcribed verbatim from `API_Contract.md`), then frozen. All three packages import from it: `from contracts.enums import Emotion`, `from contracts.models import ROIRequest`.
- `requirements.txt`: append-only; announce every addition in team chat (dependency conflicts are the #1 silent integration killer).
- `.env.example`: each owner adds their own variables under a commented section header with their name.

**Git workflow:** branch per workstream — `ws1-ingestion`, `ws2-backend`, `ws3-intelligence`. Merge to `main` only at the integration phase boundaries (§6). `main` must always run `scripts/smoke_test.py` clean.

---

## 3. Workstream W1 — R S Raksha: Ingestion & Live Intelligence (Feature 1 + Replay Engine)

### 3.1 Mission
Everything from raw fan text to decision-ready aggregates. You own the truth about *what fans are feeling right now*. Your work ends at the database/Redis boundary: you produce classified messages, rolling aggregates, momentum snapshots, and moment events, formatted exactly per contract §D/§E. **You do not call Gemini, do not build APIs, and do not make marketing decisions** — Saanvi's strategy engine consumes your outputs and does that (your data is an *input* to her RAG pipeline; it is never sent to the LLM raw).

### 3.2 What to build, component by component

**a) Connectors** (`ingestion/connectors/`)
- All implement `base.Connector` ABC with one method: `fetch() -> list[contracts.models.RawMessageIn]`.
- **Reddit** (PRAW, script app): poll new comments from configured subreddits (`r/soccer` + team subs from config), every 20s. This is the always-alive live source — it must work during any demo regardless of match schedule.
- **YouTube** (google-api-python-client): resolve live video ID with `search.list` **once per match** (cache it — quota rule from Build Bible §2.3), then poll `liveChatMessages.list` every 15s.
- **News** (NewsAPI, GNews fallback): poll every 10 min, headlines + descriptions become messages with `source="news"`.
- Each connector: dedupe by external ID (keep a seen-set in Redis `ingest:seen:{source}`), swallow-and-log API errors (a dead connector must never crash the worker), respect rate limits from config.

**b) Replay Engine** (`ingestion/replay/`) — *build this FIRST; every other workstream's testing depends on data flowing*
- `capture.py`: runs the real connectors against a live match and dumps everything to `data/replay/replay_match_01.json` in the schema of contract §E.6 (message + `t_offset` seconds since capture start). Run it during any real football match early in the build. Manually tag the three narrative beats by inserting marker objects: `{"t_offset": 1380, "marker": "goal"}`, plus `var_controversy` and `full_time`.
- `replay_engine.py`: streams the captured file into the **exact same pipeline path** as live data (same `RawMessageIn`, same NLP, same writer) at a configurable speed multiplier. Subscribes to Redis channel `replay:control` (contract §E.5) for `start` / `stop` / `speed` / `seek` commands so Saanvi's API (and later the demo) can drive it.
- Until the real capture exists, generate `data/replay/replay_dev_fixture.json` (~200 hand-written messages with the three beats) so W2/W3 have flowing data from day one. Replace with the real capture when available; keep both files.

**c) NLP pipeline** (`ingestion/nlp/pipeline.py`)
- Loaded **once at worker startup**: sentiment `cardiffnlp/twitter-roberta-base-sentiment-latest`, emotion `j-hartmann/emotion-english-distilroberta-base`, topics via KeyBERT. All local CPU, batch inference (batch size 16–32) for throughput.
- Emotion labels are locked to the 7 the model emits (contract §A.2). Map arousal per message from `contracts.constants.AROUSAL` — do not invent your own mapping (Raksha S's ROI multiplier uses the same table; they must agree).
- Entity extraction: KeyBERT keyphrases + a simple watchlist match (player names from the match's team rosters in `matches` seed data, plus "VAR", "referee", "penalty") — watchlist hits get priority as topics.
- `geo.py` country inference, in priority order: (1) explicit country in replay data, (2) subreddit→country map, (3) flag emoji in author/text, (4) language detection → most-likely country, (5) `None`. Output ISO-3166 alpha-2.

**d) Aggregator** (`ingestion/aggregate/aggregator.py`) — runs on a 15s tick:
- Write `sentiment_snapshots` and `country_sentiment` rows (contract §D) per active match.
- Refresh Redis: `match:{id}:kpis` (compute excitement score with the frozen formula in contract §A.6 — never your own variant), `match:{id}:heatmap`, `match:{id}:topics`, `match:{id}:momentum`, and push each classified message to the capped list `match:{id}:feed` + publish `new_message` on the events channel.
- Momentum snapshot (contract §E.3) is the single most consumed thing you produce — Saanvi's strategy engine and Raksha S's re-forecast/multiplier both read it. Get its fields exactly right.

**e) Moment detector** (`ingestion/aggregate/moment_detector.py`)
- Implements the locked rule in contract §E.4 (velocity z-score ≥ 2.5 vs trailing 10-min baseline AND |sentiment delta| ≥ 10pp over 2 min), classifies the `event_tag` via the emotion/topic heuristics there, writes a `moments` row, and publishes `moment_detected` on `match:{id}:events`. This event is the trigger for the entire downstream auto-campaign flow — its payload shape (contract §E.4) is sacred.
- Cooldown: no second moment within 120s of the last (prevents alert storms).

**f) Worker entrypoint** (`run_worker.py`): one process, asyncio: connector polls + NLP batch loop + aggregator tick + moment detector + replay-control subscriber. Config-selectable source mix (`SOURCES=replay` / `SOURCES=reddit,youtube,news,replay`).

### 3.3 Data sources
Real: Reddit API (PRAW), YouTube Data API v3, NewsAPI/GNews. Real-captured: your replay files. You use **no synthetic data** except the temporary dev fixture in (b).

### 3.4 Stubs you rely on (so you never wait)
- Phase 0 gives you `contracts/` and the Alembic migration from Saanvi. Until her seed exists, insert one `matches` row yourself in a local script.
- You need nothing from Raksha S. Nothing you build imports `app/` routers, `strategy/`, `rag/`, or `intelligence/`.

### 3.5 Definition of Done
- [ ] `python -m ingestion.run_worker` with `SOURCES=replay` populates all four DB tables and all Redis keys, continuously, from a cold start
- [ ] With `SOURCES=reddit`, real live Reddit comments flow through the same path (the live-credibility demo)
- [ ] Replay of the goal beat fires exactly one `moment_detected` event with `event_tag="goal"` and a correct payload
- [ ] Momentum snapshot fields match contract §E.3 byte-for-byte (validated by `tests/test_contract_momentum.py`)
- [ ] Kill the network mid-replay: worker keeps running (models are local; only live connectors log errors)
- [ ] A real captured replay file exists at `data/replay/replay_match_01.json` with the three tagged beats

---

## 4. Workstream W2 — Saanvi C: Backend, Database & AI Recommendation Engine (Feature 5)

### 4.1 Mission
You own the spine: the database schema, the API surface, the WebSocket, and the entire Feature-5 brain — the deterministic strategy engine, the marketing playbook, the RAG knowledge base, and the Gemini copy layer. You are the only workstream that integrates with both others, which is why you also own the frozen `contracts/` package and go first in Phase 0.

### 4.2 Phase 0 duty (do this before anything else — the other two are blocked on it)
1. Transcribe `docs/API_Contract.md` §A into `backend/contracts/` (enums, pydantic models, constants) **verbatim**.
2. Write `app/models_db.py` (SQLAlchemy) matching contract §D exactly, plus the initial Alembic migration.
3. Write `app/seed.py`: 6 fixture matches (mix of upcoming/live/finished, World Cup-flavoured fixtures) + a handful of fixture rows in every other table so every endpoint can return non-empty data before real pipelines run.
4. Commit to `main`. Announce. This unblocks W1 (imports `models_db` read-only for writes) and W3 (imports `contracts` models for signatures).

Rule for others: W1 imports `app.models_db` and `app.db` **only** — never routers/strategy/rag. W3 imports `contracts` **only**.

### 4.3 What to build, component by component

**a) REST API** (`app/routers/`) — implement every endpoint in contract §B, response shapes verbatim. Serving strategy: hot reads (KPIs, heatmap, topics, feed, momentum) come from Redis via `redis_io.py`; historical reads (timeline, moments, campaigns) from Postgres; intelligence reads (forecast, segments, NBA, ROI, media plan) call the `intelligence/` package functions per contract §F. Until W3 delivers, code against `intelligence` stubs you write yourself returning contract-valid dummies (`app/stubs_intelligence.py`), switched by env flag `USE_INTELLIGENCE_STUBS=true`.

**b) WebSocket layer** (`app/ws.py`) — `/ws/matches/{match_id}` per contract §C: subscribe to Redis `match:{id}:events`, fan out to connected clients. Also emit `kpi_update` every 5–10s from the Redis KPI hash. Events: `kpi_update`, `new_message`, `topic_trend`, `moment_detected`, `campaign_alert`, `forecast_update`.

**c) Strategy engine** (`app/strategy/engine.py`) — the deterministic Feature-5 core (spec §7.1). Input: a `MomentEvent` (auto path, triggered by the `moment_detected` subscription) or a manual `CampaignGenerateRequest`. Steps, all pure/deterministic:
1. **WHO** — call `intelligence.segments` for segment profiles; score each segment: `fit = segment_industry_affinity × country_overlap_with_active_regions × avg_engagement_score`; pick the top one (or honor an explicitly requested segment).
2. **WHEN** — timing window from the playbook archetype (e.g. goal → 15 min), starting at the moment timestamp.
3. **WHERE** — channel with best benchmark ROI for (industry × segment preferred channels), via `intelligence.roi.api.best_channel()`.
4. **WHAT-TYPE** — archetype lookup from `playbook.py`: the `(emotion × industry) → archetype` table transcribed from spec §7.1, extended to cover all 15 industries × 7 emotions (fall back to `brand_awareness` archetype for weak fits).
5. Call `intelligence.roi.api.simulate_roi()` for predicted CTR/ROAS at the current moment, and assemble the **evidence trail** (contract §B.7 `evidence` block) from the momentum snapshot + segment stats + multiplier breakdown. Output: a `CampaignBrief` (contract §G.1).

**d) RAG + Gemini copy layer** (`app/rag/`) — spec §7.2:
- **Knowledge base**: 25–40 markdown files in `rag/knowledge_base/`, each with YAML frontmatter `{archetype, industry, channel, type: framework|tone|template|example}`. Content: copywriting frameworks (AIDA, PAS), per-industry tone guides, 2–3 example templates per starred industry × archetype. You author these (LLM-assisted authoring is fine; curate them).
- **Retriever** (`retriever.py`): baseline = deterministic frontmatter filtering on (archetype, industry, channel) returning top-k=4 entries. Optional upgrade (only after everything else is done): local `all-MiniLM-L6-v2` embedding similarity over the KB.
- **Prompt** (`prompts.py`): contract §G.3 template — Brief + retrieved snippets + live trending topics + strict JSON output schema (§G.2). The prompt must state: *use only the numbers provided; do not invent statistics.*
- **Gemini client** (`gemini_client.py`): `gemini-2.5-flash`, JSON-mode; server-side debounce ≥ 12s between calls; response cache keyed `(match, archetype, industry, segment)`; on any failure or rate-limit, fall back to a filled template from the KB (`fallback: true` in the response) — the demo must never show a spinner that doesn't resolve.
- **Content-recommendation flavour** (spec §7.3): same pipeline with `archetype="content_idea"` and creator-oriented prompt — serves `POST /content/generate`.

**e) Auto-campaign trigger**: on `moment_detected` → run strategy engine for the default demo industry set (config `AUTO_CAMPAIGN_INDUSTRIES=food_delivery,merch_apparel`) → persist `campaigns` rows → publish `campaign_alert` on the events channel. Debounced: max one auto-generation batch per moment.

**f) Replay control passthrough** (`routers/replay.py`): `POST /replay/control` publishes to Redis `replay:control` (contract §E.5). You never import ingestion code.

**g) Test/demo tooling** (`scripts/`): `seed_all.py`, `smoke_test.py` (start from cold DB → seed → assert every §B endpoint returns 200 + contract-valid shape → run 60s of replay → assert a moment fired and a campaign exists), `dev_console.html` (connect WS, dump events as JSON lines — deliberately ugly).

### 4.4 Data sources
No datasets of your own. Your "data" is the KB you author, the playbook table, and prompt templates. Env: `GEMINI_API_KEY`, `DATABASE_URL`, `REDIS_URL`. Local dev runs Postgres + Redis via a `docker-compose.yml` you own at repo root.

### 4.5 Stubs you rely on
- W1 not running? `seed.py` fixture rows + a tiny `scripts/fake_momentum.py` (you write it) that sets contract-valid Redis keys and publishes one fake `moment_detected` — so you can develop the auto-campaign path end-to-end alone.
- W3 not delivered? `app/stubs_intelligence.py` per §4.3(a).

### 4.6 Definition of Done
- [ ] Every endpoint in contract §B returns contract-valid JSON (pydantic response models enforce this) with only seed data present
- [ ] `dev_console.html` shows live `kpi_update` / `new_message` / `moment_detected` / `campaign_alert` events while W1's replay runs
- [ ] A fake `moment_detected` produces a persisted campaign card with a complete evidence trail and grounded copy (real Gemini call) in < 15s
- [ ] Gemini unreachable → fallback template card is served, `fallback: true`, no error surfaced
- [ ] `scripts/smoke_test.py` passes from a cold database
- [ ] Swagger UI (`/docs`) renders every endpoint with request/response examples — this is our stand-in frontend

---

## 5. Workstream W3 — Raksha S: Predictive Intelligence (Features 3, 4, 6)

### 5.1 Mission
You own every number the product predicts: the audience/demand forecast and its live re-forecast (F3), the fan segments, engagement scores and next-best-action matrix (F4), and the ROI funnel + engagement multiplier + media planner (F6). You also own **all synthetic and benchmark datasets**, including their generation code. You deliver a **pure Python package** (`backend/intelligence/`) implementing contract §F exactly — no FastAPI, no Redis, no DB access, no async. Determinism rule: every function is a pure function of its inputs + committed artifacts; all randomness seeded (`RANDOM_SEED=42` everywhere).

### 5.2 Feature 4 first — the synthetic fan CRM (everything else references segments)

**Dataset:** `data/synthetic/fans.csv`, **50,000 rows**, generated by `intelligence/data_gen/gen_fans.py`.

**Exact schema** (this is also contract §F.2's feature space — keep in sync):

| column | type | description |
|---|---|---|
| `fan_id` | str | `f_000001`… |
| `age` | int | 16–70 |
| `country_code` | str | ISO-2, drawn from a football-nation prior (BR, AR, DE, FR, GB, ES, IT, MX, US, IN, SA, JP, NG, …) |
| `favourite_team` | str | national team, correlated with country (80% home team, 20% other) |
| `matches_attended` | int | lifetime, Poisson |
| `tickets_bought_24m` | int | Poisson |
| `avg_ticket_spend_usd` | float | LogNormal |
| `merch_purchases_12m` | int | Poisson |
| `merch_spend_usd_12m` | float | LogNormal |
| `app_sessions_30d` | int | NegBinomial |
| `email_open_rate` | float | Beta, 0–1 |
| `push_opt_in` | bool | Bernoulli |
| `days_since_last_engagement` | int | Exponential |
| `streaming_minutes_30d` | int | Gamma |
| `social_shares_30d` | int | Poisson |
| `preferred_channel` | enum | contract §A.4 Channel, persona-conditioned categorical |

**Generation technique — persona-first sampling (write this in the module docstring; it's the defense against "you just made up random numbers"):**
1. Define 5 latent persona archetypes with a per-persona parameter table (hardcoded in `gen_fans.py`): **Superfan** (8% prior; high attendance ~Poisson(6), high merch ~LogNormal(μ=5.8), low recency-gap), **Traveling Ultra** (7%; highest attendance/ticket spend, mid digital), **Casual Streamer** (35%; near-zero attendance, high streaming/app, mid opens), **Deal-Seeker** (30%; low spend, high push opt-in ~0.9, high app sessions, offer-responsive), **Lapsed Fan** (20%; historic activity, `days_since_last_engagement`~Exp(mean 200)).
2. Sample persona from the categorical prior → sample every feature from that persona's distributions → add cross-feature noise.
3. **Drop the persona column** before saving. KMeans must *re-discover* the structure — that's what makes the clustering demo honest ("we recover 5 behavioural clusters from raw features; here's the silhouette score").

**Segmentation** (`segments/train.py`): StandardScaler → KMeans (k selected from 3–8 by silhouette; expected k=5) → name clusters by rule-matching centroid profiles to the 5 persona names (contract §A.5 slugs) → save `kmeans.pkl`, `scaler.pkl`, `segment_profiles.json` (per-segment: size, share, centroid, top countries, preferred channel, avg engagement, avg annual value, churn risk = share with recency-gap > 90d).

**Engagement score** (`segments/engagement.py`): RFM-D per contract §F.2 — four 0–100 subscores (Recency = inverted percentile of `days_since_last_engagement`; Frequency = percentile of sessions+attendance+shares; Monetary = percentile of total spend; Digital = percentile of streaming+opens+opt-in), combined with frozen weights 0.25 each. Deterministic given the CSV.

**NBA matrix** (`segments/nba.py`): for each (segment × starred industry): recommended channel (segment preference ∩ best benchmark ROI), offer archetype (from the playbook logic mirror in contract §A.7), timing rule, expected CTR (= benchmark CTR × segment affinity factor from `segment_profiles.json`), and a one-line rationale string citing the segment stats. Returns contract §F.2 `NextBestAction` models.

### 5.3 Feature 3 — audience/demand forecast

**Dataset:** `data/historical/matches_history.csv` built by `gen_history.py` from **real public data**: Kaggle "FIFA World Cup" matches dataset (1930–2022, includes attendance) + Wikipedia attendance tables for recent tournaments. Document the exact source URLs in the module docstring.

**Feature table** (= contract §F.1 `MatchFeatures`): `stage` (ordinal 0–5: group→final), `home_rank`, `away_rank`, `rank_gap`, `rivalry_flag` (hardcoded rivalry-pairs list), `host_involved`, `city_population_m`, `venue_capacity`, `day_of_week`, `kickoff_hour_local`, `buzz_index` (0–1). Target: `attendance_pct` (attendance ÷ capacity, clipped to 1.05).

**`buzz_index` — the honest hybrid:** historical rows have no social data, so training-time buzz is synthesized with a *documented* formula: `buzz = clip(0.40·stage_norm + 0.25·rivalry + 0.20·(1 − rank_gap_norm) + 0.15·host_involved + N(0, 0.05), 0, 1)`. At **inference** time it's computed from W1's real live data: `buzz_live = clip(0.6·volume_percentile + 0.4·norm_velocity, 0, 1)` from the `MomentumSnapshot` passed in by W2. Put both formulas in docstrings; this transparency is the defense.

**Model** (`forecast/train.py`): XGBoost regressor (or sklearn GBR fallback), 5-fold CV, save `artifacts/model.json` + `artifacts/feature_importance.json` + CV MAE in `artifacts/metrics.json` (the API exposes real metrics, not vibes).

**Inference** (`forecast/predict.py`, contract §F.1): `predict_audience(features) -> AudienceForecast` (demand index 0–100 = predicted attendance_pct × 100 rescaled, sell-out probability = calibrated fraction of trees predicting ≥ 0.98 fill, top-5 feature importances) and `reforecast(features, momentum) -> AudienceForecast` — recompute with `buzz_index=buzz_live` and include `delta_vs_baseline_pct` + `trigger_description`. **The delta between those two calls is the live-loop demo moment; make sure a strong momentum snapshot moves the forecast visibly (sanity-test: goal-level momentum ⇒ +5 to +20 points).**

### 5.4 Feature 6 — ROI engine

**Datasets** (`data/benchmarks/`):
- `benchmarks.csv` — schema: `industry, channel, cpm_usd, ctr, cvr, aov_usd, frequency, source, source_url`. One row per (industry × channel) for all 15 industries × applicable channels. Values from **real published benchmarks** (WordStream/Google Ads industry benchmarks, Meta & YouTube ad benchmark reports, Statista CPM data, industry AOV studies). Every row cites its source. Where a niche combination has no published number, interpolate from the nearest category and mark `source="interpolated"` — honesty beats fake precision.
- `emotion_brand_fit.csv` — `industry, emotion, fit` (0–1), the hand-built matrix from spec §6.3, all 15 × 7 filled, with a rationale comment column.

**Funnel** (`roi/funnel.py`): spec §6.1 verbatim — Budget→Impressions→Reach→Clicks→Conversions→Revenue→ROAS/ROI. Returns the full step-by-step breakdown (contract §F.3 `FunnelBreakdown`) — the API shows every intermediate number; that's the glass-box.

**Multiplier** (`roi/multiplier.py`): spec §6.3 verbatim: `M = clamp(1 + K·Arousal·Fit·MomentStrength·SegmentMatch, 0.7, 2.5)`, K = 2.0; `CTR_eff = CTR·M`, `CVR_eff = CVR·(1+(M−1)·0.5)`. Arousal from `contracts.constants.AROUSAL[momentum.dominant_emotion]`; Fit from the CSV; MomentStrength = `clip(velocity_zscore/4, 0, 1)`; SegmentMatch computed from segment-profile country/affinity overlap (document the formula). Returns `MultiplierBreakdown` with every factor exposed. Baseline mode (`timing="baseline"`) forces M=1.0 — the API's before/after comparison depends on both modes.

**Simulator + planner** (`roi/api.py`, contract §F.3): `simulate_roi(request, momentum, segment_profiles)` → funnel at M and at baseline, side by side; `best_channel(industry, segment)`; `plan_media(budget, industry, forecasts)` → allocate proportional to `demand_index × expected_M`, greedy with a 60% single-match cap, per-match expected returns. `confidence` per spec §6.6 (data-support score: message volume + moment recency + segment population; formula in docstring).

### 5.5 Stubs you rely on
Nothing live. Your only inputs are contract §F pydantic models — write your own fixture instances (`tests/fixtures_f.py`) including a "goal-moment" and a "dead-moment" `MomentumSnapshot`. You never touch Redis, the DB, or the API.

### 5.6 Definition of Done
- [ ] `gen_fans.py`, `gen_history.py` run seeded and reproduce identical CSVs; all datasets + artifacts committed
- [ ] `benchmarks.csv` complete for 15 industries with real citations; `emotion_brand_fit.csv` fully populated
- [ ] KMeans recovers ~5 clusters (silhouette reported in `segment_profiles.json`); personas named per contract §A.5
- [ ] Forecast CV MAE recorded in `artifacts/metrics.json`; goal-level momentum moves reforecast +5..+20 demand points
- [ ] Worked example from spec §6.5 reproduces within rounding: $100k food-delivery push, dead moment ROAS ≈ 1.35, goal moment (M≈1.9) ROAS ≈ 3.7
- [ ] Every contract §F function passes the shared contract tests (`tests/test_contract_f.py`) using only fixture inputs
- [ ] Package imports and runs with zero FastAPI/Redis/DB imports (`tests/test_purity.py` asserts this)

---

## 6. Integration plan (broad phases, no clocks)

| Phase | Gate to pass | What happens |
|---|---|---|
| **0 · Foundation** | `contracts/` + DB migration + seeds on `main`; docker-compose up works | Saanvi commits the frozen ground truth. W1 starts replay-fixture + NLP; W3 starts data generation. |
| **1 · Independent build** | Each workstream's own tests green on its branch | Everyone builds against stubs/fixtures per their section. No cross-branch imports. |
| **2 · Pairwise integration** | (a) W1→W2: replay running ⇒ Saanvi's endpoints/WS serve real flowing data. (b) W3→W2: stubs flag off ⇒ real intelligence behind every endpoint. | Merge to `main` one pair at a time. Fix mismatches *against the contract* — the contract wins; the code changes. |
| **3 · Full loop** | `scripts/smoke_test.py` green on `main`: cold start → seed → replay → moment fires → auto-campaign persists with real Gemini copy + real ROI + evidence trail → reforecast delta visible | The complete demo spine works headless. Only now does frontend work begin (separately planned later). |

**Conflict-prevention rules (all agents):**
1. The contract is law; code conforms to it, never vice-versa. Contract changes require: human approval → edit `docs/API_Contract.md` + `backend/contracts/` in one commit → bump the version header → announce.
2. Never edit files outside your ownership map (§2). Shared files (`requirements.txt`, `.env.example`) are append-only with announcement.
3. Every cross-boundary payload has a contract test (`tests/test_contract_*.py`) — those tests are written once from the contract doc and are as frozen as the contract.
4. All randomness seeded; all model artifacts committed — any agent can reproduce any other's outputs.
5. If blocked on another workstream, build the stub the contract implies and keep moving; never reach into their branch.
