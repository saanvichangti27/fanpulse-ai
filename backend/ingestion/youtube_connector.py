import asyncio
import os
import requests
import logging
from datetime import datetime, timezone
from ..contracts import RawMessageIn, Source

logger = logging.getLogger(__name__)

class YoutubeConnector:
    def __init__(self, video_id: str):
        self.video_id = video_id
        self.api_key = os.environ.get("YOUTUBE_API_KEY")
        self.seen_ids = set()
        
    async def poll_comments(self) -> list[RawMessageIn]:
        if not self.api_key:
            logger.error("YOUTUBE_API_KEY not set. Cannot poll YouTube.")
            return []
            
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": self.video_id,
            "key": self.api_key,
            "maxResults": 100,
            "order": "time"
        }
        
        try:
            # Running synchronous request in a thread
            resp = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"YouTube API error {resp.status_code}: {resp.text}")
                return []
                
            data = resp.json()
            items = data.get("items", [])
            
            new_messages = []
            for item in items:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                ext_id = item["id"]
                
                if ext_id in self.seen_ids:
                    continue
                self.seen_ids.add(ext_id)
                
                text = comment.get("textOriginal", "")
                author = comment.get("authorDisplayName", "unknown")
                published_at_str = comment.get("publishedAt")
                
                try:
                    # Parse ISO string
                    created_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                except Exception:
                    created_at = datetime.now(timezone.utc)
                
                msg = RawMessageIn(
                    external_id=f"yt_{ext_id}",
                    match_id="m_001",
                    source=Source.youtube,
                    author=author,
                    text=text,
                    country=None,  # YouTube API doesn't provide country on comments
                    created_at=created_at
                )
                new_messages.append(msg)
                
            return new_messages
            
        except Exception as e:
            logger.error(f"YouTube connector error: {e}")
            return []
