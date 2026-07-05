import os
import sys

# Add the root directory to path to allow imports from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.db import SessionLocal
from backend.app.models_db import Message, Moment
from backend.contracts import Sentiment, Emotion, Source
from datetime import datetime, timezone

def trigger_fake_moment():
    db = SessionLocal()
    now = datetime.now(timezone.utc).isoformat()
    
    # Insert a fake message that looks like a joy spike
    fake_msg = Message(
        external_id="fake_001",
        match_id="m_001",
        source=Source.replay,
        author="fake_user",
        text="GOAAAAAAAAL!!!! VAMOSSSS!!!",
        country="BR",
        sentiment=Sentiment.positive,
        sentiment_score=0.99,
        emotion=Emotion.joy,
        emotion_score=0.98,
        topics_json='["goal", "messi"]',
        created_at=now
    )
    
    db.add(fake_msg)
    db.commit()
    
    # We would also trigger a moment row here and manually invoke on_moment callback if needed.
    print(f"Fake moment triggered and message inserted at {now}!")
    db.close()

if __name__ == "__main__":
    trigger_fake_moment()
