from datetime import UTC, datetime, time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_admin
from app.db.models import (
    Conversation,
    KnowledgeEntry,
    Message,
    Ticket,
    TicketReply,
    User,
)
from app.db.session import get_db
from app.schemas.api import (
    KnowledgeEntryCreate,
    TicketRead,
    TicketStatusUpdate,
)
from app.schemas.api import (
    TicketReply as TicketReplyRequest,
)
from app.services.chat_service import rebuild_knowledge_base
from app.services.ws_manager import manager

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/tickets", response_model=list[TicketRead])
def list_tickets(
    status: Literal["open", "in_progress", "resolved"] | None = None,
    category: str | None = None,
    priority: Literal["low", "medium", "high"] | None = None,
    page: int = Query(default=1, ge=1),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = (
        select(Ticket)
        .options(selectinload(Ticket.replies))
        .order_by(Ticket.created_at.desc())
    )
    if status:
        query = query.where(Ticket.status == status)
    if category:
        query = query.where(Ticket.category == category)
    if priority:
        query = query.where(Ticket.priority == priority)
    return db.scalars(query.offset((page - 1) * 25).limit(25)).all()


@router.patch("/tickets/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: int, payload: TicketStatusUpdate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.id == ticket_id)
        .options(selectinload(Ticket.replies))
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = payload.status
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/tickets/{ticket_id}/reply")
async def reply_ticket(ticket_id: int, payload: TicketReplyRequest, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id).options(selectinload(Ticket.conversation))
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    message = Message(conversation_id=ticket.conversation_id, sender="admin", body=payload.text)
    ticket_reply = TicketReply(ticket_id=ticket.id, admin_id=user.id, text=payload.text)
    db.add_all([message, ticket_reply])
    db.commit()
    db.refresh(message)
    await manager.send_to_user(
        ticket.user_id,
        {"type": "agent_message", "ticket_id": ticket.id, "text": payload.text},
    )
    return {"id": message.id, "text": message.body, "role": "agent", "admin_id": user.id}


@router.get("/stats")
def stats(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    now = datetime.now(UTC)
    start_of_day = datetime.combine(now.date(), time.min, tzinfo=UTC)
    open_tickets = db.scalar(select(func.count(Ticket.id)).where(Ticket.status == "open")) or 0
    resolved_today = db.scalar(
        select(func.count(Ticket.id)).where(
            Ticket.status == "resolved", Ticket.updated_at >= start_of_day
        )
    ) or 0
    ticket_count = db.scalar(select(func.count(Ticket.id))) or 0
    confidence = db.scalar(select(func.avg(Message.confidence)).where(Message.sender == "assistant"))
    categories = db.execute(select(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category)).all()
    conversation_count = db.scalar(select(func.count(Conversation.id))) or 0
    return {
        "open_tickets": open_tickets,
        "resolved_today": resolved_today,
        "escalation_rate": ticket_count / max(conversation_count, 1),
        "avg_confidence": float(confidence or 0),
        "by_category": [{"category": category, "count": count} for category, count in categories],
    }


@router.get("/knowledge")
def list_knowledge(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.scalars(select(KnowledgeEntry).order_by(KnowledgeEntry.id)).all()


@router.post("/knowledge", status_code=201)
def create_knowledge(payload: KnowledgeEntryCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    entry = KnowledgeEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/knowledge/{entry_id}")
def update_knowledge(entry_id: int, payload: KnowledgeEntryCreate, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    entry = db.get(KnowledgeEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    for key, value in payload.model_dump().items():
        setattr(entry, key, value)
    db.commit()
    return entry


@router.delete("/knowledge/{entry_id}", status_code=204)
def delete_knowledge(entry_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    entry = db.get(KnowledgeEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    db.delete(entry)
    db.commit()


@router.post("/retrain")
def retrain_model(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        accuracy, samples = rebuild_knowledge_base(db)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"accuracy": accuracy, "samples": samples}


@router.get("/users")
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.created_at.desc()).limit(100)).all()
    return [{"id": user.id, "name": user.full_name, "email": user.email, "role": user.role} for user in users]
