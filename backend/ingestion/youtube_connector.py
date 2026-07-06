"""Live YouTube LIVE CHAT connector (official Data API v3).

Flow (quota-cheap, per Build Bible):
  1. videos.list (part=liveStreamingDetails) ONCE -> activeLiveChatId
  2. liveChatMessages.list repeatedly with nextPageToken; YouTube tells us how
     fast to poll via pollingIntervalMillis.

NOTE: the official API only serves chat while the stream IS live. For finished
streams (chat replay) use backend/ingestion/capture_youtube.py, which needs no
API key and writes a replay file for the Replay Engine.
"""
import asyncio
import os
import logging
from datetime import datetime, timezone

import requests

from ..contracts import RawMessageIn, Source

logger = logging.getLogger(__name__)

API_BASE = "https://www.googleapis.com/youtube/v3"


class YoutubeConnector:
    def __init__(self, video_id: str, match_id: str = "m_001"):
        self.video_id = video_id
        self.match_id = match_id
        self.api_key = os.environ.get("YOUTUBE_API_KEY")
        self.live_chat_id: str | None = None
        self.page_token: str | None = None
        self.seen_ids: set[str] = set()

    def _resolve_live_chat_id(self) -> str | None:
        """One videos.list call (1 quota unit) to find the active live chat."""
        resp = requests.get(f"{API_BASE}/videos", params={
            "part": "liveStreamingDetails",
            "id": self.video_id,
            "key": self.api_key,
        }, timeout=10)
        if resp.status_code != 200:
            logger.error(f"videos.list error {resp.status_code}: {resp.text[:200]}")
            return None
        items = resp.json().get("items", [])
        if not items:
            logger.error(f"Video {self.video_id} not found.")
            return None
        details = items[0].get("liveStreamingDetails", {})
        chat_id = details.get("activeLiveChatId")
        if not chat_id:
            logger.error(
                f"Video {self.video_id} has no ACTIVE live chat (not live right now). "
                "For a finished stream, capture its chat replay with: "
                "python -m backend.ingestion.capture_youtube <video_id>"
            )
        return chat_id

    async def poll_live_chat(self) -> tuple[list[RawMessageIn], float]:
        """Returns (new_messages, seconds_to_wait_before_next_poll)."""
        if not self.api_key:
            logger.error("YOUTUBE_API_KEY not set. Cannot poll YouTube.")
            return [], 60.0

        if self.live_chat_id is None:
            self.live_chat_id = await asyncio.to_thread(self._resolve_live_chat_id)
            if self.live_chat_id is None:
                return [], 60.0  # retry later; stream may go live

        params = {
            "liveChatId": self.live_chat_id,
            "part": "snippet,authorDetails",
            "maxResults": 200,
            "key": self.api_key,
        }
        if self.page_token:
            params["pageToken"] = self.page_token

        resp = await asyncio.to_thread(
            requests.get, f"{API_BASE}/liveChat/messages", params=params, timeout=10
        )
        if resp.status_code != 200:
            logger.error(f"liveChatMessages error {resp.status_code}: {resp.text[:200]}")
            if resp.status_code in (403, 404):  # chat ended or quota — re-resolve later
                self.live_chat_id = None
                self.page_token = None
            return [], 30.0

        data = resp.json()
        self.page_token = data.get("nextPageToken")
        wait_s = data.get("pollingIntervalMillis", 15000) / 1000.0

        new_messages = []
        for item in data.get("items", []):
            ext_id = item["id"]
            if ext_id in self.seen_ids:
                continue
            self.seen_ids.add(ext_id)

            snippet = item.get("snippet", {})
            text = snippet.get("displayMessage", "")
            if not text.strip():
                continue  # non-text events (member joins, etc.)

            published = snippet.get("publishedAt")
            try:
                created_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except Exception:
                created_at = datetime.now(timezone.utc)

            new_messages.append(RawMessageIn(
                external_id=f"yt_{ext_id}",
                match_id=self.match_id,
                source=Source.youtube,
                author=item.get("authorDetails", {}).get("displayName", "unknown"),
                text=text,
                country=None,  # YouTube does not expose commenter country
                created_at=created_at,
            ))
        return new_messages, wait_s
