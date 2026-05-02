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
