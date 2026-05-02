"""
Classifier module for Support Triage Agent.
Detects request type and product area using keyword matching.
"""

from typing import Tuple


class IssueClassifier:
    """Classifies support issues by type and product area."""
    
    # Request type keywords
    REQUEST_TYPE_KEYWORDS = {
        "faq": ["how do i", "how to", "what is", "explain", "tutorial", "guide", "help me understand", "can you help", "tell me about", "help me debug"],
        "bug": ["error", "crash", "bug", "broken", "issue", "problem", "failed", "exception", "traceback", "timeout", "slow"],
        "billing": ["charge", "bill", "payment", "price", "cost", "invoice", "refund", "subscription", "cancel", "charged", "duplicate charge", "overcharged", "cancel my billing", "billing history", "view bill"],
        "account_access": ["login", "password", "locked", "can't access", "forgot password", "cannot log in", "account locked", "reset password", "authentication error", "locked out", "can't log in", "authentication", "failed login", "unlock account", "sign in", "two-factor", "2fa", "verification failed", "reset my password"],
        "fraud": ["fraud", "unauthorized", "hacked", "stolen", "unauthorized transaction", "suspicious", "someone accessed", "compromised", "cloned", "card cloned", "stolen card", "identity theft", "unauthorized charge"],
        "permissions": ["permission", "access denied", "no access", "don't have access", "can't view", "insufficient", "unauthorized access", "can't edit", "read only", "can't share"]
    }
    
    # Product area keywords
    PRODUCT_AREA_KEYWORDS = {
        "HackerRank": ["hackerrank", "coding challenge", "interview preparation", "algorithm", "data structure", "contest", "programming languages", "reset progress"],
        "Claude": ["claude", "ai assistant", "anthropic", "conversation", "model", "ai help", "claude api", "response time", "generate code", "development workflow"],
        "Visa": ["visa", "payment", "credit card", "transaction", "merchant", "visa card", "cardholder", "dispute charge", "contactless", "activate card", "card cloned", "stolen card", "card", "purchase", "purchases"]
    }
    
    def classify(self, issue_text: str) -> Tuple[str, str]:
        """
        Classify an issue by request type and product area.
        
        Args:
            issue_text: The support issue text
            
        Returns:
            Tuple of (request_type, product_area)
        """
        issue_lower = issue_text.lower()
        
        # Detect request type
        request_type = self._detect_request_type(issue_lower)
        
        # Detect product area
        product_area = self._detect_product_area(issue_lower)
        
        return request_type, product_area
    
    def _detect_request_type(self, issue_lower: str) -> str:
        """Detect request type using keyword matching with priority."""
        # Priority 1: Check high-risk categories first (account_access, fraud, billing)
        high_risk_types = ["account_access", "fraud", "billing"]
        for req_type in high_risk_types:
            keywords = self.REQUEST_TYPE_KEYWORDS[req_type]
            if any(keyword in issue_lower for keyword in keywords):
                return req_type
        
        # Priority 2: Check other request types
        scores = {}
        for req_type, keywords in self.REQUEST_TYPE_KEYWORDS.items():
            if req_type not in high_risk_types:
                count = sum(1 for keyword in keywords if keyword in issue_lower)
                scores[req_type] = count
        
        # Return highest scoring type, default to "faq"
        if max(scores.values()) == 0:
            return "faq"
        return max(scores, key=scores.get)
    
    def _detect_product_area(self, issue_lower: str) -> str:
        """Detect product area using keyword matching."""
        # Score each area by keyword matches
        scores = {}
        for area, keywords in self.PRODUCT_AREA_KEYWORDS.items():
            count = sum(1 for keyword in keywords if keyword in issue_lower)
            scores[area] = count
        
        # Return highest scoring area, default to "HackerRank"
        if max(scores.values()) == 0:
            return "HackerRank"
        return max(scores, key=scores.get)
