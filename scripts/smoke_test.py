import os
import sys
import json
from dotenv import load_dotenv

# Fix windows terminal encoding crash for emojis
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.contracts import MomentEvent, MomentumSnapshot, Emotion
from backend.app.automation import on_moment

def run_smoke_test():
    load_dotenv()
    print("Triggering Smoke Test...")
    
    # 1. Create a dummy MomentEvent simulating a huge goal (Joy)
    moment = MomentEvent(
        moment_id="mom_smoke_001",
        match_id="m_001",
        ts="2026-07-05T12:00:00Z",
        momentum=MomentumSnapshot(
            match_id="m_001",
            volume_1m=1200,
            volume_5m=3000,
            volume_ratio=2.5,
            arousal=98.5,
            dominant_emotion=Emotion.joy,
            excitement_score=98.5,
            positive_pct=85.0,
            sentiment_delta_pp=15.0,
            top_topics=["messi", "goal", "unbelievable"],
            top_countries=["BR", "US"],
            computed_at="2026-07-05T12:00:00Z"
        ),
        triggering_messages=["msg_1", "msg_2"],
        event_tag="goal",
        detected_at="2026-07-05T12:00:00Z",
        description="A massive goal was just scored!"
    )
    
    print("Sending MomentEvent to on_moment auto-campaign engine...")
    on_moment(moment)
    print("Auto-campaign generation complete.")
    
    # Check DB
    from backend.app.db import SessionLocal
    from backend.app.models_db import Campaign
    
    db = SessionLocal()
    campaigns = db.query(Campaign).filter(Campaign.match_id == "m_001").all()
    print(f"\nFound {len(campaigns)} campaigns in database for match m_001:")
    for c in campaigns:
        copy_data = json.loads(c.copy_json)
        print(f"\n--- Campaign ID: {c.id} | Industry: {c.industry} ---")
        print(f"Segment: {c.target_segment}")
        print(f"Archetype: {c.archetype}")
        print(f"Headline: {copy_data.get('headline')}")
        print(f"LLM Fallback: {bool(c.llm_fallback)}")
        print("-" * 50)
        
    db.close()
    print("\nSmoke test finished successfully!")

if __name__ == "__main__":
    run_smoke_test()
