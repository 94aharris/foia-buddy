from typing import List, Dict, Any, Optional
import time
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class LocalPDFSearchAgent(BaseAgent):
    """
    Searches local PDF directory for documents relevant to FOIA requests.

    This agent finds PDFs in a local directory, analyzes their filenames and metadata,
    and identifies the most relevant ones to be parsed by the PDF Parser Agent.
    """

    def __init__(self, nvidia_client, pdf_directory: str = "sample_data/pdfs"):
        super().__init__(
            name="local_pdf_search",
            description="Searches local PDF directory for relevant documents",
            nvidia_client=nvidia_client
        )
        self.pdf_directory = pdf_directory
        self.add_capability("local_pdf_search")
        self.add_capability("pdf_discovery")
        self.add_capability("filename_analysis")

    def get_system_prompt(self) -> str:
        return """You are the Local PDF Search Agent for FOIA-Buddy.

Your role is to:
1. SEARCH local PDF directories for documents relevant to FOIA requests
2. ANALYZE PDF filenames and metadata to determine relevance
3. RANK PDFs by likely relevance to the request
4. IDENTIFY which PDFs should be parsed and analyzed

When analyzing PDFs:
- Extract keywords from the FOIA request
- Match keywords against PDF filenames
- Consider file dates if available in filename
- Prioritize PDFs with relevant naming patterns
- Return ranked list of PDFs to be parsed

Provide structured analysis including:
- total_pdfs_found: Count of all PDFs discovered
- relevant_pdfs: List of PDFs ranked by relevance
- search_keywords: Keywords used for matching
- recommendations: Which PDFs to prioritize for parsing"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute local PDF search task."""
        start_time = time.time()

        try:
            # Get FOIA request from task
            foia_request = task.context.get("foia_request", "")
            max_pdfs = task.context.get("max_pdfs", 20)  # Limit PDFs to process

            # Find all PDFs in directory
            pdf_files = self._find_pdfs()

            if not pdf_files:
                return self._create_result(
                    task.task_id,
                    success=True,
                    data={
                        "total_pdfs_found": 0,
                        "relevant_pdfs": [],
                        "message": f"No PDFs found in {self.pdf_directory}",
                        "pdf_directory": self.pdf_directory
                    },
                    reasoning=f"No PDF files found in {self.pdf_directory}",
                    confidence=1.0,
                    start_time=start_time
                )

            # Analyze and rank PDFs
            if foia_request:
                ranked_pdfs = await self._rank_pdfs_by_relevance(pdf_files, foia_request)
            else:
                # If no FOIA request, just return all PDFs
                ranked_pdfs = [
                    {
                        "path": str(pdf),
                        "filename": pdf.name,
                        "size": pdf.stat().st_size,
                        "relevance_score": 0.5,
                        "match_reason": "No FOIA request provided for ranking"
                    }
                    for pdf in pdf_files
                ]

            # Limit to max_pdfs
            selected_pdfs = ranked_pdfs[:max_pdfs]

            result_data = {
                "total_pdfs_found": len(pdf_files),
                "relevant_pdfs": selected_pdfs,
                "pdfs_selected": len(selected_pdfs),
                "pdf_directory": self.pdf_directory,
                "pdf_paths": [pdf["path"] for pdf in selected_pdfs]
            }

            reasoning = f"Found {len(pdf_files)} PDFs, selected top {len(selected_pdfs)} for processing"

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning=reasoning,
                confidence=0.8,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during local PDF search: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    def _find_pdfs(self) -> List[Path]:
        """Find all PDF files in the directory."""
        pdf_dir = Path(self.pdf_directory)

        if not pdf_dir.exists():
            return []

        # Find all PDFs recursively
        pdf_files = list(pdf_dir.rglob("*.pdf"))

        # Sort by modification time (most recent first)
        pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        return pdf_files

    async def _rank_pdfs_by_relevance(
        self,
        pdf_files: List[Path],
        foia_request: str
    ) -> List[Dict[str, Any]]:
        """
        Rank PDFs by relevance to the FOIA request using AI analysis.
        """

        # Extract keywords from FOIA request
        keywords = self._extract_keywords_from_request(foia_request)

        # Score each PDF
        ranked = []

        for pdf_path in pdf_files:
            filename = pdf_path.stem.lower()

            # Simple keyword matching in filename
            matches = sum(1 for keyword in keywords if keyword in filename)

            # Calculate relevance score
            score = min(matches / max(len(keywords), 1), 1.0) if keywords else 0.5

            # Boost score for certain patterns
            if any(term in filename for term in ['foia', 'policy', 'memo', 'report']):
                score = min(score + 0.2, 1.0)

            match_reasons = []
            for keyword in keywords:
                if keyword in filename:
                    match_reasons.append(f"Filename contains '{keyword}'")

            ranked.append({
                "path": str(pdf_path),
                "filename": pdf_path.name,
                "size": pdf_path.stat().st_size,
                "relevance_score": score,
                "match_reason": "; ".join(match_reasons) if match_reasons else "General document",
                "matched_keywords": [kw for kw in keywords if kw in filename]
            })

        # Sort by relevance score
        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Use AI to provide additional analysis for top PDFs
        if ranked[:5]:  # Analyze top 5
            await self._ai_analyze_top_pdfs(ranked[:5], foia_request)

        return ranked

    async def _ai_analyze_top_pdfs(
        self,
        top_pdfs: List[Dict[str, Any]],
        foia_request: str
    ):
        """Use AI to provide additional relevance analysis for top PDFs."""

        pdf_list = "\n".join([
            f"{i+1}. {pdf['filename']} (Score: {pdf['relevance_score']:.2f})"
            for i, pdf in enumerate(top_pdfs)
        ])

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""
Analyze these PDF filenames for relevance to the FOIA request:

FOIA REQUEST:
{foia_request[:500]}

TOP PDFs FOUND:
{pdf_list}

For each PDF, briefly explain why it might be relevant or not relevant.
Keep each explanation to 1-2 sentences.
"""}
        ]

        response = await self._generate_response(messages, use_thinking=True)

        if "error" not in response:
            # Add AI analysis to the PDFs
            analysis = response.get("content", "")
            for pdf in top_pdfs:
                pdf["ai_analysis"] = analysis[:200]  # Store snippet

    def _extract_keywords_from_request(self, foia_request: str) -> List[str]:
        """Extract key search terms from FOIA request."""

        # Common keywords to look for
        request_lower = foia_request.lower()

        important_terms = [
            'ai', 'artificial intelligence', 'policy', 'governance',
            'ethics', 'implementation', 'oversight', 'compliance',
            'algorithm', 'machine learning', 'automation', 'framework',
            'guideline', 'regulation', 'transparency', 'accountability',
            'memo', 'memorandum', 'report', 'email', 'correspondence'
        ]

        # Find matching terms
        keywords = [term for term in important_terms if term in request_lower]

        # Extract quoted phrases
        import re
        quoted = re.findall(r'"([^"]+)"', foia_request)
        keywords.extend([q.lower() for q in quoted if len(q) > 2])

        # Remove duplicates
        keywords = list(dict.fromkeys(keywords))

        # If no keywords found, use common document terms
        if not keywords:
            keywords = ['policy', 'memo', 'report', 'document']

        return keywords[:15]  # Limit to top 15

    def get_pdf_count(self) -> int:
        """Get total count of PDFs in directory."""
        return len(self._find_pdfs())

    def get_pdf_list(self) -> List[str]:
        """Get list of all PDF filenames."""
        return [pdf.name for pdf in self._find_pdfs()]
