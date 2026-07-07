import requests
import time
import json
import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE = "http://127.0.0.1:8000/api/v1"
MATCH_ID = "m_001"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("Waiting for backend to start...")
    while True:
        try:
            health = requests.get(f"{BASE}/health", timeout=2).json()
            if health.get("status") == "ok":
                break
        except Exception:
            pass
        time.sleep(1)

    for _ in range(5):
        try:
            kpis = requests.get(f"{BASE}/matches/{MATCH_ID}/kpis", timeout=2).json()
            feed = requests.get(f"{BASE}/matches/{MATCH_ID}/feed?limit=15", timeout=2).json()
            moments = requests.get(f"{BASE}/matches/{MATCH_ID}/moments", timeout=2).json()

            clear_screen()
            print("="*60)
            print(" FANPULSE AI - LIVE YOUTUBE PIPELINE DASHBOARD")
            print("="*60)
            
            # KPIs
            if "total_messages" in kpis:
                print(f" TOTAL MESSAGES : {kpis['total_messages']}")
                print(f" VOLUME RATIO   : {kpis.get('volume_ratio', 0.0):.1f}x (vs baseline)")
                print(f" DOMINANT EMOT. : {kpis.get('dominant_emotion', 'N/A').upper()}")
                print(f" SENTIMENT DELTA: {kpis.get('sentiment_delta_pp', 0.0):+.1f}pp")
            else:
                print(" Waiting for messages to accumulate...")

            print("\n" + "-"*60)
            print(" LATEST MOMENTS")
            print("-"*60)
            ms = moments.get("moments", [])
            if not ms:
                print(" No moments detected yet.")
            for m in ms[-3:]:
                print(f" [{m['event_tag'].upper()}] {m['description']}")

            print("\n" + "-"*60)
            print(" LIVE COMMENTS FEED (Latest 15)")
            print("-"*60)
            messages = feed.get("messages", [])
            if not messages:
                print(" Waiting for comments...")
            for msg in messages:
                # Truncate text if too long
                text = msg['text'].replace('\n', ' ')
                if len(text) > 80:
                    text = text[:77] + "..."
                author = msg['author']
                if len(author) > 15:
                    author = author[:12] + "..."
                
                sentiment = msg['sentiment'].upper()
                print(f" [{sentiment:8}] {author:15} | {text}")
                
            print("\n" + "="*60)
            print(" Press Ctrl+C to exit.")
            time.sleep(3)
        except Exception as e:
            print(f"Error fetching data: {e}")
            time.sleep(3)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting dashboard.")
        sys.exit(0)
