import os
import uuid
from datetime import datetime, timezone
from ..contracts import MomentEvent, Industry, CampaignCard, Source
from .db import SessionLocal
from .models_db import Campaign
from .strategy.engine import generate_campaign_brief
from .gemini_client import generate_copy

def on_moment(moment: MomentEvent):
    # This is called by W1's run_ingestion when a moment is detected
    industries_str = os.getenv("AUTO_CAMPAIGN_INDUSTRIES", "")
    if not industries_str:
        return
        
    industries = [Industry(ind.strip()) for ind in industries_str.split(",") if ind.strip()]
    db = SessionLocal()
    
    try:
        for ind in industries:
            # 1. Generate brief
            budget_usd = 5000.0 # Default auto budget
            brief = generate_campaign_brief(
                match_id=moment.match_id,
                industry=ind,
                budget_usd=budget_usd,
                moment=moment
            )
            
            # 2. Call LLM
            copy, llm_fallback = generate_copy(brief)
            
            # 3. Create Card
            now = datetime.now(timezone.utc).isoformat()
            card = CampaignCard(
                campaign_id=f"cmp_{uuid.uuid4().hex[:8]}",
                match_id=brief.match_id,
                industry=brief.industry,
                target_segment=brief.target_segment,
                channel=brief.channel,
                archetype=brief.archetype,
                window_minutes=brief.window_minutes,
                window_ends_at=now, # Simplified for demo
                status="draft",
                trigger="auto_moment",
                moment_id=moment.moment_id,
                copy=copy,
                roi=brief.roi,
                evidence={
                    "emotion": brief.emotion.value,
                    "top_topics": brief.top_topics,
                    "top_countries": brief.top_countries,
                    "segment_traits": brief.segment.defining_traits
                },
                confidence=0.88 if not llm_fallback else 0.5,
                llm_fallback=llm_fallback,
                created_at=now
            )
            
            import json
            # 4. Save to DB
            db_camp = Campaign(
                id=card.campaign_id,
                match_id=card.match_id,
                industry=card.industry.value,
                archetype=card.archetype.value,
                target_segment=card.target_segment.value,
                channel=card.channel.value,
                trigger=card.trigger,
                moment_id=card.moment_id,
                window_minutes=card.window_minutes,
                copy_json=card.copy_content.model_dump_json(),
                roi_json=card.roi.model_dump_json(),
                evidence_json=json.dumps(card.evidence),
                confidence=card.confidence,
                llm_fallback=1 if card.llm_fallback else 0,
                created_at=card.created_at
            )
            db.add(db_camp)
            
        db.commit()
    except Exception as e:
        print(f"Error in on_moment auto-campaign generation: {e}")
        db.rollback()
    finally:
        db.close()
