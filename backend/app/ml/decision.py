class DecisionEngine:
    def __init__(self, confidence_threshold: float = 0.70, similarity_threshold: float = 0.35):
        self.confidence_threshold = confidence_threshold
        self.similarity_threshold = similarity_threshold

    def decide(self, classifier_confidence: float, similarity_score: float, category: str = "") -> str:
        if category.casefold() == "security / fraud":
            return "fallback"
        if similarity_score >= self.similarity_threshold:
            return "matched"
        if classifier_confidence >= self.confidence_threshold:
            return "default"
        return "fallback"
