<<<<<<< HEAD
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
=======
"""
Logger module for Support Triage Agent.
Captures step-by-step reasoning for each issue.
"""

from datetime import datetime
from pathlib import Path


class TriageLogger:
    """Manages logging for the triage system."""
    
    def __init__(self, log_file: str = "log.txt"):
        """Initialize logger with output file."""
        self.log_file = Path(log_file)
        self.entries = []
        self._write_header()
    
    def _write_header(self):
        """Write header to log file."""
        header = f"\n{'='*80}\n"
        header += f"SUPPORT TRIAGE SYSTEM LOG\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"{'='*80}\n\n"
        self.log_file.write_text(header, encoding="utf-8")
    
    def log_issue(self, issue_id: str, issue_text: str):
        """Log the start of processing an issue."""
        entry = f"\n{'─'*80}\n"
        entry += f"ISSUE ID: {issue_id}\n"
        entry += f"TEXT: {issue_text[:100]}...\n" if len(issue_text) > 100 else f"TEXT: {issue_text}\n"
        entry += f"{'─'*80}\n"
        self.entries.append(entry)
    
    def log_classification(self, request_type: str, product_area: str):
        """Log classification results."""
        entry = f"[CLASSIFICATION]\n"
        entry += f"  Request Type: {request_type}\n"
        entry += f"  Product Area: {product_area}\n"
        self.entries.append(entry)
    
    def log_retrieval(self, query: str, document: str, similarity_score: float, found: bool):
        """Log document retrieval."""
        entry = f"[DOCUMENT RETRIEVAL]\n"
        entry += f"  Query: {query[:80]}...\n" if len(query) > 80 else f"  Query: {query}\n"
        entry += f"  Document Found: {found}\n"
        entry += f"  Similarity Score: {similarity_score:.4f}\n"
        if found:
            entry += f"  Document: {document[:100]}...\n" if len(document) > 100 else f"  Document: {document}\n"
        self.entries.append(entry)
    
    def log_decision(self, action: str, reason: str):
        """Log the decision."""
        entry = f"[DECISION]\n"
        entry += f"  Action: {action}\n"
        entry += f"  Reason: {reason}\n"
        self.entries.append(entry)
    
    def log_response(self, response: str):
        """Log the generated response."""
        entry = f"[RESPONSE]\n"
        entry += f"  {response[:150]}...\n" if len(response) > 150 else f"  {response}\n"
        self.entries.append(entry)
    
    def flush(self):
        """Write all entries to log file."""
        current_content = self.log_file.read_text(encoding="utf-8")
        new_content = current_content + "".join(self.entries)
        self.log_file.write_text(new_content, encoding="utf-8")
        self.entries = []
>>>>>>> 22d775295bd02b2266de166adbc66b5a39493b91
