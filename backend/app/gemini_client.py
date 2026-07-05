import json
from google import genai
from google.genai import types
from ..contracts import CampaignBrief, Copy, CopyVariant
from .strategy.playbook import PLAYBOOK

def generate_copy(brief: CampaignBrief) -> tuple[Copy, bool]:
    """Returns (Copy, llm_fallback)"""
    
    playbook_entry = PLAYBOOK.get((brief.emotion.value, brief.industry.value))
    if not playbook_entry:
        playbook_entry = PLAYBOOK.get(("*", brief.industry.value), PLAYBOOK.get(("*", "*")))
    
    template = playbook_entry["template"]
    
    prompt = f"""
    You are a senior performance-marketing copywriter.
    Generate a short, high-conversion marketing copy based on the following context.
    Use ONLY the numbers provided; never invent statistics.
    Output strictly in JSON matching the schema.
    
    Context:
    Industry: {brief.industry.value}
    Emotion: {brief.emotion.value}
    Segment: {brief.segment.display_name} (Traits: {', '.join(brief.segment.defining_traits)})
    Channel: {brief.channel.value}
    Window: {brief.window_minutes} minutes
    Trending Topics: {', '.join(brief.top_topics)}
    Tone Notes: {brief.tone_notes}
    """
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "headline": {"type": "STRING", "description": "Max 60 chars"},
            "body": {"type": "STRING", "description": "Max 140 chars"},
            "cta": {"type": "STRING", "description": "Max 25 chars"},
            "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Max 4 hashtags"},
            "variant_b": {
                "type": "OBJECT",
                "properties": {
                    "headline": {"type": "STRING"},
                    "body": {"type": "STRING"},
                    "cta": {"type": "STRING"}
                },
                "required": ["headline", "body", "cta"]
            }
        },
        "required": ["headline", "body", "cta", "hashtags", "variant_b"]
    }
    
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.7,
            ),
        )
        data = json.loads(response.text)
        variant = data.get("variant_b", {})
        copy = Copy(
            headline=data.get("headline", ""),
            body=data.get("body", ""),
            cta=data.get("cta", ""),
            hashtags=data.get("hashtags", []),
            variant_b=CopyVariant(
                headline=variant.get("headline", ""),
                body=variant.get("body", ""),
                cta=variant.get("cta", "")
            )
        )
        return copy, False
    except Exception as e:
        print(f"Gemini fallback triggered due to error: {e}")
        # Fallback to template logic
        def fill(s):
            if isinstance(s, str):
                return s.replace("{window_minutes}", str(brief.window_minutes))\
                        .replace("{match_hashtag}", "MatchDay")\
                        .replace("{segment_favorite}", "items")\
                        .replace("{trending_topic}", brief.top_topics[0] if brief.top_topics else "the action")
            return s
            
        return Copy(
            headline=fill(template.get("headline", "")),
            body=fill(template.get("body", "")),
            cta=fill(template.get("cta", "")),
            hashtags=template.get("hashtags", []),
            variant_b=CopyVariant(
                headline=fill(template.get("variant_b", {}).get("headline", "")),
                body=fill(template.get("variant_b", {}).get("body", "")),
                cta=fill(template.get("variant_b", {}).get("cta", ""))
            )
        ), True
