class ResponseGenerator:
    def generate_response(self, category: str, company_response: str = "", response_mode: str = "matched") -> str:
        if category.casefold() == "security / fraud":
            return (
                "Your security concern has been escalated to a human support specialist. "
                "If you suspect account access, change your password and contact your bank."
            )
        if response_mode == "matched" and company_response.strip():
            return company_response.strip()
        if response_mode == "default":
            return self.get_default_response(category)
        return self.get_fallback_response()

    @staticmethod
    def get_default_response(category: str) -> str:
        return {
            "Account Access": "Use the password reset option to regain access. Contact support if you still cannot sign in.",
            "Billing": "You can review subscription and billing settings in your account. Contact billing support for account-specific help.",
            "Refund": "Your refund request needs review by our support team. We will follow up with the next steps.",
            "Technical Issue": "Please restart and update the application. If the problem persists, support can investigate further.",
            "Payment Issue": "Please verify your payment details and try again. Contact support if the payment still fails.",
            "Order / Delivery": "Please check your order status and delivery address. Contact support if your order is delayed.",
            "Account Management": "Review your profile settings or contact support for help managing your account.",
            "Security / Fraud": "Your security concern has been escalated to a human support specialist.",
            "General Inquiry": "Thanks for reaching out. Our support team is happy to help with your question.",
        }.get(category, ResponseGenerator.get_fallback_response())

    @staticmethod
    def get_fallback_response() -> str:
        return "We could not confidently identify your issue, so your request has been escalated to our support team."
