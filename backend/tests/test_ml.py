from app.ml.train import train_pipeline
from app.ml.decision import DecisionEngine
from app.ml.responder import ResponseGenerator


def test_train_pipeline_creates_artifact(tmp_path):
    csv_path = tmp_path / "knowledge_base.csv"
    csv_path.write_text(
        """Customer Message,Category,Company Response
I cannot log in,Account Access,Reset your password.
I was charged twice,Payment Issue,We reviewed the charge.
I need a refund,Refund,Your refund is in progress.
This is suspicious fraud,Security / Fraud,Escalate to a specialist.
""",
        encoding="utf-8",
    )
    model_dir = tmp_path / "artifacts"
    model_dir.mkdir(exist_ok=True)
    artifact = train_pipeline(str(csv_path), str(model_dir))
    assert artifact.exists()
    assert artifact.name.endswith(".joblib")


def test_retrieval_and_decisions():
    engine = DecisionEngine()
    assert engine.decide(0.9, 0.7) == "matched"
    assert engine.decide(0.8, 0.2) == "default"
    assert engine.decide(0.4, 0.2) == "fallback"


def test_fraud_always_escalates_regardless_of_scores():
    engine = DecisionEngine(confidence_threshold=0.7, similarity_threshold=0.35)
    assert engine.decide(1.0, 1.0, "Security / Fraud") == "fallback"
    response = ResponseGenerator().generate_response("Security / Fraud", "Do not trust matched content", "matched")
    assert "human support specialist" in response


def test_fallback_response_is_escalated():
    engine = DecisionEngine(confidence_threshold=0.7, similarity_threshold=0.35)
    assert engine.decide(0.2, 0.1, "General Inquiry") == "fallback"
    assert "escalated" in ResponseGenerator().generate_response("General Inquiry", response_mode="fallback")
