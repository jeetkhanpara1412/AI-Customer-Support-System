<<<<<<< HEAD
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
=======
"""
Retriever module for Support Triage Agent.
Implements TF-IDF based document retrieval system.
"""

import os
from pathlib import Path
from typing import Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class DocumentRetriever:
    """Retrieves relevant documents using TF-IDF similarity."""
    
    CONFIDENCE_THRESHOLD = 0.3
    
    def __init__(self, data_dir: str = "data"):
        """Initialize retriever and build vector index."""
        self.data_dir = Path(data_dir)
        self.documents = []
        self.doc_names = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.build_vector_index()
    
    def build_vector_index(self):
        """Load documents and build TF-IDF index."""
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        # Load all .txt files from data directory
        if self.data_dir.exists():
            for filename in sorted(self.data_dir.glob("*.txt")):
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:  # Only add non-empty documents
                        # Clean text: lowercase, strip, normalize spaces
                        cleaned = ' '.join(content.lower().split())
                        self.documents.append(cleaned)
                        self.doc_names.append(filename.stem)
        
        # If no documents found, create empty ones for demo
        if not self.documents:
            self.documents = ["sample document"]
            self.doc_names = ["empty"]
        
        # Build TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            lowercase=True,
            min_df=1,
            max_df=1.0
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
    
    def retrieve_document(self, query: str) -> Tuple[str, float, bool]:
        """
        Retrieve the most relevant document for a query.
        
        Args:
            query: The search query (usually the issue text)
            
        Returns:
            Tuple of (document_text, similarity_score, found)
            - document_text: The retrieved document or empty string
            - similarity_score: Cosine similarity score (0-1)
            - found: Whether a sufficiently similar document was found
        """
        if not self.documents or self.tfidf_matrix is None:
            return "", 0.0, False
        
        # Clean query: lowercase, strip, normalize spaces
        cleaned_query = ' '.join(query.lower().split())
        
        # Vectorize the query
        try:
            query_vector = self.vectorizer.transform([cleaned_query])
        except:
            return "", 0.0, False
        
        # Calculate similarity with all documents
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
        
        # Get the most similar document
        best_idx = np.argmax(similarities)
        best_score = float(similarities[best_idx])
        
        # Check if score meets confidence threshold
        found = best_score >= self.CONFIDENCE_THRESHOLD
        
        document = self.documents[best_idx] if found else ""
        
        return document, best_score, found
>>>>>>> 22d775295bd02b2266de166adbc66b5a39493b91
