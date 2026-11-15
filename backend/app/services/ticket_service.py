from sqlalchemy.orm import Session

from app.db.models import Conversation, Ticket, User


def priority_for_category(category: str) -> str:
    if category == "Security / Fraud":
        return "high"
    if category in {"Billing", "Refund", "Payment Issue"}:
        return "medium"
    return "low"


def create_escalation_ticket(
    db: Session,
    user: User,
    conversation: Conversation,
    category: str,
    subject: str,
) -> Ticket:
    ticket = Ticket(
        user_id=user.id,
        conversation_id=conversation.id,
        subject=subject[:160],
        category=category,
        priority=priority_for_category(category),
    )
    db.add(ticket)
    return ticket
