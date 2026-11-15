import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_REPLACEMENTS = (
    (r"\blog in\b|\bsign in\b|\bsign into\b", "login"),
    (r"\bcancel membership\b|\bpremium\b|\bmembership\b", "subscription"),
    (r"\bcredit card\b|\bdebit card\b", "card"),
    (r"\bpackage\b", "order"),
    (r"\bsuspicious charge\b|\bunrecognized charge\b", "fraud charge"),
    (r"\bunauthorized transaction\b", "fraud transaction"),
    (r"\bunauthorized access\b|\bcompromised account\b|\bhacked account\b", "fraud account"),
)


def preprocess_text(text: str) -> str:
    normalized = (text or "").lower()
    normalized = normalized.replace("can't", "cannot").replace("won't", "will not")
    normalized = re.sub(r"https?://\S+|www\.\S+", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for pattern, replacement in _REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized)
    return " ".join(token for token in normalized.split() if token not in ENGLISH_STOP_WORDS)
