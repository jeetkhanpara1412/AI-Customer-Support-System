"""
Responder module for Support Triage Agent.
Generates appropriate responses based on decisions.
"""


class ResponseGenerator:
    """Generates responses for support issues."""
    
    ESCALATION_MESSAGE = "This issue requires further assistance. We are escalating it to a human support agent."
    
    def generate_response(
        self,
        action: str,
        document: str,
        issue_text: str = ""
    ) -> str:
        """
        Generate a response based on action and retrieved document.
        
        Args:
            action: "answer" or "escalate"
            document: Retrieved document text (empty if escalating)
            issue_text: Original issue text for context
            
        Returns:
            The generated response
        """
        if action == "escalate":
            return self.ESCALATION_MESSAGE
        
        # Action is "answer"
        if document:
            # Format the response based on the retrieved document
            response = self._format_answer(document)
            return response
        else:
            # Fallback if no document available
            return self.ESCALATION_MESSAGE
    
    def _format_answer(self, document: str) -> str:
        """
        Format a response using the retrieved document.
        
        Args:
            document: The retrieved document text
            
        Returns:
            Formatted response
        """
        # Check if document is very short (header/title only)
        if len(document) < 20:
            return document
        
        # Truncate if too long
        if len(document) > 500:
            response = document[:497] + "..."
        else:
            response = document
        
        return response
