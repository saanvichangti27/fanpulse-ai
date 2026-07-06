import re
from typing import List, Dict, Any

import emoji as emoji_lib
from transformers import pipeline

from ..contracts import AROUSAL, Emotion, Sentiment

_ALPHA_RE = re.compile(r"[A-Za-z]")


def _prep_for_models(text: str) -> str:
    """Emoji handling (verified empirically):
    - messages WITH real words keep their raw emoji — the Twitter-trained
      models read inline emoji well ('GOOOAL 🔥🔥🔥' → positive 0.90);
    - (nearly) emoji-ONLY messages get demojized to words, which the models
      classify far better ('😭😭😭' → sadness instead of neutral).
    Only the model INPUT is transformed; the stored message stays raw."""
    if len(_ALPHA_RE.findall(text)) < 4:
        demojized = emoji_lib.demojize(text, delimiters=(" ", " ")).replace("_", " ").strip()
        if demojized:
            return demojized
    return text

# Watchlist for topics
WATCHLIST = {"var", "referee", "penalty", "red card", "goal", "messi", "ronaldo", "mbappe", "neymar"}
STOPWORDS = {"the", "is", "in", "and", "to", "a", "of", "for", "on", "with", "as", "at", "by", "this", "it", "that"}

# Lazy-loaded pipelines
_sentiment_pipe = None
_emotion_pipe = None

def get_sentiment_pipeline():
    global _sentiment_pipe
    if _sentiment_pipe is None:
        _sentiment_pipe = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", truncation=True, max_length=512)
    return _sentiment_pipe

def get_emotion_pipeline():
    global _emotion_pipe
    if _emotion_pipe is None:
        _emotion_pipe = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", truncation=True, max_length=512)
    return _emotion_pipe

def extract_topics(text: str) -> List[str]:
    text_lower = text.lower()
    found_topics = []

    # 0. Hashtags are first-class topics (tweet-style sources)
    for tag in re.findall(r"#([a-z0-9_]{3,})", text_lower):
        if tag not in found_topics:
            found_topics.append(tag)

    # 1. Watchlist matching
    for term in WATCHLIST:
        if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
            found_topics.append(term)
            
    # 2. Simple top tokens (non-stopwords, > 3 chars)
    words = re.findall(r'\b[a-z]{4,}\b', text_lower)
    word_counts = {}
    for w in words:
        if w not in STOPWORDS and w not in found_topics:
            word_counts[w] = word_counts.get(w, 0) + 1
            
    sorted_words = sorted(word_counts.keys(), key=lambda w: word_counts[w], reverse=True)
    
    found_topics.extend(sorted_words)
    return found_topics[:5]

def classify_batch(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Returns a list of dicts:
    {
      "sentiment": Sentiment,
      "sentiment_score": float,
      "emotion": Emotion,
      "emotion_score": float,
      "topics": list[str]
    }
    """
    if not texts:
        return []
        
    sent_pipe = get_sentiment_pipeline()
    emo_pipe = get_emotion_pipeline()

    model_texts = [_prep_for_models(t) if t.strip() else "..." for t in texts]
    sent_results = sent_pipe(model_texts, batch_size=16)
    emo_results = emo_pipe(model_texts, batch_size=16)
    
    results = []
    for i, text in enumerate(texts):
        # map sentiment
        s_res = sent_results[i]
        s_label = s_res["label"].lower()
        if "positive" in s_label:
            sentiment = "positive"
        elif "negative" in s_label:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        # map emotion
        e_res = emo_results[i]
        e_label = e_res["label"].lower() # j-hartmann outputs anger, disgust, fear, joy, neutral, sadness, surprise
        
        results.append({
            "sentiment": sentiment,
            "sentiment_score": s_res["score"],
            "emotion": e_label,
            "emotion_score": e_res["score"],
            "topics": extract_topics(text)
        })
        
    return results
