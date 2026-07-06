"""Capture the live chat of a YouTube stream — LIVE or ALREADY FINISHED — into
a Replay Engine file (data/replay/replay_<video_id>.json, schema per contract §E.3).

Backend: yt-dlp (actively maintained). It downloads the stream's live chat as a
JSONL sidecar file (works for finished streams' chat replay, which the official
Data API cannot fetch), which we then convert to our replay schema. No API key.

Usage (from the repo root):
    backend/venv/Scripts/python -m backend.ingestion.capture_youtube VIDEO_ID_OR_URL
        [--match-id m_001] [--max-messages 2000] [--max-seconds 7200] [--out FILE]

For a CURRENTLY-LIVE stream this keeps capturing until you press Ctrl+C (the
chat downloaded so far is kept and converted). For a FINISHED stream it runs to
completion (or until --max-messages/--max-seconds worth of chat is parsed).

Then replay it through the real pipeline:
    POST /api/v1/replay/control
    {"action": "start", "match_id": "m_001", "file": "replay_<video_id>.json", "speed": 30}

Captured messages are REAL fan text. Goal/full-time markers are NOT auto-inserted;
add {"t_offset": N, "marker": "goal"} items by hand for guaranteed moment tags,
otherwise the volume/sentiment moment detector runs naturally.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone


def _video_id(arg: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/live/)([A-Za-z0-9_-]{11})", arg)
    return m.group(1) if m else arg


def _runs_to_text(message: dict) -> str:
    """Flatten YouTube's message 'runs' (text pieces + emojis) into one string.
    Standard unicode emoji keep their character; channel emotes use :shortcut:."""
    parts = []
    for run in (message or {}).get("runs", []):
        if "text" in run:
            parts.append(run["text"])
        elif "emoji" in run:
            emoji = run["emoji"]
            emoji_id = emoji.get("emojiId", "")
            if emoji_id and len(emoji_id) <= 8:      # real unicode emoji
                parts.append(emoji_id)
            else:                                     # custom channel emote
                shortcuts = emoji.get("shortcuts") or []
                parts.append(shortcuts[0] if shortcuts else "")
    return "".join(parts).strip()


def _parse_chat_line(line: str):
    """One line of yt-dlp's .live_chat.json -> (offset_seconds|None, id, author, text)."""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None

    offset_ms = None
    if "replayChatItemAction" in obj:               # finished-stream chat replay
        offset_ms = obj["replayChatItemAction"].get("videoOffsetTimeMsec")
        actions = obj["replayChatItemAction"].get("actions", [])
    else:                                            # ongoing-live capture
        actions = obj.get("actions", [])

    for action in actions:
        item = action.get("addChatItemAction", {}).get("item", {})
        renderer = item.get("liveChatTextMessageRenderer") or item.get("liveChatPaidMessageRenderer")
        if not renderer:
            continue
        text = _runs_to_text(renderer.get("message"))
        if not text:
            continue
        author = (renderer.get("authorName") or {}).get("simpleText")
        msg_id = renderer.get("id", "")
        ts_usec = renderer.get("timestampUsec")
        return (
            float(offset_ms) / 1000.0 if offset_ms is not None else None,
            msg_id, author, text,
            int(ts_usec) if ts_usec else None,
        )
    return None


def _download_chat(url: str, workdir: str) -> str:
    """Run yt-dlp to fetch the live_chat JSONL; returns the file path."""
    import yt_dlp

    outtmpl = os.path.join(workdir, "capture")
    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "subtitleslangs": ["live_chat"],
        "outtmpl": {"default": outtmpl},
        "quiet": True,
        "noprogress": True,
        "no_warnings": True,
    }
    print("Downloading chat (yt-dlp fetches the full chat replay first, then we trim)...")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except KeyboardInterrupt:
        print("\nCapture interrupted — converting what was downloaded so far...")
    except Exception as e:
        # A partial live_chat file may still exist (e.g. live stream interrupted)
        print(f"yt-dlp finished with: {e}")

    for name in os.listdir(workdir):
        if name.endswith(".live_chat.json"):
            return os.path.join(workdir, name)
    raise SystemExit(
        "No live chat found. Either this video never had a live chat, the chat "
        "replay is disabled, or the video ID is wrong."
    )


def capture(video: str, match_id: str, max_messages: int, max_seconds: float,
            out_path: str | None) -> str:
    vid = _video_id(video)
    url = f"https://www.youtube.com/watch?v={vid}"
    print(f"Capturing chat for {url} ...")

    items, seen = [], set()
    with tempfile.TemporaryDirectory() as workdir:
        chat_file = _download_chat(url, workdir)
        first_ts_usec = None
        with open(chat_file, encoding="utf-8") as f:
            for line in f:
                parsed = _parse_chat_line(line)
                if not parsed:
                    continue
                offset_s, msg_id, author, text, ts_usec = parsed

                if offset_s is None:                 # live capture: offset from first msg
                    if ts_usec is None:
                        continue
                    if first_ts_usec is None:
                        first_ts_usec = ts_usec
                    offset_s = (ts_usec - first_ts_usec) / 1_000_000.0
                if offset_s < 0:                     # pre-stream chat -> t=0
                    offset_s = 0.0
                if offset_s > max_seconds:
                    break
                if msg_id in seen:
                    continue
                seen.add(msg_id)

                items.append({
                    "t_offset": round(offset_s, 2),
                    "external_id": f"yt_{msg_id or f'{vid}_{len(items)}'}",
                    "source": "youtube",
                    "author": author,
                    "text": text,
                    "country": None,   # inferred at ingestion (flag emoji / language)
                })
                if len(items) % 500 == 0:
                    print(f"  parsed {len(items)} messages (t={offset_s:.0f}s)")
                if len(items) >= max_messages:
                    break

    if not items:
        raise SystemExit("Chat file downloaded but contained no text messages.")

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

    span = items[-1]["t_offset"] - items[0]["t_offset"]
    print(f"Saved {len(items)} real messages spanning {span/60:.1f} min -> {out_path}")
    print(f'Replay it with: POST /api/v1/replay/control '
          f'{{"action":"start","match_id":"{match_id}","file":"{os.path.basename(out_path)}","speed":30}}')
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Capture YouTube live chat (live or finished) into a replay file")
    p.add_argument("video", help="YouTube video ID or URL (live or finished stream)")
    p.add_argument("--match-id", default="m_001")
    p.add_argument("--max-messages", type=int, default=2000)
    p.add_argument("--max-seconds", type=float, default=3 * 3600)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    capture(a.video, a.match_id, a.max_messages, a.max_seconds, a.out)
