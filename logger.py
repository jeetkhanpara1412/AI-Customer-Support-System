"""Store simple customer support conversations for review."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class TriageLogger:
    """Write a clean conversation log without internal ML details."""

    def __init__(self, log_file: str = "support_triage_log.txt") -> None:
        self.log_file = Path(log_file)
        self._write_header()

    def _write_header(self) -> None:
        header = f"{'=' * 80}\n"
        header += "CUSTOMER SUPPORT CONVERSATION LOG\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"{'=' * 80}\n\n"
        self.log_file.write_text(header, encoding="utf-8")

    def log_conversation(self, customer_message: str, company_response: str) -> None:
        """Append a simple customer-support conversation entry."""
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"Customer: {customer_message}\n")
            handle.write(f"Support: {company_response}\n")
            handle.write(f"{'-' * 80}\n")
