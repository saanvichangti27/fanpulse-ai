# FanPulseAI — Frontend PRD

## Original Problem Statement
Build an ultra-premium, 4-page marketing-agency frontend that reconciles the energy of football with a luxury brand feel (minimalist typography, dark mode, high-contrast metallic accents). Pages: Landing (high-impact hero), Heatmap, Strategies, Matches. Include smooth scroll interactions, page transitions and a striking WebGL 3D element. **Frontend-only** — backend already exists on GitHub; all data must be mock JSON simulating REST responses. Clean, DRY, modular code.

## User Personas
- **Brand Marketer** — find right audience × moment × message × channel with projected ROI.
- **Agency / Media Buyer** — allocate budget across matches and simulate what-if.
- **Content Creator** — get real-time trend/emotion signals and concrete content ideas.
- **Analyst** — inspect segments, model drivers, and evidence behind every recommendation.

## User Choices (locked)
- Brand: **FanPulseAI**
- Palette: **Midnight navy (#050914) + silver/chrome metallic**
- 3D element: **Rotating 3D football with dynamic lighting**
- Typography: **Archivo Black (display) + JetBrains Mono (data)**
- Charts: **Recharts + custom heatmap grid**
- Data: **All JSON mock — no backend calls**

## Architecture
- React 19 + React Router 7 SPA
- `@react-three/fiber@9.0.4` + `@react-three/drei@9.114.0` + `three@0.170.0` for WebGL 3D football
- Framer Motion 11 for scroll reveals, page-transition-style animations, and layout animations
- Recharts 3 for sentiment timeline + demand drivers bar chart
- Sonner for toasts (copy-to-clipboard confirmation)
- Tailwind + shadcn base (customised heavily to editorial dark theme)
- Custom cursor (silver ring, mix-blend-difference)
- Alias `@` → `/app/frontend/src`

## Implemented (2026-02-XX)
- **Landing (`/`)** — 3D chrome football hero, huge display headline "THE PULSE OF THE PITCH, MONETISED.", KPI ticker, manifesto strip, 4 modules (F.01–F.04), stat band (fixtures/moments/segments/ROAS), CTA card
- **Heatmap (`/heatmap`)** — 22-country segmentation grid with sentiment-intensity tint + dominant-emotion dot + segment base color, 6 filter chips (All + 5 segments), hover detail panel, 5 persona cards with size/share/engagement/annual value/channel/churn/traits
- **Strategies (`/strategies`)** — Location dropdown + 15 industry sector chips (iGaming shows 18+ compliance badge), 6 recommendation cards streaming into detail panel with headline + Variant A/B copy + Copy-to-clipboard, multiplier breakdown bars (arousal, emotion_fit, moment, segment), ROI funnel (impressions→revenue) + ROAS, benchmark citation, confidence bar, AI vs Fallback flag
- **Matches (`/matches`)** — Match schedule sidebar (5 fixtures across live/upcoming/finished), Trending topics panel, animated 0–100 demand gauge (SVG stroke-dashoffset), sellout probability, excitement, baseline vs live re-forecast with delta + trigger explanation, Recharts sentiment area timeline, moments list (6 events), demand drivers bar chart
- Global: sticky glass nav (backdrop-blur), KPI ticker, custom silver cursor, chrome corner brackets, grain overlay, footer

## Testing
- Testing agent iteration 1: **100% frontend pass rate**, 0 console errors, all data-testids verified interactive.

## Prioritized Backlog
### P0 (defer — user can wire live)
- Wire mock JSON to real FanPulseAI REST endpoints (2s polling for KPI/timeline/feed)
- Live inbox behaviour: auto-append new strategy cards when moments fire
- Live message feed component (raw evidence view) — not built in v1

### P1
- ROI What-If Simulator page (interactive funnel with live vs baseline)
- Cross-Match Media Planner (budget × industries × candidate matches → allocation table)
- Content Idea cards (creator persona) with hooks + hashtags
- Country drill-down modal from heatmap cells

### P2
- Match-level dark-map globe (three-globe) instead of grid heatmap
- Command palette (⌘K) to jump between matches + strategies
- Persist filter state in URL search params
- Prefers-reduced-motion path (skip cursor + reveal animations)
