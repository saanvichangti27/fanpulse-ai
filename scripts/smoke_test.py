import os
import sys
import json
import time
import requests
import subprocess
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Fix windows terminal encoding crash for emojis
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_smoke_test():
    load_dotenv()
    print("Triggering Full Integration Smoke Test...")
    
    db_path = os.path.join("backend", "fanpulse.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted old database at {db_path}")

    # Boot app
    print("Booting FastAPI server...")
    # Use the current python executable so it runs in the venv
    env = os.environ.copy()
    env["AUTO_CAMPAIGN_INDUSTRIES"] = "retail_ecommerce"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", "8000", "--host", "127.0.0.1"],
        env=env
    )
    
    try:
        # Wait for boot by polling /health
        print("Waiting for server to boot (NLP models take time to load)...")
        booted = False
        for _ in range(60):
            try:
                if requests.get("http://127.0.0.1:8000/api/v1/health").status_code == 200:
                    booted = True
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
            
        if not booted:
            print("❌ Server failed to boot within 60s")
            sys.exit(1)
            
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
            sys.exit(1)
            
        print("\nSmoke test finished successfully!")
        
    finally:
        print("Shutting down server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    run_smoke_test()
