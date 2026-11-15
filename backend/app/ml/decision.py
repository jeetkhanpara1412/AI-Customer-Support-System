class DecisionEngine:
    def __init__(
        self,
        answer_confidence: float = 0.60,
        answer_similarity: float = 0.45,
        clarify_confidence: float = 0.35,
    ):
        self.answer_confidence = answer_confidence
        self.answer_similarity = answer_similarity
        self.clarify_confidence = clarify_confidence

    def decide(self, classifier_confidence: float, similarity_score: float, category: str = "") -> str:
        normalized_category = category.casefold()
        if normalized_category == "security / fraud":
            return "fallback"
        if normalized_category == "greeting":
            return "greeting"
        if normalized_category == "thanks / goodbye":
            return "thanks"
        if normalized_category == "out of scope":
            return "out_of_scope"
        if (
            classifier_confidence >= self.answer_confidence
            and similarity_score >= self.answer_similarity
        ):
            return "matched"
        if classifier_confidence >= self.clarify_confidence:
            return "clarify"
        return "fallback"
