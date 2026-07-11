"""Main entry point for the customer support chatbot experience."""

from __future__ import annotations

import sys
from typing import Dict

from classifier import SupportCategoryClassifier
from decision import DecisionEngine
from logger import TriageLogger
from responder import ResponseGenerator
from retriever import TicketRetriever


class SupportTicketSystem:
    """Orchestrate the full customer support ticket workflow."""

    def __init__(self) -> None:
        self.classifier = SupportCategoryClassifier()
        self.retriever = TicketRetriever()
        self.decision_engine = DecisionEngine()
        self.responder = ResponseGenerator()
        self.logger = TriageLogger("support_triage_log.txt")

    def process_message(self, customer_message: str) -> Dict[str, str]:
        """Process a single customer message end-to-end."""
        if not customer_message or not customer_message.strip():
            raise ValueError("Customer message cannot be empty.")

        preprocessed_text = self.classifier.preprocess(customer_message)
        category, confidence_score = self.classifier.predict(
            customer_message,
            preprocessed_text=preprocessed_text,
        )
        _, similarity_score, company_response = self.retriever.retrieve(
            customer_message,
            category,
            preprocessed_text=preprocessed_text,
        )
        response_mode = self.decision_engine.decide(confidence_score, similarity_score)
        generated_response = self.responder.generate_response(
            category,
            company_response,
            response_mode=response_mode,
        )

        self.logger.log_conversation(customer_message, generated_response)

        return {
            "customer_message": customer_message,
            "company_response": generated_response,
        }

    def run(self, customer_message: str) -> None:
        """Run the support workflow and print a clean chatbot-style response."""
        result = self.process_message(customer_message)
        print("Customer:")
        print(customer_message)
        print()
        print("Support:")
        print(result["company_response"])


def main() -> None:
    """Entry point for running the system from the command line."""
    if len(sys.argv) > 1:
        customer_message = " ".join(sys.argv[1:])
    else:
        customer_message = input("Customer: ").strip()

    if not customer_message:
        print("Support:\nWe're sorry, but we did not receive your message. Please try again.")
        sys.exit(1)

    agent = SupportTicketSystem()
    agent.run(customer_message)


if __name__ == "__main__":
    main()
