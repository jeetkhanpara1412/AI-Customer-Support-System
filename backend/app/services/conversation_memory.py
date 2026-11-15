import re
from dataclasses import dataclass

from app.db.models import Message
from app.ml.intents import explicit_intent

_SHORT_FOLLOW_UP = re.compile(
    r"^(?:yes|yeah|yep|no|nope|that one|the first one|first|the second one|second|"
    r"please|that|it|what about .+|and .+)[!.? ]*$",
    re.IGNORECASE,
)
_FIRST_OPTION = re.compile(r"^(?:yes|yeah|yep|that one|the first one|first|1)[!.? ]*$", re.I)
_SECOND_OPTION = re.compile(r"^(?:the second one|second|2)[!.? ]*$", re.I)


@dataclass(frozen=True)
class FollowUp:
    query: str
    selected_category: str | None = None
    needs_clarification: bool = False


def resolve_follow_up(
    message: str,
    history: list[Message],
    current_topic: str | None = None,
    pending_clarification: list[str] | None = None,
) -> FollowUp:
    text = message.strip()
    latest_user_message = next(
        (item.body for item in reversed(history) if item.sender == "user"),
        "",
    )
    explicit = explicit_intent(text)

    if pending_clarification:
        selected = next(
            (category for category in pending_clarification if category.casefold() in text.casefold()),
            None,
        )
        if selected is None and _FIRST_OPTION.fullmatch(text):
            selected = pending_clarification[0]
        elif selected is None and _SECOND_OPTION.fullmatch(text) and len(pending_clarification) > 1:
            selected = pending_clarification[1]
        if selected is not None:
            context = latest_user_message or current_topic or ""
            return FollowUp(f"{context}. {text}".strip(". "), selected_category=selected)
        if explicit is None or _SHORT_FOLLOW_UP.fullmatch(text):
            context = latest_user_message or current_topic or ""
            return FollowUp(
                f"{context}. {text}".strip(". "),
                needs_clarification=True,
            )

    if explicit in {"Greeting", "Thanks / Goodbye", "Out of Scope", "Security / Fraud"}:
        return FollowUp(text, selected_category=explicit)
    if explicit:
        context = latest_user_message or current_topic or ""
        query = f"{context}. {text}" if context else text
        return FollowUp(query, selected_category=explicit)
    if _SHORT_FOLLOW_UP.fullmatch(text):
        context = latest_user_message or current_topic or ""
        if context:
            return FollowUp(f"{context}. {text}")
    return FollowUp(text)
