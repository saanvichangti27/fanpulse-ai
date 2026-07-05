"""Deterministic strategy engine (spec §7.1) — decides WHO / WHEN / WHERE /
WHAT-TYPE from measured data + the playbook. No LLM is involved here; Gemini
only writes the words afterwards (gemini_client.py)."""
from datetime import datetime, timezone
from typing import Optional

from ...intelligence import segments
from ...intelligence import roi as roi_engine
from .playbook import PLAYBOOK
from ...contracts import (
    SegmentReport, ROIResult, CampaignBrief, MomentEvent,
    Emotion, Industry, SegmentId, Channel,
)


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
    requested_channel: Optional[Channel] = None,
    activity_overlay: Optional[dict] = None,   # segment_id -> live activity_share_pct
) -> CampaignBrief:
    # 1. WHO — best segment by live activity x engagement (or the requested one)
    report = SegmentReport(**segments.get_segments())
    if activity_overlay:
        for s in report.segments:
            s.activity_share_pct = activity_overlay.get(s.segment_id.value, 0.0)
    if requested_segment:
        target = next((s for s in report.segments if s.segment_id == requested_segment),
                      report.segments[0])
    else:
        target = max(report.segments,
                     key=lambda s: max(s.activity_share_pct, 1.0) * s.avg_engagement_score)

    # Live context from the moment (measured), or neutral baseline
    if moment:
        emotion = moment.momentum.dominant_emotion
        top_topics = moment.momentum.top_topics
        top_countries = moment.momentum.top_countries
        momentum_dict = moment.momentum.model_dump(mode="json")
        age_min = max(0.0, (datetime.now(timezone.utc)
                            - moment.detected_at.replace(tzinfo=timezone.utc)).total_seconds() / 60.0) \
            if moment.detected_at.tzinfo is None else \
            max(0.0, (datetime.now(timezone.utc) - moment.detected_at).total_seconds() / 60.0)
    else:
        emotion = Emotion.neutral
        top_topics, top_countries = [], []
        momentum_dict, age_min = None, 0.0

    # 4. WHAT-TYPE + 2. WHEN + 3. WHERE — playbook, overridable channel
    entry = get_playbook_entry(emotion, industry)
    archetype = entry["archetype"]
    window_minutes = entry["window_minutes"]
    channel = requested_channel if requested_channel else entry["channel_default"]

    # 5. ROI — real benchmark funnel at the live multiplier (+ baseline inside)
    roi_result = ROIResult(**roi_engine.simulate_roi(
        industry=industry.value,
        channel=channel.value,
        budget_usd=budget_usd,
        momentum=momentum_dict,
        target_segment=target.segment_id.value,
        segment_top_countries=target.top_countries,
        segment_size=target.size,
        moment_age_min=age_min,
    ))

    return CampaignBrief(
        match_id=match_id,
        industry=industry,
        archetype=archetype,
        target_segment=target.segment_id,
        channel=channel,
        window_minutes=window_minutes,
        moment=moment,
        emotion=emotion,
        top_topics=top_topics,
        top_countries=top_countries,
        roi=roi_result,
        segment=target.model_dump(),
        tone_notes=entry["tone_notes"],
    )


def build_evidence(brief: CampaignBrief) -> dict:
    """Contract §B.7 evidence block — every claim traces to measured data."""
    seg = brief.segment
    evidence = {
        "moment": (f"{brief.moment.description} ({brief.moment.moment_id}, "
                   f"{brief.moment.event_tag.value})") if brief.moment
                  else "no live moment — baseline targeting",
        "segment": (f"{seg.segment_id.value}: {seg.size:,} fans in sample "
                    f"({seg.share_pct:.1f}%), avg engagement {seg.avg_engagement_score:.0f}, "
                    f"prefers {seg.preferred_channel.value}"),
        "regional": (f"top live regions {', '.join(brief.top_countries)}"
                     if brief.top_countries else "no live regional signal"),
        "multiplier": brief.roi.multiplier.model_dump(),
        "benchmark_source": brief.roi.benchmark_source,
    }
    return evidence
