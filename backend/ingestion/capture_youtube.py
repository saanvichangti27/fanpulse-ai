"""Capture the live chat of a YouTube stream — LIVE or ALREADY FINISHED — into
a Replay Engine file (data/replay/replay_<video_id>.json, schema per contract §E.3).

Uses the `chat-downloader` package: no API key, no quota, and (crucially) it can
read the CHAT REPLAY of a finished stream, which the official Data API cannot.

Usage (from the repo root):
    backend/venv/Scripts/python -m backend.ingestion.capture_youtube VIDEO_ID_OR_URL
        [--match-id m_001] [--max-messages 2000] [--max-seconds 7200] [--out FILE]

Then replay it through the real pipeline:
    POST /api/v1/replay/control
    {"action": "start", "match_id": "m_001", "file": "replay_<video_id>.json", "speed": 30}

The captured messages are REAL fan text; markers (goal/full_time beats) are NOT
auto-inserted — add them by hand at the right t_offsets if you want forced
moment tags, otherwise the volume/sentiment moment detector runs naturally.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone


def _video_id(arg: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/live/)([A-Za-z0-9_-]{11})", arg)
    return m.group(1) if m else arg


def capture(video: str, match_id: str, max_messages: int, max_seconds: float,
            out_path: str | None) -> str:
    from chat_downloader import ChatDownloader

    vid = _video_id(video)
    url = f"https://www.youtube.com/watch?v={vid}"
    print(f"Capturing chat for {url} ...")

    chat = ChatDownloader().get_chat(url)  # works for live AND finished streams

    items = []
    first_ts_us = None
    for message in chat:
        text = message.get("message")
        if not text or not str(text).strip():
            continue

        # Offset since stream start: replays give time_in_seconds; live chats
        # may not, so fall back to the delta from the first captured message.
        t = message.get("time_in_seconds")
        if t is None:
            ts = message.get("timestamp")  # microseconds since epoch
            if ts is None:
                continue
            if first_ts_us is None:
                first_ts_us = ts
            t = (ts - first_ts_us) / 1_000_000.0
        t = max(0.0, float(t))

        items.append({
            "t_offset": round(t, 2),
            "external_id": f"yt_{message.get('message_id', f'{vid}_{len(items)}')}",
            "source": "youtube",
            "author": (message.get("author") or {}).get("name"),
            "text": str(text),
            "country": None,
        })

        if len(items) % 200 == 0:
            print(f"  captured {len(items)} messages (t={t:.0f}s)")
        if len(items) >= max_messages or t >= max_seconds:
            break

    if not items:
        print("No chat messages captured — the video may have chat disabled or no replay.")
        sys.exit(1)

    items.sort(key=lambda i: i["t_offset"])

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_path = out_path or os.path.join(repo_root, "data", "replay", f"replay_{vid}.json")
    payload = {
        "meta": {
            "match_id": match_id,
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "description": f"Real YouTube live-chat capture of {url} ({len(items)} messages)",
            "video_id": vid,
        },
        "items": items,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print(f"Saved {len(items)} messages -> {out_path}")
    print(f'Replay it with: POST /api/v1/replay/control '
          f'{{"action":"start","match_id":"{match_id}","file":"{os.path.basename(out_path)}","speed":30}}')
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("video", help="YouTube video ID or URL (live or finished stream)")
    p.add_argument("--match-id", default="m_001")
    p.add_argument("--max-messages", type=int, default=2000)
    p.add_argument("--max-seconds", type=float, default=3 * 3600)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    capture(a.video, a.match_id, a.max_messages, a.max_seconds, a.out)
