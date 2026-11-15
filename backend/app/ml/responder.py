import re


class ResponseGenerator:
    def generate_response(
        self,
        category: str,
        company_response: str = "",
        response_mode: str = "matched",
        clarification_options: list[str] | None = None,
        user_message: str = "",
    ) -> str:
        normalized_category = category.casefold()
        if normalized_category == "security / fraud":
            return (
                "I’m sorry this happened. I’ve alerted a human support specialist to help secure your account. "
                "If you still have access, change your password and contact your bank about unfamiliar charges."
            )
        if response_mode == "greeting":
            return "Hi! I’m your support assistant. What can I help you with today?"
        if response_mode == "thanks":
            return "You’re welcome! If anything else comes up, I’m here to help."
        if response_mode == "out_of_scope":
            platform = re.search(
                r"\b(instagram|facebook|tiktok|twitter|snapchat|whatsapp|netflix|spotify|youtube|google)\b",
                user_message,
                re.IGNORECASE,
            )
            if platform:
                name = platform.group(1).capitalize()
                return (
                    f"I can help with this service, but I can’t access or manage {name} accounts. "
                    f"Please use {name}’s own settings or help center."
                )
            if re.search(r"\b(weather|forecast)\b", user_message, re.IGNORECASE):
                return "I’m here to help with this service, so I can’t provide weather forecasts."
            return (
                "I can help with this service, but I can’t manage accounts or answer questions for other "
                "platforms. Please use that service’s own settings or help center."
            )
        if response_mode == "matched" and company_response.strip():
            return company_response.strip()
        if response_mode == "clarify":
            options = clarification_options or []
            if len(options) >= 2:
                return (
                    "I want to make sure I point you to the right help. Is this about "
                    f"{options[0]} or {options[1]}?"
                )
            return "Could you share a little more detail so I can point you to the right help?"
        if response_mode == "default":
            return self.get_default_response(category)
        return "I’m not confident I understood that. I’ve asked a support specialist to follow up and help you."

    @staticmethod
    def get_default_response(category: str) -> str:
        return {
            "Account Access": (
                "To change your password, open account settings and choose Change password. "
                "If you can’t sign in, use Forgot password on the sign-in page."
            ),
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
        return "I’m not confident I understood that. I’ve asked a support specialist to follow up and help you."
