import csv
import hashlib
import json
import re
import threading
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import logger
from app.db.models import Conversation, KnowledgeEntry, Message, User
from app.ml.classifier import ARTIFACT_PATH, SupportCategoryClassifier
from app.ml.decision import DecisionEngine
from app.ml.responder import ResponseGenerator
from app.ml.retriever import TicketRetriever
from app.ml.train import DATA_PATH, train_pipeline
from app.services.ticket_service import create_escalation_ticket
from redis import Redis

_lock = threading.RLock()
_classifier: SupportCategoryClassifier | None = None
_retriever: TicketRetriever | None = None
_cache = Redis.from_url(get_settings().redis_url, socket_connect_timeout=1, socket_timeout=1)
_security_pattern = re.compile(
    r"\b(fraud|unauthori[sz]ed|suspicious|hacked|compromised|stolen|identity theft|"
    r"don't recognize|do not recognize|unrecognized|without permission|account takeover)\b",
    re.IGNORECASE,
)


def initialize_ml() -> None:
    global _classifier, _retriever
    with _lock:
        if not ARTIFACT_PATH.exists():
            train_pipeline()
        _classifier = SupportCategoryClassifier()
        _retriever = TicketRetriever(DATA_PATH)


def process_chat(db: Session, user: User, text: str, conversation_id: int | None = None) -> dict:
    global _classifier, _retriever
    if _classifier is None or _retriever is None:
        initialize_ml()
    with _lock:
        classifier, retriever = _classifier, _retriever
    if classifier is None or retriever is None:
        raise RuntimeError("The support model is not initialized")
    clean_text = text[:1000]
    prepared = classifier.preprocess(clean_text)
    category, confidence = classifier.predict(clean_text, prepared)
    if _security_pattern.search(clean_text):
        category = "Security / Fraud"
    cached: dict | None = None
    cache_key = None
    if category != "Security / Fraud":
        cache_key = "support-answer:" + hashlib.sha256(prepared.encode()).hexdigest()
        try:
            serialized = _cache.get(cache_key)
            cached = json.loads(serialized) if serialized else None
        except Exception as exc:
            logger.bind(exception=type(exc).__name__).warning("Support response cache unavailable")
    if cached:
        category = str(cached["category"])
        confidence = float(cached["confidence"])
        similarity = float(cached["similarity"])
        mode = str(cached["mode"])
        reply = str(cached["reply"])
    else:
        _, similarity, matched_response = retriever.retrieve(clean_text, category, prepared)
        settings = get_settings()
        mode = DecisionEngine(settings.confidence_threshold, settings.similarity_threshold).decide(
            confidence, similarity, category
        )
        reply = ResponseGenerator().generate_response(category, matched_response, mode)
        if cache_key and category != "Security / Fraud":
            try:
                _cache.setex(
                    cache_key,
                    300,
                    json.dumps(
                        {
                            "category": category,
                            "confidence": confidence,
                            "similarity": similarity,
                            "mode": mode,
                            "reply": reply,
                        }
                    ),
                )
            except Exception as exc:
                logger.bind(exception=type(exc).__name__).warning("Support response cache unavailable")
    escalated = mode == "fallback"

    if conversation_id is None:
        conversation = Conversation(user_id=user.id, title=clean_text[:160])
        db.add(conversation)
        db.flush()
    else:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.user_id == user.id
            )
        )
        if conversation is None:
            raise LookupError("Conversation not found")
    conversation.updated_at = datetime.now(timezone.utc)
    user_message = Message(conversation_id=conversation.id, sender="user", body=clean_text)
    assistant_message = Message(
        conversation_id=conversation.id,
        sender="assistant",
        body=reply,
        category=category,
        confidence=confidence,
        escalated=escalated,
    )
    db.add_all([user_message, assistant_message])
    ticket = None
    if escalated and conversation.ticket is None:
        ticket = create_escalation_ticket(db, user, conversation, category, clean_text)
    db.commit()
    if ticket is not None:
        db.refresh(ticket)
    return {
        "conversation_id": conversation.id,
        "message_id": assistant_message.id,
        "category": category,
        "confidence": confidence,
        "similarity": similarity,
        "reply": reply,
        "mode": mode,
        "escalated": escalated,
        "ticket_id": ticket.id if ticket else (conversation.ticket.id if conversation.ticket else None),
    }


def rebuild_knowledge_base(db: Session) -> tuple[float, int]:
    entries = db.scalars(select(KnowledgeEntry).where(KnowledgeEntry.enabled.is_(True))).all()
    if not entries:
        raise ValueError("Knowledge base cannot be empty")
    temporary_path = DATA_PATH.with_suffix(".tmp")
    temporary_path.parent.mkdir(parents=True, exist_ok=True)
    with temporary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Customer Message", "Category", "Company Response"])
        writer.writeheader()
        writer.writerows(
            {
                "Customer Message": entry.message,
                "Category": entry.category,
                "Company Response": entry.response,
            }
            for entry in entries
        )
    artifact, accuracy, sample_count = train_pipeline(temporary_path, return_metrics=True)
    new_classifier = SupportCategoryClassifier(artifact)
    new_retriever = TicketRetriever(temporary_path)
    temporary_path.replace(DATA_PATH)
    new_retriever.knowledge_base_path = DATA_PATH
    global _classifier, _retriever
    with _lock:
        _classifier = new_classifier
        _retriever = new_retriever
    return accuracy, sample_count
