from backend.app.db import SessionLocal
from backend.app.models_db import Match
from backend.intelligence.forecast import predict_audience
from backend.app.routers.predictions import get_match_features

db = SessionLocal()
match = db.query(Match).filter(Match.id == "m_001").first()
if not match:
    print("Match not found")
else:
    features = get_match_features(match)
    print("Features:", features)
    res = predict_audience(features)
    print("Result:", res)
