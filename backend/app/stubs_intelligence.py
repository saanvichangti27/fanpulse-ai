from ..contracts import (
    AudienceForecast, SegmentReport, Segment, SegmentId, Channel, 
    ROIResult, MultiplierBreakdown, ROIResultFunnel, BaselineComparison, 
    Industry, NextBestAction, MediaPlan
)

def get_audience_forecast_stub(match_id: str) -> AudienceForecast:
    return AudienceForecast(
        match_id=match_id,
        demand_index=87.4,
        predicted_attendance_pct=97.2,
        sellout_probability=0.91,
        feature_importance=[{"feature": "stage", "importance": 0.34}],
        is_reforecast=False,
        model_mae=0.041,
        computed_at="2026-07-05T12:00:00Z"
    )

def get_segments_stub() -> SegmentReport:
    return SegmentReport(
        segments=[
            Segment(
                segment_id=SegmentId.deal_seekers,
                display_name="Deal-Seekers",
                size=1480,
                share_pct=29.6,
                avg_engagement_score=71.2,
                avg_annual_value_usd=84.0,
                top_countries=["BR", "MX", "IN"],
                preferred_channel=Channel.push,
                churn_risk_pct=12.4,
                defining_traits=["push opt-in 91%", "high app sessions", "offer-responsive"],
                activity_share_pct=41.0
            )
        ],
        silhouette_score=0.41,
        n_fans=5000
    )

def get_roi_stub(industry: Industry, channel: Channel, budget: float) -> ROIResult:
    return ROIResult(
        industry=industry,
        channel=channel,
        budget_usd=budget,
        multiplier=MultiplierBreakdown(M=1.92, arousal=0.90, emotion_brand_fit=0.85, moment_strength=0.80, segment_match=0.70, k=2.0),
        funnel=ROIResultFunnel(cpm_usd=6.0, frequency=2.5, impressions=16666667, reach=6666667, ctr_baseline=0.009, ctr_effective=0.0173, clicks=288000, cvr_baseline=0.03, cvr_effective=0.0438, conversions=12614, aov_usd=30.0, revenue_usd=378420),
        roas=3.78,
        roi_pct=278.4,
        baseline_comparison=BaselineComparison(roas=1.35, roi_pct=35.0, revenue_usd=135000),
        benchmark_source="WordStream Google Ads benchmarks 2025 - food_delivery/push",
        confidence=0.88,
        computed_at="2026-07-05T12:00:00Z"
    )
