"""Gemini copy layer (spec §7.2). The LLM writes WORDS ONLY — strategy and all
numbers come from the deterministic engine. Guardrails per contract §G.3:
debounce >= GEMINI_DEBOUNCE_SECONDS between real calls, cache by
(match, archetype, industry, segment), and on ANY failure fall back to the
playbook template with llm_fallback=True — never an unresolved error."""
import json
import os
import time
import logging

from ..contracts import CampaignBrief, Copy, CopyVariant, ContentIdeaDetail, GEMINI_DEBOUNCE_SECONDS
from .strategy.playbook import PLAYBOOK

logger = logging.getLogger(__name__)

_client = None
_last_call_ts = 0.0
_cache: dict[tuple, dict] = {}

# Model is env-configurable so it can be swapped (e.g. for rate limits) without
# a code change. Default: Gemini 3.1 Flash-Lite (high free-tier limits, cheap).
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


def _get_client():
    global _client
    if _client is None:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        _client = genai.Client(api_key=api_key) if api_key else genai.Client()
    return _client


def _call_gemini(prompt: str, response_schema: dict) -> dict:
    """One debounced, schema-constrained Gemini call. Raises on any problem."""
    global _last_call_ts
    now = time.monotonic()
    if now - _last_call_ts < GEMINI_DEBOUNCE_SECONDS:
        raise RuntimeError(f"debounced (last call {now - _last_call_ts:.1f}s ago)")
    _last_call_ts = now

    from google.genai import types
    response = _get_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.7,
        ),
    )
    return json.loads(response.text)


def _playbook_entry(emotion: str, industry: str) -> dict:
    return (PLAYBOOK.get((emotion, industry))
            or PLAYBOOK.get(("*", industry))
            or PLAYBOOK.get(("*", "*")))


def _fill(s, brief: CampaignBrief):
    if isinstance(s, str):
        return (s.replace("{window_minutes}", str(brief.window_minutes))
                 .replace("{match_hashtag}", "MatchDay")
                 .replace("{segment_favorite}", "favourites")
                 .replace("{trending_topic}",
                          brief.top_topics[0] if brief.top_topics else "the action"))
    return s


def _template_copy(brief: CampaignBrief) -> Copy:
    template = _playbook_entry(brief.emotion.value, brief.industry.value)["template"]
    if "headline" not in template and "hook" in template:
        # Content-creator playbook entries use the ContentIdea shape
        # (format/hook/concept) — map them onto the campaign Copy shape.
        fmt = template.get("format", "Short-form video")
        return Copy(
            headline=_fill(template.get("hook", ""), brief),
            body=_fill(template.get("concept", ""), brief),
            cta="Copy hook",
            hashtags=[_fill(h, brief) for h in template.get("hashtags", [])],
            variant_b=CopyVariant(
                headline=f"{fmt} — alternative cut",
                body=_fill(template.get("concept", ""), brief),
                cta="Copy hook",
            ),
        )
    vb = template.get("variant_b", {})
    return Copy(
        headline=_fill(template.get("headline", ""), brief),
        body=_fill(template.get("body", ""), brief),
        cta=_fill(template.get("cta", ""), brief),
        hashtags=[_fill(h, brief) for h in template.get("hashtags", [])],
        variant_b=CopyVariant(
            headline=_fill(vb.get("headline", ""), brief),
            body=_fill(vb.get("body", ""), brief),
            cta=_fill(vb.get("cta", ""), brief),
        ),
    )


_COPY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "headline": {"type": "STRING", "description": "Max 60 chars"},
        "body": {"type": "STRING", "description": "Max 140 chars"},
        "cta": {"type": "STRING", "description": "Max 25 chars"},
        "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Max 4 hashtags"},
        "variant_b": {
            "type": "OBJECT",
            "properties": {"headline": {"type": "STRING"}, "body": {"type": "STRING"},
                           "cta": {"type": "STRING"}},
            "required": ["headline", "body", "cta"],
        },
    },
    "required": ["headline", "body", "cta", "hashtags", "variant_b"],
}


def generate_copy(brief: CampaignBrief) -> tuple[Copy, bool]:
    """Returns (Copy, llm_fallback). Cache key per contract §G.3."""
    cache_key = ("campaign", brief.match_id, brief.archetype.value,
                 brief.industry.value, brief.target_segment.value)
    if cache_key in _cache:
        return Copy(**_cache[cache_key]), False

    moment_line = brief.moment.description if brief.moment else "pre-match baseline (no live moment)"
    prompt = f"""You are a senior performance-marketing copywriter. You write copy ONLY.
Never invent statistics; use only the context given. Output strict JSON per the schema.

CONTEXT (measured, do not alter):
- Moment: {moment_line}
- Industry: {brief.industry.value} | Channel: {brief.channel.value} | Offer window: {brief.window_minutes} minutes
- Audience segment: {brief.segment.display_name} ({brief.segment.size:,} fans; traits: {', '.join(brief.segment.defining_traits) or 'n/a'})
- Dominant fan emotion right now: {brief.emotion.value}
- Trending topics fans are talking about: {', '.join(brief.top_topics) or 'none yet'}

GUIDANCE: {brief.tone_notes}
TASK: write campaign copy for the "{brief.archetype.value}" archetype. Reference the actual
trending topic/moment where natural. Headline <= 60 chars, body <= 140 chars, CTA <= 25 chars,
<= 4 hashtags, plus one alternative variant_b."""

    try:
        data = _call_gemini(prompt, _COPY_SCHEMA)
        vb = data.get("variant_b", {})
        copy = Copy(
            headline=data.get("headline", ""), body=data.get("body", ""),
            cta=data.get("cta", ""), hashtags=data.get("hashtags", [])[:4],
            variant_b=CopyVariant(headline=vb.get("headline", ""),
                                  body=vb.get("body", ""), cta=vb.get("cta", "")),
        )
        _cache[cache_key] = copy.model_dump()
        return copy, False
    except Exception as e:
        logger.warning(f"Gemini fallback (campaign copy): {e}")
        return _template_copy(brief), True


_CONTENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "format": {"type": "STRING", "description": "e.g. 15s vertical reel"},
        "hook": {"type": "STRING", "description": "First-2-seconds hook"},
        "concept": {"type": "STRING", "description": "Max 280 chars"},
        "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
        "post_within_minutes": {"type": "INTEGER"},
    },
    "required": ["format", "hook", "concept", "hashtags", "post_within_minutes"],
}


def generate_content_idea(match_id: str, platform: str, creator_niche: str,
                          top_topics: list[str], dominant_emotion: str,
                          top_countries: list[str]) -> tuple[ContentIdeaDetail, bool]:
    """Creator flavour (spec §7.3). Returns (idea, llm_fallback)."""
    top_topic = top_topics[0] if top_topics else "the match"
    cache_key = ("content", match_id, platform, top_topic, dominant_emotion)
    if cache_key in _cache:
        return ContentIdeaDetail(**_cache[cache_key]), False

    prompt = f"""You are a short-form content strategist for sports creators. Output strict JSON.
Never invent statistics; use only the context given.

CONTEXT (measured):
- Platform: {platform} | Creator niche: {creator_niche}
- Dominant fan emotion right now: {dominant_emotion}
- Trending topics: {', '.join(top_topics) or 'none yet'}
- Peak audiences: {', '.join(top_countries) or 'unknown'}

TASK: one concrete, immediately-postable content idea riding the current moment.
Engagement windows decay ~20 minutes after a moment, so recommend fast posting."""

    try:
        data = _call_gemini(prompt, _CONTENT_SCHEMA)
        idea = ContentIdeaDetail(
            format=data["format"], hook=data["hook"], concept=data["concept"][:280],
            hashtags=data.get("hashtags", [])[:4],
            post_within_minutes=int(data.get("post_within_minutes", 20)),
        )
        _cache[cache_key] = idea.model_dump()
        return idea, False
    except Exception as e:
        logger.warning(f"Gemini fallback (content idea): {e}")
        return ContentIdeaDetail(
            format="15s vertical reel",
            hook=f"React in the first 2 seconds to {top_topic}",
            concept=(f"Instant {dominant_emotion} reaction to {top_topic}: raw first take, "
                     f"then a 5-second hot take. Post before the moment cools."),
            hashtags=[f"#{top_topic.replace(' ', '')}", "#FanReaction"],
            post_within_minutes=20,
        ), True
