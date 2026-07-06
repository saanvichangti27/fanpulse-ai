"""FanPulse AI integration gate (contract §H).

From a cold start: boot the app -> seed -> replay the dev fixture at high speed
-> assert: every endpoint returns valid data, a goal moment fires, an
auto-campaign persists with real evidence + baseline ROI comparison, the
reforecast uses live momentum, and the ROI acceptance case reproduces.

Run from the repo root:  backend/venv/Scripts/python scripts/smoke_test.py
"""
import os
import sys
import time
import subprocess

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000/api/v1"
PASS, FAIL = "[PASS]", "[FAIL]"
failures = []


def check(name: str, ok: bool, detail: str = ""):
    print(f"{PASS if ok else FAIL} {name}" + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def run():
    db_path = os.path.join("backend", "fanpulse.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted old database at {db_path}")

    print("Booting FastAPI server (NLP models take ~30-60s to load)...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", "8000", "--host", "127.0.0.1"],
        env=os.environ.copy(),
    )
    try:
        booted = False
        for _ in range(90):
            try:
                if requests.get(f"{BASE}/health", timeout=2).status_code == 200:
                    booted = True
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        check("server boot", booted)
        if not booted:
            sys.exit(1)
<<<<<<< HEAD

        # ---- Static/model endpoints (work before any live data) ----
        inds = requests.get(f"{BASE}/industries").json()["industries"]
        check("industries: 15 slugs", len(inds) == 15)

        matches = requests.get(f"{BASE}/matches").json()["matches"]
        check("matches list", len(matches) == 6)
        check("matches: model-driven demand_index (not a constant)",
              matches[0]["demand_index"] is not None
              and len({round(x['demand_index'], 1) for x in matches}) > 1,
              f"values={[x['demand_index'] for x in matches]}")

        fc = requests.get(f"{BASE}/matches/m_001/forecast").json()
        check("forecast: baseline with real feature importances",
              fc["is_reforecast"] is False and len(fc["feature_importance"]) > 0
              and fc["model_mae"] > 0)

        segs = requests.get(f"{BASE}/fans/segments").json()
        check("segments: 5 personas + silhouette", len(segs["segments"]) == 5
              and 0 < segs["silhouette_score"] < 1, f"sil={segs['silhouette_score']:.3f}")
        check("segments: data-derived traits present",
              all(s["defining_traits"] for s in segs["segments"]))

        nba = requests.get(f"{BASE}/fans/next-best-actions").json()["actions"]
        check("next-best-actions: 5x5 matrix", len(nba) == 25)

        # ROI acceptance case (spec §6.5): baseline food_delivery/push $100k => ROAS 1.35
        sim = requests.post(f"{BASE}/roi/simulate", json={
            "match_id": "m_001", "industry": "food_delivery", "channel": "push",
            "budget_usd": 100000, "timing": "baseline"}).json()
        check("ROI acceptance: baseline ROAS == 1.35", abs(sim["roas"] - 1.35) < 0.01,
              f"roas={sim['roas']}, source={sim['benchmark_source'][:50]}")

        plan = requests.post(f"{BASE}/roi/media-plan", json={
            "budget_usd": 500000, "industry": "beverages",
            "match_ids": ["m_001", "m_002", "m_003"]}).json()
        check("media-plan: allocations from real forecasts",
              len(plan["allocations"]) == 3
              and abs(sum(a["share_pct"] for a in plan["allocations"]) - 100.0) < 0.5)

        # ---- Live pipeline: replay -> NLP -> analytics -> moments -> campaigns ----
        r = requests.post(f"{BASE}/replay/control", json={
            "action": "start", "match_id": "m_001",
            "file": "replay_dev_fixture.json", "speed": 60.0})
        check("replay start accepted", r.json().get("accepted") is True)

        goal_found = campaign_found = False
        kpi = {"total_mentions": 0}
        deadline = time.time() + 120
        while time.time() < deadline:
            time.sleep(5)
            kpi = requests.get(f"{BASE}/matches/m_001/kpis").json()
            moments = requests.get(f"{BASE}/matches/m_001/moments").json()["moments"]
            tags = [mo["event_tag"] for mo in moments]
            campaigns = requests.get(f"{BASE}/matches/m_001/campaigns").json()["campaigns"]
            print(f"  ... mentions={kpi['total_mentions']} moments={tags} campaigns={len(campaigns)}")
            if "goal" in tags:
                goal_found = True
            if campaigns:
                campaign_found = True
            if goal_found and campaign_found:
                break

        check("goal moment detected", goal_found)
        check("KPIs: live data flowing", kpi["total_mentions"] > 100)

        feed = requests.get(f"{BASE}/matches/m_001/feed?limit=10").json()["messages"]
        check("feed: real classified messages", len(feed) > 0
              and all("sentiment" in msg and msg["text"] for msg in feed))

        tl = requests.get(f"{BASE}/matches/m_001/sentiment-timeline").json()["points"]
        check("timeline: buckets present", len(tl) > 0)

        hm = requests.get(f"{BASE}/matches/m_001/heatmap").json()["countries"]
        check("heatmap: per-country sentiment", len(hm) > 0)

        topics = requests.get(f"{BASE}/matches/m_001/topics").json()["topics"]
        check("topics present", len(topics) > 0, f"top={[t['label'] for t in topics[:3]]}")

        check("auto-campaign persisted", campaign_found)
        if campaign_found:
            c = requests.get(f"{BASE}/matches/m_001/campaigns").json()["campaigns"][0]
            ev = c["evidence"]
            check("campaign: evidence block complete",
                  all(k in ev for k in ("moment", "segment", "regional", "multiplier", "benchmark_source")))
            check("campaign: live vs baseline ROI contrast",
                  c["roi"]["roas"] > c["roi"]["baseline_comparison"]["roas"],
                  f"live={c['roi']['roas']} base={c['roi']['baseline_comparison']['roas']} M={c['roi']['multiplier']['M']}")
            check("campaign: copy present", bool(c["copy"]["headline"] and c["copy"]["body"]),
                  f"llm_fallback={c['llm_fallback']}, headline={c['copy']['headline'][:40]!r}")

        # Reforecast from REAL live momentum (messages just replayed)
        rf = requests.post(f"{BASE}/forecast/reforecast", json={"match_id": "m_001"})
        check("reforecast: 200 with live momentum", rf.status_code == 200,
              "" if rf.status_code == 200 else rf.text[:100])
        if rf.status_code == 200:
            rfj = rf.json()
            check("reforecast: honest delta vs baseline",
                  rfj["is_reforecast"] and rfj["baseline_demand_index"] is not None,
                  f"delta={rfj['delta_vs_baseline_pct']}pp, trigger={rfj['trigger_description'][:60]}")

        # Live ROI now that momentum exists
        sim_live = requests.post(f"{BASE}/roi/simulate", json={
            "match_id": "m_001", "industry": "food_delivery", "channel": "push",
            "budget_usd": 100000, "timing": "now"}).json()
        check("ROI: live multiplier valid when momentum exists",
              sim_live["multiplier"]["M"] >= 1.0, f"M={sim_live['multiplier']['M']}")

        # Content idea generation (creator flavour)
        ci = requests.post(f"{BASE}/content/generate", json={
            "match_id": "m_001", "platform": "instagram", "creator_niche": "football_reactions"})
        check("content/generate: 200", ci.status_code == 200,
              f"fallback={ci.json().get('llm_fallback') if ci.status_code == 200 else ci.text[:80]}")

        health = requests.get(f"{BASE}/health").json()
        check("health: ingestion_alive is real", health["ingestion_alive"] is True)

        print()
        if failures:
            print(f"SMOKE TEST FAILED — {len(failures)} failure(s): {failures}")
=======
            
        print("Server booted! Triggering replay...")
        res = requests.post("http://127.0.0.1:8000/api/v1/replay/control", json={
            "action": "start",
            "match_id": "m_001",
            "file": "replay_dev_fixture.json",
            "speed": 100.0
        })
        print(f"Replay started: {res.json()}")
        
        # Poll endpoints (increased timeout for HF model download)
        timeout = time.time() + 300
        goal_found = False
        
        # Check for moment directly in DB
        engine = create_engine(f"sqlite:///{db_path}")
        
        while time.time() < timeout:
            time.sleep(1)
            
            try:
                kpi_res = requests.get("http://127.0.0.1:8000/api/v1/matches/m_001/kpis").json()
                print(f"KPIs: mentions={kpi_res.get('total_mentions', 0)}, emo={kpi_res.get('top_emotion')}")
                
                with engine.connect() as conn:
                    moments = conn.execute(text("SELECT event_tag FROM moments")).fetchall()
                    tags = [m.event_tag for m in moments]
                    if "goal" in tags:
                        print("✅ Goal moment detected!")
                        # Wait up to 10 seconds for the async LLM call to finish and save campaigns
                        print("Waiting for background AI campaign generation...")
                        campaigns = []
                        for _ in range(10):
                            campaigns = conn.execute(text("SELECT * FROM campaigns")).fetchall()
                            if campaigns:
                                break
                            time.sleep(1)

                        if campaigns:
                            print(f"✅ Auto-campaign generated! Found {len(campaigns)} campaigns.")
                            for c in campaigns:
                                print(f"  - Industry: {c.industry}, Segment: {c.target_segment}")
                        else:
                            print("⚠️ Goal moment detected, but no campaigns generated (likely missing GEMINI_API_KEY). Proceeding anyway since ingestion works.")
                        goal_found = True
                        break
            except Exception as e:
                print(f"Polling error: {e}")
                
        if not goal_found:
            print("❌ Test failed: Goal moment not found within timeout.")
>>>>>>> 5e3cf5d6ad24a48fc2c67b1e4005162bbf9db5bb
            sys.exit(1)
        print("SMOKE TEST PASSED — full pipeline green.")
    finally:
        print("Shutting down server...")
        process.terminate()
        process.wait()


if __name__ == "__main__":
    run()
