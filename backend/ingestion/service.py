import asyncio
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Callable, Awaitable

from sqlalchemy import text

from ..contracts import (
    MomentEvent, 
    MOMENT_VOLUME_RATIO, 
    MOMENT_SENTIMENT_DELTA_PP, 
    MOMENT_COOLDOWN_SECONDS
)
from .nlp import classify_batch
from .analytics import get_momentum
from .geo import get_country_from_source

logger = logging.getLogger(__name__)

# To hold forced markers from replay
_forced_markers = {}

async def _poll_youtube(connector, match_id: str, queue: asyncio.Queue):
    """Poll YouTube comments every 20s and queue RawMessageIn items."""
    while True:
        try:
            messages = await connector.poll_comments()
            if messages:
                logger.info(f"Polled {len(messages)} new messages from YouTube")
                for msg in messages:
                    await queue.put(msg)
        except Exception as e:
            logger.error(f"YouTube poll error: {e}")
        await asyncio.sleep(20)

async def _process_queue(session_factory, queue: asyncio.Queue):
    batch = []
    while True:
        try:
            item = await asyncio.wait_for(queue.get(), timeout=1.0)
            
            # Handle replay markers
            if isinstance(item, dict) and "marker" in item:
                _forced_markers["next"] = item["marker"]
                continue
                
            # It's a raw message (either dict from replay or RawMessageIn from reddit)
            if isinstance(item, dict):
                # Map replay dict to something nlp can process
                text_content = item.get("text", "")
                external_id = item.get("external_id", "")
                author = item.get("author")
                country = get_country_from_source(
                    source=item.get("source", "replay"), 
                    external_id=external_id, 
                    author=author, 
                    raw_country=item.get("country")
                )
                
                batch.append({
                    "external_id": external_id,
                    "match_id": item.get("match_id", "m_001"), # Fallback if not injected
                    "source": item.get("source", "replay"),
                    "author": author,
                    "text": text_content,
                    "country": country,
                    "created_at": datetime.now(timezone.utc).isoformat() # We use real time for processing
                })
            else:
                # RawMessageIn object
                batch.append({
                    "external_id": item.external_id,
                    "match_id": item.match_id,
                    "source": item.source,
                    "author": item.author,
                    "text": item.text,
                    "country": item.country,
                    "created_at": item.created_at.isoformat()
                })
                
        except asyncio.TimeoutError:
            pass # Process batch if we have one
            
        if batch:
            try:
                texts = [b["text"] for b in batch]
                # Run NLP in thread to avoid blocking asyncio loop
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
                            "external_id": b["external_id"],
                            "match_id": b["match_id"],
                            "source": b["source"],
                            "author": b["author"],
                            "text": b["text"],
                            "country": b["country"],
                            "sentiment": res["sentiment"],
                            "sentiment_score": res["sentiment_score"],
                            "emotion": res["emotion"],
                            "emotion_score": res["emotion_score"],
                            "topics_json": json.dumps(res["topics"]),
                            "created_at": b["created_at"].replace("+00:00", "Z")
                        })
                    session.commit()
            except Exception as e:
                logger.error(f"Error processing message batch: {e}")
            finally:
                batch.clear()

async def _moment_loop(session_factory, match_id: str, on_moment: Callable[[MomentEvent], Awaitable[None]]):
    last_moment_time = 0
    
    while True:
        await asyncio.sleep(10)
        
        try:
            with session_factory() as session:
                momentum = get_momentum(session, match_id)
                if not momentum:
                    continue
                    
                # Check moment rule
                is_moment = (
                    momentum["volume_ratio"] >= MOMENT_VOLUME_RATIO and 
                    abs(momentum["sentiment_delta_pp"]) >= MOMENT_SENTIMENT_DELTA_PP
                )
                
                forced_marker = _forced_markers.pop("next", None)
                if forced_marker:
                    is_moment = True
                    
                now = asyncio.get_event_loop().time()
                if is_moment and (now - last_moment_time) >= MOMENT_COOLDOWN_SECONDS:
                    last_moment_time = now
                    
                    # Determine tag
                    tag = "surge_other"
                    if forced_marker:
                        tag = forced_marker
                    elif momentum["dominant_emotion"] == "joy" and momentum["sentiment_delta_pp"] > 0:
                        tag = "goal"
                    elif momentum["dominant_emotion"] in ["anger", "disgust"]:
                        topics_set = set(momentum["top_topics"])
                        if topics_set.intersection({"var", "referee", "penalty", "red card"}):
                            # Default to var_controversy for anger + ref topics
                            tag = "var_controversy" 

                    moment_id = f"mo_{uuid.uuid4().hex[:8]}"
                    detected_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    desc = f"Volume spike {momentum['volume_ratio']}x baseline with {momentum['dominant_emotion']} surge ({momentum['sentiment_delta_pp']:+.1f}pp)"
                    
                    # Insert moment
                    sql = text("""
                        INSERT INTO moments (id, match_id, event_tag, detected_at, momentum_json, description)
                        VALUES (:id, :match_id, :event_tag, :detected_at, :momentum_json, :description)
                    """)
                    session.execute(sql, {
                        "id": moment_id,
                        "match_id": match_id,
                        "event_tag": tag,
                        "detected_at": detected_at,
                        "momentum_json": json.dumps(momentum),
                        "description": desc
                    })
                    session.commit()
                    
                    # Fire callback
                    event_dict = {
                        "moment_id": moment_id,
                        "match_id": match_id,
                        "event_tag": tag,
                        "detected_at": detected_at,
                        "momentum": momentum,
                        "description": desc
                    }
                    
                    # Using dict matching MomentEvent so W2 can parse it
                    try:
                        # Convert dict to Pydantic if needed
                        event = MomentEvent(**event_dict)
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

async def run_ingestion(session_factory, sources: list[str], on_moment: Callable[[MomentEvent], Awaitable[None]]) -> None:
    queue = asyncio.Queue()
    tasks = []
    
    # Start queue processor
    tasks.append(asyncio.create_task(_process_queue(session_factory, queue)))
    
    # Start moment loop for a default match_id for now (m_001) - in real life this loops active matches
    tasks.append(asyncio.create_task(_moment_loop(session_factory, "m_001", on_moment)))
    
    if "youtube" in sources:
        from ..ingestion.youtube_connector import YoutubeConnector
        video_id = os.environ.get("YOUTUBE_VIDEO_ID", "dQw4w9WgXcQ") # Default video for testing
        yt_conn = YoutubeConnector(video_id=video_id)
        tasks.append(asyncio.create_task(_poll_youtube(yt_conn, "m_001", queue)))
        
    # Replay is managed externally by ReplayController feeding into the queue?
    # Actually ReplayController needs access to the same queue.
    # We can expose the queue globally or pass it to ReplayController.
    global INGESTION_QUEUE
    INGESTION_QUEUE = queue
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
