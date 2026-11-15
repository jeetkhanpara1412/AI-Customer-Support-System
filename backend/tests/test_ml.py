from app.ml.decision import DecisionEngine
from app.ml.intents import explicit_intent
from app.ml.responder import ResponseGenerator
from app.ml.retriever import KnowledgeRow, TicketRetriever
from app.ml.train import train_pipeline


class FakeEncoder:
    def __init__(self):
        self.calls: list[list[str]] = []

    def encode(self, sentences: list[str], **_kwargs):
        import hashlib

        import numpy as np

        self.calls.append(sentences)
        vectors = []
        for sentence in sentences:
            vector = np.zeros(384, dtype=np.float32)
            for token in sentence.lower().split():
                index = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], "big") % 384
                vector[index] += 1
            norm = np.linalg.norm(vector)
            vectors.append(vector / norm if norm else vector)
        return np.vstack(vectors)


def test_train_pipeline_creates_artifact(tmp_path):
    csv_path = tmp_path / "knowledge_base.csv"
    csv_path.write_text("""Customer Message,Category,Company Response
I cannot log in,Account Access,Reset your password.
I forgot my password,Account Access,Reset your password.
Sign in is not working,Account Access,Reset your password.
Help me access my account,Account Access,Reset your password.
I was charged twice,Payment Issue,We reviewed the charge.
The payment was declined,Payment Issue,Check your payment details.
My card failed at checkout,Payment Issue,Check your payment details.
The payment did not go through,Payment Issue,Check your payment details.
I need a refund,Refund,Your refund is in progress.
Please return my money,Refund,Your refund is in progress.
My refund is late,Refund,Your refund is in progress.
Can I get my money back,Refund,Your refund is in progress.
This is suspicious fraud,Security / Fraud,Escalate to a specialist.
Someone hacked my account,Security / Fraud,Escalate to a specialist.
I see an unauthorized charge,Security / Fraud,Escalate to a specialist.
This transaction is not mine,Security / Fraud,Escalate to a specialist.
""", encoding="utf-8")
    model_dir = tmp_path / "artifacts"
    model_dir.mkdir(exist_ok=True)
    artifact = train_pipeline(str(csv_path), str(model_dir), encoder=FakeEncoder())
    assert artifact.exists()
    assert artifact.name.endswith(".joblib")


def test_retrieval_and_decisions(tmp_path):
    encoder = FakeEncoder()
    retriever = TicketRetriever(
        [
            KnowledgeRow(1, "reset my account password", "Account Access", "Use password reset."),
            KnowledgeRow(2, "change the password", "Account Access", "Open account security settings."),
            KnowledgeRow(3, "forgot my sign in credentials", "Account Access", "Recover your login."),
            KnowledgeRow(4, "how to cancel my monthly plan", "Billing", "Manage plan settings."),
        ],
        encoder=encoder,
        cache_path=tmp_path / "embeddings.joblib",
    )
    results = retriever.retrieve("change password", top_k=3)
    assert len(results) == 3
    assert results[0].category == "Account Access"
    assert 0.0 <= results[0].score <= 1.0
    assert DecisionEngine().decide(0.75, results[0].score, "Account Access") == "matched"
    assert DecisionEngine().decide(0.45, 0.2, "Account Access") == "clarify"
    assert DecisionEngine().decide(0.2, 0.2, "Account Access") == "fallback"
    call_count = len(encoder.calls)
    retriever.reload(retriever.rows + [KnowledgeRow(5, "billing receipt", "Billing", "View billing settings.")])
    assert len(encoder.calls) == call_count + 1
    assert encoder.calls[-1] == ["billing receipt"]


def test_fraud_always_escalates_regardless_of_scores():
    engine = DecisionEngine(answer_confidence=0.6, answer_similarity=0.45)
    assert engine.decide(1.0, 1.0, "Security / Fraud") == "fallback"
    response = ResponseGenerator().generate_response("Security / Fraud", "Do not trust matched content", "matched")
    assert "human support specialist" in response


def test_fallback_response_is_escalated():
    engine = DecisionEngine(answer_confidence=0.6, answer_similarity=0.45)
    assert engine.decide(0.2, 0.1, "General Inquiry") == "fallback"
    assert "support specialist" in ResponseGenerator().generate_response(
        "General Inquiry",
        response_mode="fallback",
    )


def test_greeting_thanks_and_out_of_scope_have_direct_responses():
    generator = ResponseGenerator()
    assert explicit_intent("hi") == "Greeting"
    assert "What can I help" in generator.generate_response("Greeting", response_mode="greeting")
    assert explicit_intent("thanks") == "Thanks / Goodbye"
    assert "welcome" in generator.generate_response("Thanks / Goodbye", response_mode="thanks").lower()
    assert explicit_intent("delete my Instagram") == "Out of Scope"
    assert "other platforms" in generator.generate_response("Out of Scope", response_mode="out_of_scope")
    assert explicit_intent("what's the weather") == "Out of Scope"


def test_support_rules_handle_typo_and_high_signal_topics():
    assert explicit_intent("chnage password") == "Account Access"
    assert explicit_intent("i was charged twice") == "Payment Issue"
    assert explicit_intent("someone hacked my account") == "Security / Fraud"
