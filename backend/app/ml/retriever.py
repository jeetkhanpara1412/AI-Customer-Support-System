import csv
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.preprocess import preprocess_text


class TicketRetriever:
    def __init__(self, knowledge_base_path: str | Path):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.tickets_by_category: dict[str, list[dict[str, str]]] = {}
        self.indexes: dict[str, tuple[TfidfVectorizer, object]] = {}
        self.reload()

    def reload(self) -> None:
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {self.knowledge_base_path}")
        tickets: dict[str, list[dict[str, str]]] = {}
        with self.knowledge_base_path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                message = (row.get("Customer Message") or row.get("message") or "").strip()
                category = (row.get("Category") or row.get("category") or "General Inquiry").strip()
                response = (row.get("Company Response") or row.get("response") or "").strip()
                if message and category and response:
                    tickets.setdefault(category, []).append(
                        {"Customer Message": message, "Category": category, "Company Response": response}
                    )
        if not tickets:
            raise ValueError("Knowledge base contains no valid entries")
        indexes = {}
        for category, rows in tickets.items():
            matrix_input = [preprocess_text(row["Customer Message"]) for row in rows]
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            indexes[category] = (vectorizer, vectorizer.fit_transform(matrix_input))
        self.tickets_by_category = tickets
        self.indexes = indexes

    def retrieve(self, message: str, category: str, preprocessed_text: str | None = None) -> tuple[str, float, str]:
        text = preprocessed_text if preprocessed_text is not None else preprocess_text(message)
        index = self.indexes.get(category)
        if not text or index is None:
            return "", 0.0, ""
        vectorizer, matrix = index
        scores = cosine_similarity(vectorizer.transform([text]), matrix)[0]
        best_index = int(np.argmax(scores))
        row = self.tickets_by_category[category][best_index]
        return row["Customer Message"], float(scores[best_index]), row["Company Response"]
