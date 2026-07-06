"""Country inference for fan messages.

HONESTY NOTE: YouTube does NOT expose a commenter's location — true geography
is unavailable, so we INFER it from real signals in the message itself and
return None when there is no signal (the heatmap only shows what we can
actually support). Priority:

  1. explicit country provided upstream (replay fixture files);
  2. a flag emoji in the message or author name (🇧🇷 → BR) — fans post these
     constantly during matches and it is a direct, real signal;
  3. message language, only for messages >= 20 chars detected with >= 90%
     confidence, mapped to the language's primary football nation
     (pt→BR, es→ES, de→DE, ...). English is deliberately NOT mapped — it is
     too ambiguous. This is a documented heuristic, not a fact claim.
"""
import re

from langdetect import detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 42  # deterministic language detection

_FLAG_RE = re.compile("[\U0001F1E6-\U0001F1FF]{2}")

_LANG_TO_COUNTRY = {
    "pt": "BR", "es": "ES", "de": "DE", "fr": "FR", "it": "IT",
    "ja": "JP", "ko": "KR", "ar": "SA", "hi": "IN", "tr": "TR",
    "nl": "NL", "pl": "PL", "ru": "RU", "id": "ID", "th": "TH", "vi": "VN",
}


def _flag_to_iso(flag: str) -> str:
    return "".join(chr(ord(c) - 0x1F1E6 + ord("A")) for c in flag)


def infer_country(text: str | None, author: str | None = None,
                  raw_country: str | None = None) -> str | None:
    if raw_country:
        return raw_country

    for source in (text or "", author or ""):
        m = _FLAG_RE.search(source)
        if m:
            return _flag_to_iso(m.group(0))

    t = (text or "").strip()
    if len(t) >= 20:
        try:
            langs = detect_langs(t)
            if langs and langs[0].prob >= 0.90:
                return _LANG_TO_COUNTRY.get(langs[0].lang)
        except LangDetectException:
            pass
    return None
