"""Support ticket classification using TF-IDF and scikit-learn."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import List, Optional, Tuple

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

CONTRACTION_REPLACEMENTS = {
    "can't": "cannot",
    "won't": "will not",
    "n't": " not",
}

SYNONYM_PATTERNS = [
    (r"\blog in\b", "login"),
    (r"\bsign in\b", "login"),
    (r"\bloginto\b", "login"),
    (r"\bsign into\b", "login"),
    (r"\bcancel membership\b", "cancel subscription"),
    (r"\bpremium\b", "subscription"),
    (r"\bmembership\b", "subscription"),
    (r"\brefund my money\b", "refund"),
    (r"\brefund money\b", "refund"),
    (r"\bcredit card\b", "card"),
    (r"\bdebit card\b", "card"),
    (r"\bpackage\b", "order"),
    (r"\bdelivery\b", "delivery"),
    (r"\bwebsite\b", "site"),
    (r"\bapp\b", "application"),
    (r"\bsuspicious charge\b", "fraud charge"),
    (r"\bunauthorized transaction\b", "fraud transaction"),
    (r"\bunauthorized access\b", "fraud access"),
    (r"\bcompromised account\b", "fraud account"),
    (r"\bhacked account\b", "fraud account"),
    (r"\bunrecognized charge\b", "fraud charge"),
    (r"\bcharge not recognize\b", "fraud charge"),
]


def preprocess_text(text: str) -> str:
    """Clean and normalize a customer message for ML processing."""
    if not text:
        return ""

    normalized = text.lower()
    for old_value, new_value in CONTRACTION_REPLACEMENTS.items():
        normalized = normalized.replace(old_value, new_value)

    normalized = re.sub(r"https?://\S+|www\.\S+", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    for pattern, replacement in SYNONYM_PATTERNS:
        normalized = re.sub(pattern, replacement, normalized)

    tokens = normalized.split()
    filtered_tokens = [token for token in tokens if token not in ENGLISH_STOP_WORDS]

    return " ".join(filtered_tokens).strip()


class SupportCategoryClassifier:
    """Predict a support category from a customer message using TF-IDF."""

    def __init__(self, knowledge_base_path: str = "knowledge_base.csv") -> None:
        self.knowledge_base_path = self._resolve_path(knowledge_base_path)
        self.messages: List[str] = []
        self.categories: List[str] = []
        self.pipeline: Optional[Pipeline] = None
        self._load_training_data()
        self._train_model()

    def _resolve_path(self, knowledge_base_path: str) -> Path:
        path = Path(knowledge_base_path)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parent / path

    def _load_training_data(self) -> None:
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {self.knowledge_base_path}")

        with self.knowledge_base_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not row:
                    continue
                message = (row.get("Customer Message") or row.get("customer message") or "").strip()
                category = (row.get("Category") or row.get("category") or "General Inquiry").strip()
                if message:
                    self.messages.append(preprocess_text(message))
                    self.categories.append(category)

        if not self.messages:
            raise ValueError("Knowledge base does not contain any training examples.")

    def _train_model(self) -> None:
        self.pipeline = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
                ("classifier", LogisticRegression(max_iter=5000, solver="lbfgs")),
            ]
        )
        self.pipeline.fit(self.messages, self.categories)

    def preprocess(self, message: str) -> str:
        """Return a cleaned version of the customer message."""
        return preprocess_text(message)

    def predict(self, message: str, preprocessed_text: Optional[str] = None) -> Tuple[str, float]:
        """Predict the support category and return the confidence score."""
        if self.pipeline is None:
            raise RuntimeError("Classifier has not been trained.")

        text = preprocessed_text if preprocessed_text is not None else self.preprocess(message)
        if not text:
            return "General Inquiry", 0.0

        prediction = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        confidence = float(max(probabilities))
        return str(prediction), confidence
