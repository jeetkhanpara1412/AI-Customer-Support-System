from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.rate_limit import limiter
from app.db.models import Conversation, User
from app.db.session import get_db
from app.schemas.api import (
    ChatRequest,
    ChatResponse,
    ConversationRead,
    ConversationSummary,
)
from app.services.chat_service import process_chat

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
def chat(request: Request, payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    del request
    try:
        return process_chat(db, user, payload.message, payload.conversation_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Conversation not found") from None


@router.get("/conversations", response_model=list[ConversationSummary])
def conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
    ).all()
    return [
        {"id": row.id, "title": row.title, "updated_at": row.updated_at}
        for row in rows
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def conversation_detail(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .options(selectinload(Conversation.messages))
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": row.id,
        "title": row.title,
        "updated_at": row.updated_at,
        "messages": [
            {
                "id": message.id,
                "role": "agent" if message.sender == "admin" else message.sender,
                "text": message.body,
                "category": message.category,
                "confidence": message.confidence,
                "escalated": message.escalated,
                "created_at": message.created_at,
            }
            for message in row.messages
        ],
    }
