import asyncio
import logging
import json
import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Callable, Awaitable

from sqlalchemy import text

from ..contracts import (
    MomentEvent,
    MOMENT_VOLUME_RATIO,
    MOMENT_SENTIMENT_DELTA_PP,
    MOMENT_COOLDOWN_SECONDS,
)
from .nlp import classify_batch
from .analytics import get_momentum
from .geo import infer_country

logger = logging.getLogger(__name__)

# Forced markers from replay files, queued PER MATCH so rapid-fire markers at
# high replay speed are never lost (a single slot used to get overwritten).
_forced_markers: dict[str, deque] = {}

# Auto-kickoff (stream modes): match_ids that have already been auto-kicked so
# the one-time "flip to LIVE on first real ingestion" fires at most once.
_auto_kicked: set[str] = set()

# Flip a still-"upcoming" match to LIVE the first time ingestion produces a real
# momentum snapshot. For captured/live YouTube streams (which carry no scripted
# kickoff marker) this makes the match come alive on its own. OFF by default so
# the synthetic demo — which has its own scripted kickoff marker — is untouched.
AUTO_KICKOFF = os.getenv("AUTO_KICKOFF", "false").lower() == "true"

# Set by run_ingestion; the replay router feeds items into this queue.
INGESTION_QUEUE: asyncio.Queue | None = None


async def _poll_youtube(connector, queue: asyncio.Queue):
    """Poll YouTube LIVE CHAT and enqueue RawMessageIn items. The connector
    tells us how long to wait (YouTube returns pollingIntervalMillis)."""
    while True:
        wait_s = 15.0
        try:
            messages, wait_s = await connector.poll_live_chat()
            if messages:
                logger.info(f"Polled {len(messages)} new live-chat messages from YouTube")
                for msg in messages:
                    await queue.put(msg)
        except Exception as e:
            logger.error(f"YouTube poll error: {e}")
        await asyncio.sleep(max(wait_s, 5.0))


async def _process_queue(session_factory, queue: asyncio.Queue):
    batch = []
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=1.0)

            # Replay marker → queue it for the moment loop (never overwrite)
            if isinstance(item, dict) and "marker" in item:
                match_id = item.get("match_id", "m_001")
                _forced_markers.setdefault(match_id, deque()).append(item["marker"])
                continue

            if isinstance(item, dict):  # replay message item
                batch.append({
                    "external_id": item.get("external_id", ""),
                    "match_id": item.get("match_id", "m_001"),
                    "source": item.get("source", "replay"),
                    "author": item.get("author"),
                    "text": item.get("text", ""),
                    # explicit country wins; else infer (flag emoji / language)
                    "country": infer_country(item.get("text"), item.get("author"),
                                             item.get("country")),
                    # Wall-clock time so the live analytics windows work during replay
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
            else:  # RawMessageIn from a live connector
                batch.append({
                    "external_id": item.external_id,
                    "match_id": item.match_id,
                    "source": item.source.value if hasattr(item.source, "value") else item.source,
                    "author": item.author,
                    "text": item.text,
                    "country": infer_country(item.text, item.author, item.country),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
        except asyncio.TimeoutError:
            pass  # fall through and flush whatever we have

        if batch:
            try:
                texts = [b["text"] for b in batch]
                # NLP runs in a thread so the event loop stays responsive
                results = await asyncio.to_thread(classify_batch, texts)

                with session_factory() as session:
                    for b, res in zip(batch, results):
                        sql = text("""
                            INSERT INTO messages (
                                external_id, match_id, source, author, text, country,
                                sentiment, sentiment_score, emotion, emotion_score, topics_json, created_at
                            ) VALUES (
                                :external_id, :match_id, :source, :author, :text, :country,
                                :sentiment, :sentiment_score, :emotion, :emotion_score, :topics_json, :created_at
                            )
                            ON CONFLICT(source, external_id) DO NOTHING
                        """)
                        session.execute(sql, {
                            **{k: b[k] for k in ("external_id", "match_id", "source", "author", "text", "country")},
                            "sentiment": res["sentiment"],
                            "sentiment_score": res["sentiment_score"],
                            "emotion": res["emotion"],
                            "emotion_score": res["emotion_score"],
                            "topics_json": json.dumps(res["topics"]),
                            "created_at": b["created_at"].replace("+00:00", "Z"),
                        })
                    session.commit()
            except Exception as e:
                logger.error(f"Error processing message batch: {e}")
            finally:
                batch.clear()


def _classify_tag(momentum: dict) -> str:
    """Natural (non-forced) moment tag heuristics (contract §E.2)."""
    if momentum["dominant_emotion"] == "joy" and momentum["sentiment_delta_pp"] > 0:
        return "goal"
    if momentum["dominant_emotion"] in ("anger", "disgust"):
        topics = set(momentum["top_topics"])
        if "red card" in topics:
            return "red_card"
        if topics & {"var", "referee", "penalty"}:
            return "var_controversy"
    return "surge_other"


async def _moment_loop(session_factory, match_id: str,
                       on_moment: Callable[[MomentEvent], Awaitable[None]]):
    """Every 10 s: check the moment rule. Forced replay markers are drained one
    per tick and bypass both the rule and the cooldown (they are deliberate,
    hand-tagged demo beats — the cooldown exists to stop alert storms from the
    detector, not to suppress scripted match events)."""
    last_moment_time = float("-inf")

    while True:
        await asyncio.sleep(10)
        try:
            with session_factory() as session:
                momentum = get_momentum(session, match_id)

                markers = _forced_markers.get(match_id)
                forced_marker = markers.popleft() if markers else None

                if momentum is None:
                    if forced_marker:
                        # Not enough data for a snapshot yet — requeue the marker
                        markers.appendleft(forced_marker)
                    continue

                # Auto-kickoff: the first tick with real momentum on a match that
                # is still "upcoming" synthesizes a kickoff, routed through the
                # normal forced-marker path below. Skipped if a real marker is
                # already firing this tick or the match is already live/finished
                # (so a scripted kickoff marker always wins). Fires at most once.
                if (AUTO_KICKOFF and forced_marker is None
                        and match_id not in _auto_kicked):
                    row = session.execute(
                        text("SELECT status FROM matches WHERE id = :m"),
                        {"m": match_id},
                    ).fetchone()
                    if row and row.status == "upcoming":
                        _auto_kicked.add(match_id)
                        forced_marker = "kickoff"

                natural = (
                    momentum["volume_ratio"] >= MOMENT_VOLUME_RATIO
                    and abs(momentum["sentiment_delta_pp"]) >= MOMENT_SENTIMENT_DELTA_PP
                )
                now = asyncio.get_event_loop().time()
                cooldown_ok = (now - last_moment_time) >= MOMENT_COOLDOWN_SECONDS

                if not (forced_marker or (natural and cooldown_ok)):
                    continue
                last_moment_time = now

                tag = forced_marker if forced_marker else _classify_tag(momentum)
                moment_id = f"mo_{uuid.uuid4().hex[:8]}"
                detected_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                desc = (f"Volume spike {momentum['volume_ratio']}x baseline with "
                        f"{momentum['dominant_emotion']} surge ({momentum['sentiment_delta_pp']:+.1f}pp)")

                session.execute(text("""
                    INSERT INTO moments (id, match_id, event_tag, detected_at, momentum_json, description)
                    VALUES (:id, :match_id, :event_tag, :detected_at, :momentum_json, :description)
                """), {
                    "id": moment_id, "match_id": match_id, "event_tag": tag,
                    "detected_at": detected_at,
                    "momentum_json": json.dumps(momentum), "description": desc,
                })
                session.commit()
                logger.info(f"Moment {moment_id} [{tag}] detected for {match_id}: {desc}")

            # Fire the auto-campaign callback outside the DB session
            try:
                event = MomentEvent(**{
                    "moment_id": moment_id, "match_id": match_id, "event_tag": tag,
                    "detected_at": detected_at, "momentum": momentum, "description": desc,
                })
                if asyncio.iscoroutinefunction(on_moment):
                    await on_moment(event)
                else:
                    await asyncio.to_thread(on_moment, event)
            except Exception as e:
                logger.error(f"Error in on_moment callback: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Moment loop error: {e}")


async def run_ingestion(session_factory, sources: list[str],
                        on_moment: Callable[[MomentEvent], Awaitable[None]]) -> None:
    global INGESTION_QUEUE
    queue = asyncio.Queue()
    INGESTION_QUEUE = queue

    tasks = [
        asyncio.create_task(_process_queue(session_factory, queue)),
        # Demo match. Replay items carry their own match_id; m_001 is the live default.
        asyncio.create_task(_moment_loop(session_factory, "m_001", on_moment)),
    ]

    if "youtube" in sources:
        from .youtube_connector import YoutubeConnector
        video_id = os.environ.get("YOUTUBE_VIDEO_ID")
        if not video_id:
            logger.error("SOURCES includes youtube but YOUTUBE_VIDEO_ID is not set — skipping connector.")
        else:
            yt_conn = YoutubeConnector(video_id=video_id, match_id="m_001")
            tasks.append(asyncio.create_task(_poll_youtube(yt_conn, queue)))

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
