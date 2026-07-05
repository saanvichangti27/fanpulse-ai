from typing import Optional
from ..stubs_intelligence import get_segments_stub, get_roi_stub
from .playbook import PLAYBOOK
from ...contracts import CampaignBrief, MomentEvent, Emotion, Industry, SegmentId, Channel

def get_playbook_entry(emotion: Emotion, industry: Industry) -> dict:
    entry = PLAYBOOK.get((emotion.value, industry.value))
    if not entry:
        entry = PLAYBOOK.get(("*", industry.value))
    if not entry:
        entry = PLAYBOOK.get(("*", "*"))
    return entry

def generate_campaign_brief(
    match_id: str,
    industry: Industry,
    budget_usd: float,
    moment: Optional[MomentEvent] = None,
    requested_segment: Optional[SegmentId] = None,
    requested_channel: Optional[Channel] = None
) -> CampaignBrief:
    # 1. WHO
    segments_report = get_segments_stub()
    if requested_segment:
        target_segment_obj = next((s for s in segments_report.segments if s.segment_id == requested_segment), segments_report.segments[0])
    else:
        # Simplistic selection for now (highest score = activity * engagement)
        target_segment_obj = max(segments_report.segments, key=lambda s: s.activity_share_pct * s.avg_engagement_score)
    
    # Extract emotion, top topics, countries from moment or use baseline
    if moment:
        emotion = moment.momentum.dominant_emotion
        top_topics = moment.momentum.top_topics
        top_countries = moment.momentum.top_countries
    else:
        emotion = Emotion.neutral
        top_topics = []
        top_countries = ["BR", "US"]

    # 4. WHAT-TYPE
    playbook_entry = get_playbook_entry(emotion, industry)
    archetype = playbook_entry["archetype"]
    
    # 2. WHEN
    window_minutes = playbook_entry["window_minutes"]
    
    # 3. WHERE
    channel = requested_channel if requested_channel else playbook_entry["channel_default"]

    # 5. ROI
    roi_result = get_roi_stub(industry, channel, budget_usd)

    return CampaignBrief(
        match_id=match_id,
        industry=industry,
        archetype=archetype,
        target_segment=target_segment_obj.segment_id,
        channel=channel,
        window_minutes=window_minutes,
        moment=moment,
        emotion=emotion,
        top_topics=top_topics,
        top_countries=top_countries,
        roi=roi_result,
        segment=target_segment_obj.model_dump(),
        tone_notes=playbook_entry["tone_notes"]
    )
