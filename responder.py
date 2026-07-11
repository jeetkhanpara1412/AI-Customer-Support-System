"""Generate professional customer support responses."""

from __future__ import annotations


class ResponseGenerator:
    """Create polished support responses for customers."""

    def generate_response(self, category: str, company_response: str = "", response_mode: str = "matched") -> str:
        """Return a professional support response for the classified ticket."""
        if response_mode == "matched" and company_response and company_response.strip():
            return company_response.strip()
        if response_mode == "default":
            return self.get_default_response(category)
        return self.get_fallback_response()

    def get_default_response(self, category: str) -> str:
        """Return a polite category-specific support response."""
        default_responses = {
            "Account Access": "We're sorry you're having trouble signing in. Please use the Forgot Password option to reset your password. If you still cannot access your account, contact our support team.",
            "Billing": "We're sorry for the inconvenience. You can manage your subscription from the Billing section of your account. If the issue continues, please contact our billing team.",
            "Refund": "We're sorry for the inconvenience. Your refund request has been received. Our team will review it and update you within 3–5 business days.",
            "Technical Issue": "We're sorry you're experiencing a technical issue. Please restart the application and update it to the latest version. If the problem continues, our technical team will investigate.",
            "Payment Issue": "We're sorry about the payment problem. Please verify your payment details and try again. If the charge still fails, our support team can help.",
            "Order / Delivery": "We're sorry about the order or delivery issue. Please confirm your shipping details and contact support if your order has not arrived as expected.",
            "Account Management": "We're sorry you're having trouble with account settings. Please review your account profile and contact support if you need further help.",
            "Security / Fraud": "We're sorry you're dealing with a security concern. Please secure your account immediately and contact our support team for urgent assistance.",
            "General Inquiry": "Thanks for reaching out. Our support team is happy to help with your question. Please contact us if you need any additional assistance.",
        }
        return default_responses.get(category, self.get_fallback_response())

    def get_fallback_response(self) -> str:
        """Return a generic fallback message for low-confidence cases."""
        return "We're sorry, but we couldn't confidently identify your issue. Your request has been forwarded to our support team for further assistance."
