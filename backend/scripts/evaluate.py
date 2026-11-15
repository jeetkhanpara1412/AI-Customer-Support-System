import csv
import sys
from collections import Counter
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.ml.classifier import ARTIFACT_PATH, SupportCategoryClassifier
from app.ml.decision import DecisionEngine
from app.ml.intents import predict_intent
from app.ml.retriever import TicketRetriever
from app.ml.train import DATA_PATH

EVAL_PATH = Path(__file__).parents[1] / "eval" / "test_set.csv"
LABELS = (
    "Account Access",
    "Account Management",
    "Billing",
    "General Inquiry",
    "Greeting",
    "Order / Delivery",
    "Out of Scope",
    "Payment Issue",
    "Refund",
    "Security / Fraud",
    "Thanks / Goodbye",
    "Technical Issue",
)


def load_test_set(path: Path = EVAL_PATH) -> tuple[list[str], list[str]]:
    messages: list[str] = []
    categories: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            message = (row.get("Message") or "").strip()
            category = (row.get("Category") or "").strip()
            if message and category:
                messages.append(message)
                categories.append(category)
    if len(messages) < 150:
        raise ValueError(f"Evaluation set must contain at least 150 messages; found {len(messages)}")
    unknown = set(categories) - set(LABELS)
    if unknown:
        raise ValueError(f"Unknown evaluation labels: {', '.join(sorted(unknown))}")
    return messages, categories


def evaluate() -> int:
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(f"Trained model not found: {ARTIFACT_PATH}; run python -m app.ml.train first")
    messages, expected = load_test_set()
    classifier = SupportCategoryClassifier()
    retriever = TicketRetriever(
        DATA_PATH,
        cache_path=ARTIFACT_PATH.with_name("evaluation_embeddings.joblib"),
    )
    settings = get_settings()
    decisions = DecisionEngine(
        answer_confidence=settings.answer_confidence_threshold,
        answer_similarity=settings.answer_similarity_threshold,
        clarify_confidence=settings.clarify_confidence_threshold,
    )
    predicted: list[str] = []
    modes: list[str] = []
    for message in messages:
        result = predict_intent(message, classifier)
        matches = retriever.retrieve(message, top_k=1, category=result.category)
        similarity = matches[0].score if matches else 0.0
        predicted.append(result.category)
        modes.append(decisions.decide(result.confidence, similarity, result.category))

    accuracy = float(accuracy_score(expected, predicted))
    fraud_indexes = [index for index, category in enumerate(expected) if category == "Security / Fraud"]
    fraud_recall = sum(predicted[index] == "Security / Fraud" for index in fraud_indexes) / max(
        len(fraud_indexes), 1
    )
    escalation_rate = sum(mode == "fallback" for mode in modes) / len(modes)
    wrong_answer_rate = sum(
        mode == "matched" and expected[index] != predicted[index]
        for index, mode in enumerate(modes)
    ) / len(modes)
    clarification_rate = sum(mode == "clarify" for mode in modes) / len(modes)

    print(f"Evaluation messages: {len(messages)}")
    print(f"Overall accuracy: {accuracy:.4f}")
    print(f"Fraud recall: {fraud_recall:.4f}")
    print(f"Escalation rate: {escalation_rate:.4f}")
    print(f"Wrong-answer rate: {wrong_answer_rate:.4f}")
    print(f"Clarification rate: {clarification_rate:.4f}")
    print("\nAccuracy / precision / recall by category:")
    print(classification_report(expected, predicted, labels=LABELS, zero_division=0))
    print("Confusion matrix (rows: expected, columns: predicted):")
    print(confusion_matrix(expected, predicted, labels=LABELS))
    print("Per-category accuracy:")
    counts = Counter(expected)
    correct = Counter(
        category for category, result in zip(expected, predicted, strict=True) if category == result
    )
    for category in LABELS:
        if counts[category]:
            print(f"  {category}: {correct[category] / counts[category]:.4f} ({correct[category]}/{counts[category]})")
    failures = [
        (message, truth, guess, mode)
        for message, truth, guess, mode in zip(messages, expected, predicted, modes, strict=True)
        if truth != guess
    ]
    if failures:
        print("\nMisclassified evaluation messages:")
        for message, truth, guess, mode in failures:
            print(f"  expected={truth!r}, predicted={guess!r}, mode={mode!r}: {message}")

    if accuracy < 0.88 or fraud_recall < 1.0:
        print("\nEvaluation failed: require accuracy >= 0.88 and Security / Fraud recall == 1.00.")
        return 1
    print("\nEvaluation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(evaluate())
