import requests
import time
import json

BASE = "http://127.0.0.1:8000/api/v1"

print("Checking Health...")
health = requests.get(f"{BASE}/health").json()
print(f"Health: {json.dumps(health, indent=2)}")

print("Waiting for ingestion to pick up messages...")
time.sleep(10)

kpi = requests.get(f"{BASE}/matches/m_001/kpis").json()
print(f"KPIs: {json.dumps(kpi, indent=2)}")

feed = requests.get(f"{BASE}/matches/m_001/feed?limit=5").json()
print("Latest Feed messages:")
for msg in feed.get("messages", []):
    print(f"- [{msg['sentiment']}] {msg['text']}")

moments = requests.get(f"{BASE}/matches/m_001/moments").json()
print(f"Moments detected: {[m['event_tag'] for m in moments.get('moments', [])]}")
