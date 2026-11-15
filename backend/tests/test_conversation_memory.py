from app.db.models import Message
from app.services.conversation_memory import resolve_follow_up


def test_short_confirmation_uses_the_previous_user_turn():
    history = [
        Message(sender="user", body="I need to change my password"),
        Message(sender="assistant", body="Use the account security settings."),
    ]

    follow_up = resolve_follow_up("yes", history)

    assert follow_up.query == "I need to change my password. yes"
    assert follow_up.selected_category is None
    assert not follow_up.needs_clarification


def test_follow_up_can_switch_to_a_new_explicit_topic():
    history = [Message(sender="user", body="I was charged twice")]

    follow_up = resolve_follow_up("what about refunds?", history, current_topic="Payment Issue")

    assert "I was charged twice" in follow_up.query
    assert follow_up.selected_category == "Refund"


def test_pending_clarification_options_resolve_by_label_or_choice():
    history = [Message(sender="user", body="Something is wrong with my account")]
    options = ["Account Access", "Billing"]

    selected = resolve_follow_up("Billing", history, pending_clarification=options)
    first = resolve_follow_up("yes", history, pending_clarification=options)
    unclear = resolve_follow_up("maybe", history, pending_clarification=options)

    assert selected.selected_category == "Billing"
    assert first.selected_category == "Account Access"
    assert unclear.needs_clarification
