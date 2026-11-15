import re
from dataclasses import dataclass

from app.ml.classifier import SupportCategoryClassifier
from app.ml.preprocess import correct_common_typos

_GREETING = re.compile(
    r"^(?:hi|hello|hey|hiya|howdy|yo|good morning|good afternoon|good evening|"
    r"greetings|anyone there)(?: there| support| support team|,? can you help)?[!.? ]*$",
    re.IGNORECASE,
)
_THANKS = re.compile(
    r"^(?:thanks?|thank you|thx|ty|cheers|appreciate it|goodbye|bye|see you)"
    r"(?: so much| very much| again)?[!.? ]*$",
    re.IGNORECASE,
)
_FRAUD = re.compile(
    r"\b(fraud|unauthori[sz]ed|suspicious|hacked|compromised|stolen|identity theft|"
    r"don['’]t recognize|do not recognize|unrecognized|without permission|account takeover|"
    r"unknown person|scammer|stole my credentials|identity may have been used|"
    r"messages i did not write|password was changed by an unknown)\b",
    re.IGNORECASE,
)
_THIRD_PARTY = re.compile(
    r"\b(instagram|facebook|tiktok|twitter|x\.com|snapchat|whatsapp|netflix|spotify|"
    r"youtube|google|apple id|microsoft|amazon prime)\b",
    re.IGNORECASE,
)
_OUT_OF_SCOPE = re.compile(
    r"\b(weather|forecast|capital of|president of|recipe|write me a poem|"
    r"tell me a joke|solve this equation|stock price|bitcoin price|football score|"
    r"won (?:the )?(?:match|game))\b",
    re.IGNORECASE,
)
_INTENT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Payment Issue",
        re.compile(
            r"\b(charged twice|double charged|billed twice|duplicate charge|payment (?:failed|declined|rejected)|"
            r"card (?:was )?declined|charged two times|marked unpaid|payment status.*unpaid)\b",
            re.I,
        ),
    ),
    (
        "Refund",
        re.compile(
            r"\b(refunds?|money back|money returned|return my purchase|return(?:ed)? (?:the )?item|"
            r"reverse this charge|order i returned|returned (?:the )?order)\b",
            re.I,
        ),
    ),
    (
        "Billing",
        re.compile(
            r"\b(billing|subscription|invoice|receipt|renewal|cancel my plan|monthly fee|"
            r"(?:switch|change|downgrade|upgrade) to a .*plan|payment details for my plan)\b",
            re.I,
        ),
    ),
    (
        "Account Access",
        re.compile(
            r"\b(password|pass word|passcode|sign in|log ?in|locked out|reset my credentials)\b",
            re.I,
        ),
    ),
    (
        "Account Management",
        re.compile(
            r"\b(delete|deactivate|close|remove)\b.*\b(my )?(account|profile)\b", re.I
        ),
    ),
    (
        "Account Management",
        re.compile(
            r"\b(change|update|edit|manage)\b.*\b(email|username|profile|personal details|privacy preferences)\b|"
            r"\b(unsubscribe from|stop) (?:promotional|marketing) emails\b|"
            r"\b(download|export).*\b(personal data|account data|data you have)\b",
            re.I,
        ),
    ),
    (
        "Order / Delivery",
        re.compile(
            r"\b(order|delivery|deliver|shipping|package|tracking number|parcel)\b",
            re.I,
        ),
    ),
    (
        "Technical Issue",
        re.compile(
            r"\b(crash|crashing|bug|error|not loading|keeps freezing|won't open|does not work)\b",
            re.I,
        ),
    ),
    (
        "General Inquiry",
        re.compile(
            r"\b(contact (?:a )?(?:real )?(?:support|care|agent)|support team|help center|"
            r"privacy policy|service terms|what kind of issues|support on weekends)\b",
            re.I,
        ),
    ),
)


@dataclass(frozen=True)
class IntentPrediction:
    category: str
    confidence: float
    alternatives: list[tuple[str, float]]


def explicit_intent(message: str) -> str | None:
    text = correct_common_typos(message.strip())
    if _FRAUD.search(text):
        return "Security / Fraud"
    if _THIRD_PARTY.search(text) or _OUT_OF_SCOPE.search(text):
        return "Out of Scope"
    if _GREETING.fullmatch(text):
        return "Greeting"
    if _THANKS.fullmatch(text):
        return "Thanks / Goodbye"
    for category, pattern in _INTENT_RULES:
        if pattern.search(text):
            return category
    return None


def predict_intent(
    message: str,
    classifier: SupportCategoryClassifier,
) -> IntentPrediction:
    explicit = explicit_intent(message)
    if explicit:
        alternatives = classifier.predict_top_k(message, top_k=3)
        if explicit in {
            "Greeting",
            "Thanks / Goodbye",
            "Out of Scope",
            "Security / Fraud",
        }:
            return IntentPrediction(
                explicit,
                1.0,
                [
                    (explicit, 1.0),
                    *[
                        (category, score)
                        for category, score in alternatives
                        if category != explicit
                    ][:2],
                ],
            )
        remaining = [
            (category, score)
            for category, score in alternatives
            if category != explicit
        ]
        return IntentPrediction(
            explicit,
            max(0.60, alternatives[0][1]),
            [(explicit, max(0.60, alternatives[0][1])), *remaining[:2]],
        )
    alternatives = classifier.predict_top_k(message, top_k=3)
    category, confidence = alternatives[0]
    return IntentPrediction(category, confidence, alternatives)
