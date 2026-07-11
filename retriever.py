"""Retrieve the most similar previous ticket using TF-IDF and cosine similarity."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from classifier import preprocess_text


class TicketRetriever:
    """Find the closest ticket in the knowledge base for a new customer message."""

    def __init__(self, knowledge_base_path: str = "knowledge_base.csv") -> None:
        self.knowledge_base_path = self._resolve_path(knowledge_base_path)
        self.tickets_by_category: Dict[str, List[Dict[str, str]]] = {}
        self.indexes: Dict[str, Tuple[TfidfVectorizer, object]] = {}
        self._load_tickets()
        self._build_indexes()

    def _resolve_path(self, knowledge_base_path: str) -> Path:
        path = Path(knowledge_base_path)
        if path.is_absolute():
            return path
        return Path(__file__).resolve().parent / path

    def _load_tickets(self) -> None:
        if not self.knowledge_base_path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {self.knowledge_base_path}")

        with self.knowledge_base_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not row:
                    continue
                message = (row.get("Customer Message") or row.get("customer message") or "").strip()
                response = (row.get("Company Response") or row.get("company response") or "").strip()
                category = (row.get("Category") or row.get("category") or "General Inquiry").strip()
                if message:
                    ticket = {
                        "Customer Message": message,
                        "Company Response": response,
                        "Category": category,
                    }
                    self.tickets_by_category.setdefault(category, []).append(ticket)

        if not self.tickets_by_category:
            raise ValueError("Knowledge base does not contain any tickets for retrieval.")

    def _build_indexes(self) -> None:
        for category, category_tickets in self.tickets_by_category.items():
            messages = [preprocess_text(ticket["Customer Message"]) for ticket in category_tickets]
            vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            matrix = vectorizer.fit_transform(messages)
            self.indexes[category] = (vectorizer, matrix)

    def retrieve(self, message: str, category: str, preprocessed_text: Optional[str] = None) -> Tuple[str, float, str]:
        """Return the closest ticket, similarity score, and company response for the predicted category."""
        text = preprocessed_text if preprocessed_text is not None else preprocess_text(message)
        if not text:
            return "", 0.0, ""

        category = category or "General Inquiry"
        index_pair = self.indexes.get(category)
        if index_pair is None:
            return "", 0.0, ""

        vectorizer, tfidf_matrix = index_pair
        query_vector = vectorizer.transform([text])
        similarities = cosine_similarity(query_vector, tfidf_matrix)[0]
        best_index = int(np.argmax(similarities))
        similarity_score = float(similarities[best_index])
        best_ticket = self.tickets_by_category[category][best_index]

        return best_ticket["Customer Message"], similarity_score, best_ticket["Company Response"]
