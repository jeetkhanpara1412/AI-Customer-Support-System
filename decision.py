<<<<<<< HEAD
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
=======
"""
Decision module for Support Triage Agent.
Determines whether to answer or escalate based on risk assessment.
"""

from typing import Tuple


class DecisionEngine:
    """Evaluates risk and makes escalation decisions."""
    
    # High-risk request types that should always escalate
    ESCALATE_REQUEST_TYPES = ["fraud", "billing", "account_access"]
    
    # Confidence threshold for document retrieval
    CONFIDENCE_THRESHOLD = 0.3
    
    def make_decision(
        self,
        request_type: str,
        similarity_score: float,
        document_found: bool,
        issue_text: str
    ) -> Tuple[str, str]:
        """
        Make a decision to answer or escalate.
        
        Args:
            request_type: The classified request type
            similarity_score: The TF-IDF similarity score
            document_found: Whether a document above threshold was found
            issue_text: The original issue text
            
        Returns:
            Tuple of (action, reason)
            - action: "answer" or "escalate"
            - reason: Explanation for the decision
        """
        # Always escalate high-risk types
        if request_type in ["fraud", "account_access"]:
            reason = f"High-risk request type '{request_type}' requires human review"
            return "escalate", reason
        
        # Handle billing: allow informational queries
        if request_type == "billing":
            if self._is_informational_billing(issue_text):
                if document_found and similarity_score >= self.CONFIDENCE_THRESHOLD:
                    reason = f"Informational billing query answered (score: {similarity_score:.4f})"
                    return "answer", reason
                else:
                    reason = f"Billing query but low confidence ({similarity_score:.4f})"
                    return "escalate", reason
            else:
                reason = "Complex billing request requires human review"
                return "escalate", reason
        
        # Check for low confidence retrieval
        if not document_found or similarity_score < self.CONFIDENCE_THRESHOLD:
            reason = f"Low confidence ({similarity_score:.4f} < {self.CONFIDENCE_THRESHOLD}): No relevant documentation found"
            return "escalate", reason
        
        # Safe to answer
        reason = f"Request type '{request_type}' is safe; relevant documentation retrieved (score: {similarity_score:.4f})"
        return "answer", reason
    
    def _is_informational_billing(self, issue_text: str) -> bool:
        """Check if billing query is informational (view/history) vs. action (charge/refund)."""
        text_lower = issue_text.lower()
        informational_words = ["view", "history", "see", "check", "status", "show"]
        action_words = ["charge", "refund", "cancel", "payment", "bill", "invoice", "cost", "price", "subscription", "update", "change"]
        
        has_informational = any(word in text_lower for word in informational_words)
        has_action = any(word in text_lower for word in action_words)
        
        return has_informational and not has_action
>>>>>>> 22d775295bd02b2266de166adbc66b5a39493b91
