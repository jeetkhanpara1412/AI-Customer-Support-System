"""
Main entry point for Support Triage Agent.
Orchestrates the triage process: classification, retrieval, decision, response.
"""

import csv
import sys
from pathlib import Path
from classifier import IssueClassifier
from retriever import DocumentRetriever
from decision import DecisionEngine
from responder import ResponseGenerator
from logger import TriageLogger


class TriageAgent:
    """Main orchestrator for the support triage system."""
    
    def __init__(self):
        """Initialize all components."""
        self.classifier = IssueClassifier()
        self.retriever = DocumentRetriever()
        self.decision_engine = DecisionEngine()
        self.responder = ResponseGenerator()
        self.logger = TriageLogger("log.txt")
        self.results = []
    
    def process_issues(self, input_dir: str = "support_tickets") -> bool:
        """
        Process all support issues from CSV files in the input directory.
        
        Args:
            input_dir: Path to directory containing CSV files
            
        Returns:
            True if successful, False otherwise
        """
        input_path = Path(input_dir)
        
        # Check if input directory exists
        if not input_path.exists():
            print(f"❌ Error: Input directory not found: {input_dir}")
            print(f"   Expected at: {input_path.absolute()}")
            return False
        
        print(f"\n📂 Reading issues from: {input_dir}")
        
        # Find all CSV files in the directory
        csv_files = list(input_path.glob("*.csv"))
        if not csv_files:
            print("⚠️  No CSV files found in input directory")
            return False
        
        total_issues = 0
        
        for csv_file in csv_files:
            print(f"Processing file: {csv_file.name}")
            
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    issues = list(reader)
                
                if not issues:
                    print(f"⚠️  No issues found in {csv_file.name}")
                    continue
                
                print(f"✓ Loaded {len(issues)} issues from {csv_file.name}")
                total_issues += len(issues)
                
            except Exception as e:
                print(f"❌ Error reading {csv_file.name}: {e}")
                continue
        
        if total_issues == 0:
            print("⚠️  No issues found in any CSV file")
            return False
        
        print(f"\n✓ Total loaded {total_issues} issues from {len(csv_files)} files\n")
        
        # Process each issue from all files
        processed_count = 0
        for csv_file in csv_files:
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    issues = list(reader)
                
                for idx, issue in enumerate(issues, 1):
                    print(f"Processing {processed_count + idx}/{total_issues}...", end="", flush=True)
                    
                    try:
                        # Map CSV columns to expected names
                        # Try standard names first, then fallback to CSV column names
                        issue_id = (issue.get("issue_id") or issue.get("Issue") or f"{csv_file.stem}_{idx}").strip()
                        issue_text = (issue.get("issue_text") or issue.get("Subject") or "").strip()
                        
                        if not issue_text:
                            print(" (empty)")
                            continue
                        
                        # Process the issue
                        result = self._process_single_issue(issue_id, issue_text)
                        self.results.append(result)
                        print("✓")
                        
                    except Exception as e:
                        print(f"❌ ({e})")
                        continue
                
                processed_count += len(issues)
                
            except Exception as e:
                print(f"❌ Error processing {csv_file.name}: {e}")
                continue
        
        print(f"\n✓ Processed {len(self.results)} issues successfully\n")
        return True
    
    def _process_single_issue(self, issue_id: str, issue_text: str) -> dict:
        """
        Process a single support issue through the entire pipeline.
        
        Args:
            issue_id: The issue identifier
            issue_text: The issue description
            
        Returns:
            Dictionary with issue, request_type, product_area, action, response
        """
        # Step 1: Log issue
        self.logger.log_issue(issue_id, issue_text)
        
        # Step 2: Classify
        request_type, product_area = self.classifier.classify(issue_text)
        self.logger.log_classification(request_type, product_area)
        
        # Step 3: Retrieve document
        document, similarity_score, found = self.retriever.retrieve_document(issue_text)
        self.logger.log_retrieval(issue_text, document, similarity_score, found)
        
        # Step 4: Make decision
        action, decision_reason = self.decision_engine.make_decision(
            request_type, similarity_score, found, issue_text
        )
        self.logger.log_decision(action, decision_reason)
        
        # Step 5: Generate response
        response = self.responder.generate_response(action, document, issue_text)
        self.logger.log_response(response)
        
        # Flush logger after each issue
        self.logger.flush()
        
        return {
            "issue_id": issue_id,
            "request_type": request_type,
            "product_area": product_area,
            "action": action,
            "response": response
        }
    
    def save_output(self, output_file: str = "output.csv") -> bool:
        """
        Save results to CSV file.
        
        Args:
            output_file: Path to output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.results:
            print("❌ No results to save")
            return False
        
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["issue_id", "request_type", "product_area", "action", "response"]
                )
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"💾 Output saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving output: {e}")
            return False
    
    def run(self, input_dir: str = "support_tickets",
            output_file: str = "output.csv") -> bool:
        """
        Run the complete triage workflow.
        
        Args:
            input_dir: Path to directory containing CSV files
            output_file: Path to output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        print("\n" + "="*80)
        print("SUPPORT TRIAGE AGENT")
        print("="*80)
        
        # Process issues
        if not self.process_issues(input_dir):
            return False
        
        # Save results
        if not self.save_output(output_file):
            return False
        
        print("="*80)
        print("✓ Triage process completed successfully!")
        print(f"  Results: {output_file}")
        print(f"  Logs: log.txt")
        print("="*80 + "\n")
        
        return True


def main():
    """Main entry point."""
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "support_tickets"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.csv"
    agent = TriageAgent()
    success = agent.run(input_dir, output_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
