import unittest

from main import SupportTicketSystem


class SupportSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.system = SupportTicketSystem()

    def test_suspicious_charge_uses_support_response(self) -> None:
        result = self.system.process_message("I noticed a suspicious charge on my account")
        self.assertNotIn("couldn't confidently identify", result["company_response"])
        self.assertIn("support", result["company_response"].lower())

    def test_cancellation_request_uses_relevant_response(self) -> None:
        result = self.system.process_message("I want to cancel my subscription and stop the monthly charge")
        self.assertNotIn("couldn't confidently identify", result["company_response"])
        self.assertIn("cancel", result["company_response"].lower())


if __name__ == "__main__":
    unittest.main()
