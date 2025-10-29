from typing import List, Dict, Any
import os
import time
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage, DocumentResult


class DocumentResearcherAgent(BaseAgent):
    """Searches and analyzes local markdown documents for FOIA-relevant information."""

    def __init__(self, nvidia_client, document_directory: str = "sample_data/documents"):
        super().__init__(
            name="document_researcher",
            description="Searches local document repositories using semantic analysis",
            nvidia_client=nvidia_client
        )
        self.document_directory = document_directory
        self.add_capability("document_search")
        self.add_capability("content_analysis")
        self.add_capability("relevance_scoring")

    def get_system_prompt(self) -> str:
        return """You are the Document Researcher Agent for FOIA-Buddy.

Your role is to:
1. SEARCH through local document repositories for information relevant to FOIA requests
2. ANALYZE document content to determine relevance and extract key information
3. SCORE documents based on their relevance to the request
4. EXTRACT relevant sections and summarize findings

When analyzing documents:
- Focus on factual information that directly addresses the FOIA request
- Look for dates, names, policies, procedures, and specific events
- Identify potential redaction needs (PII, classified info)
- Provide confidence scores for relevance (0.0-1.0)

Always respond with structured analysis including:
- relevance_score: How relevant the document is (0.0-1.0)
- key_findings: List of important information found
- relevant_sections: Specific text passages that address the request
- summary: Brief summary of the document's relevance
- redaction_flags: Any content that may need redaction"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute document research task."""
        start_time = time.time()

        try:
            # Get search parameters from task
            search_query = task.context.get("search_query", "")
            foia_request = task.context.get("foia_request", "")

            # Find and analyze documents
            documents = self._find_documents()
            analyzed_docs = []

            for doc_path in documents:
                doc_content = self._read_document(doc_path)
                if doc_content:
                    analysis = await self._analyze_document(doc_content, foia_request, doc_path)
                    if analysis["relevance_score"] > 0.1:  # Only include relevant docs
                        analyzed_docs.append(analysis)

            # Sort by relevance score
            analyzed_docs.sort(key=lambda x: x["relevance_score"], reverse=True)

            result_data = {
                "total_documents_searched": len(documents),
                "relevant_documents_found": len(analyzed_docs),
                "document_analyses": analyzed_docs[:10],  # Top 10 most relevant
                "search_summary": f"Searched {len(documents)} documents, found {len(analyzed_docs)} relevant matches"
            }

            reasoning = f"Successfully searched {len(documents)} documents and identified {len(analyzed_docs)} relevant matches"

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning=reasoning,
                confidence=0.85,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during document research: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    def _find_documents(self) -> List[str]:
        """Find all markdown documents in the document directory."""
        doc_dir = Path(self.document_directory)
        if not doc_dir.exists():
            return []

        markdown_files = []
        for file_path in doc_dir.rglob("*.md"):
            markdown_files.append(str(file_path))

        return markdown_files

    def _read_document(self, file_path: str) -> str:
        """Read document content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

    async def _analyze_document(self, content: str, foia_request: str, file_path: str) -> Dict[str, Any]:
        """Analyze a document for relevance to FOIA request."""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""
Analyze this document for relevance to the FOIA request:

FOIA REQUEST:
{foia_request}

DOCUMENT PATH: {file_path}
DOCUMENT CONTENT:
{content[:2000]}{"..." if len(content) > 2000 else ""}

Provide structured analysis with relevance scoring and key findings.
"""}
        ]

        response = await self._generate_response(messages, use_thinking=True)

        if "error" in response:
            return {
                "file_path": file_path,
                "relevance_score": 0.0,
                "key_findings": [],
                "relevant_sections": [],
                "summary": "Error analyzing document",
                "redaction_flags": [],
                "error": response["error"]
            }

        # Parse response to extract structured data
        analysis_text = response["content"]

        # Extract relevance score using simple heuristics
        relevance_score = self._extract_relevance_score(analysis_text, content, foia_request)

        return {
            "file_path": file_path,
            "relevance_score": relevance_score,
            "key_findings": self._extract_key_findings(analysis_text),
            "relevant_sections": self._extract_relevant_sections(content, foia_request),
            "summary": analysis_text[:300] + "..." if len(analysis_text) > 300 else analysis_text,
            "redaction_flags": self._identify_redaction_flags(content),
            "full_analysis": analysis_text
        }

    def _extract_relevance_score(self, analysis: str, content: str, foia_request: str) -> float:
        """Extract or calculate relevance score."""
        # Simple keyword matching approach
        foia_keywords = foia_request.lower().split()
        content_lower = content.lower()

        matches = sum(1 for keyword in foia_keywords if keyword in content_lower and len(keyword) > 2)
        score = min(matches / max(len(foia_keywords), 1), 1.0)

        # Boost score if analysis seems positive
        if any(word in analysis.lower() for word in ["relevant", "important", "addresses", "contains"]):
            score = min(score + 0.3, 1.0)

        return score

    def _extract_key_findings(self, analysis: str) -> List[str]:
        """Extract key findings from analysis text."""
        # Simple extraction - look for bullet points or numbered lists
        findings = []
        lines = analysis.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                findings.append(line[1:].strip())
            elif line and len(line) > 20 and any(word in line.lower() for word in ["finding", "important", "relevant"]):
                findings.append(line)

        return findings[:5]  # Top 5 findings

    def _extract_relevant_sections(self, content: str, foia_request: str) -> List[str]:
        """Extract relevant sections from document content."""
        sections = []
        foia_keywords = [word.lower() for word in foia_request.split() if len(word) > 2]

        # Split content into paragraphs
        paragraphs = content.split('\n\n')

        for para in paragraphs:
            if len(para) > 50:  # Skip very short paragraphs
                para_lower = para.lower()
                keyword_count = sum(1 for keyword in foia_keywords if keyword in para_lower)

                if keyword_count >= 2:  # At least 2 keyword matches
                    sections.append(para.strip()[:500] + "..." if len(para) > 500 else para.strip())

        return sections[:3]  # Top 3 relevant sections

    def _identify_redaction_flags(self, content: str) -> List[str]:
        """Identify content that may need redaction."""
        flags = []
        content_lower = content.lower()

        # Simple PII detection
        if "ssn" in content_lower or "social security" in content_lower:
            flags.append("Potential SSN")
        if "@" in content and "email" in content_lower:
            flags.append("Email addresses")
        if "phone" in content_lower or "tel:" in content_lower:
            flags.append("Phone numbers")
        if "classified" in content_lower or "confidential" in content_lower:
            flags.append("Classified information")

        return flags