from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Ticket, User
from app.db.session import get_db
from app.schemas.api import TicketRead

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketRead])
def list_my_tickets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Ticket)
        .where(Ticket.user_id == user.id)
        .options(selectinload(Ticket.replies))
        .order_by(Ticket.created_at.desc())
    ).all()


@router.get("/{ticket_id}", response_model=TicketRead)
def get_my_ticket(ticket_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.id == ticket_id, Ticket.user_id == user.id)
        .options(selectinload(Ticket.replies))
    )
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
