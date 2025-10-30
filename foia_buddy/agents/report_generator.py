from typing import List, Dict, Any
import time
from datetime import datetime
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class ReportGeneratorAgent(BaseAgent):
    """Generates comprehensive FOIA response reports from research findings."""

    def __init__(self, nvidia_client):
        super().__init__(
            name="report_generator",
            description="Creates structured FOIA response reports with source attribution",
            nvidia_client=nvidia_client
        )
        self.add_capability("report_generation")
        self.add_capability("content_synthesis")
        self.add_capability("source_attribution")

    def get_system_prompt(self) -> str:
        return """You are the Report Generator Agent for FOIA-Buddy.

Your role is to:
1. SYNTHESIZE findings from multiple research agents into comprehensive reports
2. CREATE structured FOIA response documents that meet legal requirements
3. ATTRIBUTE all information to specific sources with proper documentation
4. IDENTIFY and FLAG any content requiring redaction or special handling

Report Structure Requirements:
- Executive Summary: Brief overview of the request and findings
- Methodology: How the search was conducted
- Findings: Detailed results organized by topic/source
- Source Documentation: Complete attribution for all information
- Redaction Notes: Identification of sensitive content
- Compliance Statement: Legal compliance status

Writing Style:
- Professional, clear, and factual
- Appropriate for government/legal context
- Complete source attribution
- Objective tone without speculation

CRITICAL OUTPUT FORMAT INSTRUCTIONS:
- Generate your report in markdown format with clear sections and proper formatting
- DO NOT wrap your response in code blocks (no ```markdown or ``` markers)
- Output the raw markdown directly without any wrapper
- Start directly with the markdown heading (e.g., # FOIA Response Report)"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute report generation task."""
        start_time = time.time()

        try:
            # Get research results and FOIA request from task context
            research_results = task.context.get("research_results", {})
            foia_request = task.context.get("foia_request", "")
            coordination_plan = task.context.get("coordination_plan", {})

            # Generate the report
            report_content = await self._generate_report(
                foia_request,
                research_results,
                coordination_plan
            )

            if "error" in report_content:
                return self._create_result(
                    task.task_id,
                    success=False,
                    data={"error": report_content["error"]},
                    reasoning="Failed to generate report",
                    confidence=0.0,
                    start_time=start_time
                )

            # Create additional outputs
            summary = self._create_executive_summary(research_results)
            compliance_notes = self._create_compliance_notes(research_results)

            result_data = {
                "report_content": report_content["content"],
                "executive_summary": summary,
                "compliance_notes": compliance_notes,
                "source_count": self._count_sources(research_results),
                "redaction_flags": self._collect_redaction_flags(research_results),
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "model_used": "nvidia-nemotron-nano-9b-v2",
                    "reasoning_tokens": report_content.get("reasoning", "")
                }
            }

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning="Successfully generated comprehensive FOIA response report",
                confidence=0.9,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during report generation: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    async def _generate_report(
        self,
        foia_request: str,
        research_results: Dict[str, Any],
        coordination_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate the main report content using Nemotron."""

        # Prepare research summary for the model
        research_summary = self._prepare_research_summary(research_results)

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""
Generate a comprehensive FOIA response report based on the following:

ORIGINAL FOIA REQUEST:
{foia_request}

RESEARCH FINDINGS:
{research_summary}

COORDINATION PLAN:
{coordination_plan}

Create a professional, well-structured report that addresses the FOIA request with complete source attribution and compliance notes.

IMPORTANT: Output raw markdown directly - DO NOT wrap your response in ```markdown code blocks.
"""}
        ]

        response = await self._generate_response(messages, use_thinking=True)

        # Post-process to remove any markdown code block wrappers
        if "content" in response and response["content"]:
            content = response["content"].strip()

            # Remove ```markdown and ``` wrappers if present
            if content.startswith("```markdown"):
                content = content[len("```markdown"):].strip()
            elif content.startswith("```"):
                content = content[3:].strip()

            if content.endswith("```"):
                content = content[:-3].strip()

            response["content"] = content

        return response

    def _prepare_research_summary(self, research_results: Dict[str, Any]) -> str:
        """Prepare research results for inclusion in the prompt."""
        summary_parts = []

        if "document_analyses" in research_results:
            summary_parts.append("DOCUMENT SEARCH RESULTS:")
            for i, doc in enumerate(research_results["document_analyses"][:5], 1):
                summary_parts.append(f"\nDocument {i}: {doc.get('file_path', 'Unknown')}")
                summary_parts.append(f"Relevance Score: {doc.get('relevance_score', 0.0)}")
                summary_parts.append(f"Summary: {doc.get('summary', 'No summary')}")
                if doc.get('key_findings'):
                    summary_parts.append("Key Findings:")
                    for finding in doc['key_findings'][:3]:
                        summary_parts.append(f"  - {finding}")

        if "search_summary" in research_results:
            summary_parts.append(f"\nSearch Summary: {research_results['search_summary']}")

        return "\n".join(summary_parts)

    def _create_executive_summary(self, research_results: Dict[str, Any]) -> str:
        """Create executive summary of findings."""
        total_docs = research_results.get("total_documents_searched", 0)
        relevant_docs = research_results.get("relevant_documents_found", 0)

        summary = f"""Executive Summary:

The FOIA request was processed using an automated multi-agent system that conducted comprehensive document searches and analysis.

Search Results:
- Total documents searched: {total_docs}
- Relevant documents identified: {relevant_docs}
- Success rate: {(relevant_docs/max(total_docs, 1)*100):.1f}%

The system identified potentially responsive documents and flagged content requiring review for redaction compliance.
"""
        return summary

    def _create_compliance_notes(self, research_results: Dict[str, Any]) -> str:
        """Create compliance and legal notes."""
        redaction_flags = self._collect_redaction_flags(research_results)

        notes = """Compliance Notes:

1. All identified documents have been analyzed for relevance to the FOIA request
2. Potential redaction requirements have been flagged for manual review
3. Source attribution has been maintained throughout the process
4. Response prepared in accordance with FOIA guidelines
"""

        if redaction_flags:
            notes += f"\nRedaction Review Required:\n"
            for flag in set(redaction_flags):
                notes += f"- {flag}\n"

        return notes

    def _count_sources(self, research_results: Dict[str, Any]) -> int:
        """Count the number of sources found."""
        return research_results.get("relevant_documents_found", 0)

    def _collect_redaction_flags(self, research_results: Dict[str, Any]) -> List[str]:
        """Collect all redaction flags from research results."""
        flags = []

        if "document_analyses" in research_results:
            for doc in research_results["document_analyses"]:
                flags.extend(doc.get("redaction_flags", []))

        return flags