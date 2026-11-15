import csv
import hashlib
import json
import threading
from datetime import UTC, datetime

from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import logger
from app.db.models import Conversation, KnowledgeEntry, Message, User
from app.ml.classifier import SupportCategoryClassifier
from app.ml.decision import DecisionEngine
from app.ml.intents import IntentPrediction, predict_intent
from app.ml.responder import ResponseGenerator
from app.ml.retriever import TicketRetriever
from app.ml.train import DATA_PATH, ensure_model, train_pipeline
from app.services.conversation_memory import resolve_follow_up
from app.services.ticket_service import create_escalation_ticket

_lock = threading.RLock()
_classifier: SupportCategoryClassifier | None = None
_retriever: TicketRetriever | None = None
_cache = Redis.from_url(
    get_settings().redis_url, socket_connect_timeout=1, socket_timeout=1
)


def initialize_ml(db: Session | None = None) -> None:
    global _classifier, _retriever
    with _lock:
        ensure_model()
        _classifier = SupportCategoryClassifier()
        if db is None:
            _retriever = TicketRetriever(DATA_PATH)
        else:
            entries = db.scalars(
                select(KnowledgeEntry)
                .where(KnowledgeEntry.enabled.is_(True))
                .order_by(KnowledgeEntry.id)
            ).all()
            _retriever = TicketRetriever(entries or [])


def process_chat(
    db: Session, user: User, text: str, conversation_id: int | None = None
) -> dict:
    global _classifier, _retriever
    if _classifier is None or _retriever is None:
        initialize_ml(db)
    with _lock:
        classifier, retriever = _classifier, _retriever
    if classifier is None or retriever is None:
        raise RuntimeError("The support model is not initialized")
    clean_text = text[:1000]
    if conversation_id is None:
        conversation = Conversation(user_id=user.id, title=clean_text[:160])
        db.add(conversation)
        db.flush()
        history: list[Message] = []
    else:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
            )
        )
        if conversation is None:
            raise LookupError("Conversation not found")
        history = list(
            reversed(
                db.scalars(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.desc(), Message.id.desc())
                    .limit(6)
                ).all()
            )
        )
    follow_up = resolve_follow_up(
        clean_text,
        history,
        current_topic=conversation.current_topic,
        pending_clarification=conversation.pending_clarification,
    )
    if follow_up.selected_category:
        alternatives = classifier.predict_top_k(follow_up.query, top_k=3)
        selected_score = next(
            (
                score
                for category, score in alternatives
                if category == follow_up.selected_category
            ),
            0.60,
        )
        confidence = (
            1.0
            if follow_up.selected_category
            in {"Greeting", "Thanks / Goodbye", "Out of Scope", "Security / Fraud"}
            else max(0.60, selected_score)
        )
        prediction = IntentPrediction(
            follow_up.selected_category,
            confidence,
            [
                (follow_up.selected_category, confidence),
                *[
                    (category, score)
                    for category, score in alternatives
                    if category != follow_up.selected_category
                ][:2],
            ],
        )
    else:
        prediction = predict_intent(follow_up.query, classifier)
    category = prediction.category
    confidence = prediction.confidence
    cached: dict | None = None
    cache_key = None
    settings = get_settings()
    decision_engine = DecisionEngine(
        answer_confidence=settings.answer_confidence_threshold,
        answer_similarity=settings.answer_similarity_threshold,
        clarify_confidence=settings.clarify_confidence_threshold,
    )
    if category not in {
        "Security / Fraud",
        "Greeting",
        "Thanks / Goodbye",
        "Out of Scope",
    }:
        cache_key = (
            f"support-answer:{category}:"
            + hashlib.sha256(
                classifier.preprocess(follow_up.query).encode()
            ).hexdigest()
        )
        try:
            serialized = _cache.get(cache_key)
            cached = json.loads(serialized) if serialized else None
        except Exception as exc:
            logger.bind(exception=type(exc).__name__).warning(
                "Support response cache unavailable"
            )
    if cached and cached.get("mode") in {"matched", "default"}:
        category = str(cached["category"])
        confidence = float(cached["confidence"])
        similarity = float(cached["similarity"])
        mode = str(cached["mode"])
        reply = str(cached["reply"])
        options: list[str] = []
    else:
        matches = retriever.retrieve(follow_up.query, top_k=3, category=category)
        similarity = matches[0].score if matches else 0.0
        mode = decision_engine.decide(confidence, similarity, category)
        options = []
        if mode == "clarify" or follow_up.needs_clarification:
            mode = "clarify"
        if mode == "clarify":
            options = conversation.pending_clarification or []
        if mode == "clarify" and not options:
            options = list(
                dict.fromkeys(
                    item_category
                    for item_category, _ in prediction.alternatives
                    if item_category != category
                )
            )[:2]
            options.insert(0, category)
            options = options[:2]
        matched_response = matches[0].response if matches else ""
        reply = ResponseGenerator().generate_response(
            category,
            matched_response,
            mode,
            clarification_options=options,
            user_message=clean_text,
        )
        if cache_key and mode in {"matched", "default"}:
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
                logger.bind(exception=type(exc).__name__).warning(
                    "Support response cache unavailable"
                )
    escalated = mode == "fallback"

    conversation.current_topic = category
    conversation.pending_clarification = options if mode == "clarify" else None
    conversation.updated_at = datetime.now(UTC)
    user_message = Message(
        conversation_id=conversation.id, sender="user", body=clean_text
    )
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
        "ticket_id": ticket.id
        if ticket
        else (conversation.ticket.id if conversation.ticket else None),
        "options": options,
    }


def rebuild_knowledge_base(db: Session) -> tuple[float, int]:
    entries = db.scalars(
        select(KnowledgeEntry).where(KnowledgeEntry.enabled.is_(True))
    ).all()
    if not entries:
        raise ValueError("Knowledge base cannot be empty")
    temporary_path = DATA_PATH.with_suffix(".tmp")
    temporary_path.parent.mkdir(parents=True, exist_ok=True)
    with temporary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["Customer Message", "Category", "Company Response"]
        )
        writer.writeheader()
        writer.writerows(
            {
                "Customer Message": entry.message,
                "Category": entry.category,
                "Company Response": entry.response,
            }
            for entry in entries
        )
    artifact, accuracy, sample_count = train_pipeline(
        temporary_path, return_metrics=True
    )
    new_classifier = SupportCategoryClassifier(artifact)
    new_retriever = TicketRetriever(entries)
    temporary_path.replace(DATA_PATH)
    new_retriever.knowledge_base_path = DATA_PATH
    global _classifier, _retriever
    with _lock:
        _classifier = new_classifier
        _retriever = new_retriever
    return accuracy, sample_count
