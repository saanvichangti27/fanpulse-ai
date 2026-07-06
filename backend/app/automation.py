"""Auto-campaign path: run_ingestion's moment loop calls on_moment(event) for
every detected moment; we generate one campaign per configured industry using
the exact same code path as the manual endpoint (no special-cased logic)."""
import os
import logging

from ..contracts import MomentEvent, Industry
from .db import SessionLocal
from .routers.campaigns import build_campaign_card

logger = logging.getLogger(__name__)


def on_moment(moment: MomentEvent):
    industries_str = os.getenv("AUTO_CAMPAIGN_INDUSTRIES", "")
    if not industries_str:
        return
    budget = float(os.getenv("AUTO_CAMPAIGN_BUDGET_USD", "100000"))

    industries = [Industry(i.strip()) for i in industries_str.split(",") if i.strip()]
    db = SessionLocal()
    try:
        for ind in industries:
            try:
                card = build_campaign_card(
                    db, moment.match_id, ind, budget, trigger="auto", moment=moment,
                )
                logger.info(
                    f"Auto-campaign {card.campaign_id} [{ind.value}] on {moment.event_tag.value} "
                    f"-> {card.target_segment.value}/{card.channel.value}, "
                    f"ROAS {card.roi.roas} (baseline {card.roi.baseline_comparison.roas}), "
                    f"fallback={card.llm_fallback}"
                )
            except Exception as e:
                logger.error(f"Auto-campaign failed for {ind.value}: {e}")
    finally:
        db.close()
