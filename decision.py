"""Decision logic for the support response workflow."""

from __future__ import annotations


class DecisionEngine:
    """Choose whether to return a matched response, a default category response, or a fallback response."""

    def __init__(self, confidence_threshold: float = 0.70, similarity_threshold: float = 0.35) -> None:
        self.confidence_threshold = confidence_threshold
        self.similarity_threshold = similarity_threshold

    def decide(self, classifier_confidence: float, similarity_score: float) -> str:
        """Return the response mode based on classifier confidence and similarity score."""
        if similarity_score >= self.similarity_threshold:
            return "matched"
        if classifier_confidence >= self.confidence_threshold:
            return "default"
        return "fallback"
