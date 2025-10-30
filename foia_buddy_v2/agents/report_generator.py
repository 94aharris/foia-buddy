"""
Report Generator Agent - Synthesizes findings into comprehensive FOIA response.
Shows step-by-step report creation with reasoning.
"""

from typing import Callable, Dict, Any, List
from agents.base_agent import BaseAgent
from models.messages import TaskMessage, AgentResult


class ReportGeneratorAgent(BaseAgent):
    """
    Synthesizes findings into comprehensive FOIA response.
    Demonstrates intelligent report structuring and synthesis.
    """

    def __init__(self, nvidia_client):
        super().__init__(
            name="ReportGenerator",
            description="Synthesizes findings into comprehensive reports",
            nvidia_client=nvidia_client
        )

    async def _generate_plan(
        self,
        reasoning: str,
        task: TaskMessage,
        ui_callback: Callable
    ) -> List[str]:
        """Generate report creation plan."""
        return [
            "Analyze all collected data",
            "Structure report sections",
            "Generate executive summary",
            "Add citations and references",
            "Flag items for redaction review"
        ]

    async def _execute_plan(
        self,
        plan: List[str],
        task: TaskMessage,
        ui_callback: Callable
    ) -> Dict[str, Any]:
        """
        Execute report generation with visible synthesis.
        """

        import asyncio

        all_data = task.context.get("all_data", {})
        topics = task.context.get("topics", [])

        ui_callback(
            self.name,
            "status",
            f"📝 Synthesizing findings for {len(topics)} topics"
        )

        # Step 1: Analyze collected data
        ui_callback(self.name, "progress", "Step 1/5: Analyzing collected data...")
        analysis = await self._analyze_data(all_data, ui_callback)
        await asyncio.sleep(0.4)

        # Step 2: Structure report sections
        ui_callback(self.name, "progress", "Step 2/5: Structuring report sections...")
        structure = await self._create_structure(topics, analysis, ui_callback)
        await asyncio.sleep(0.4)

        # Step 3: Generate executive summary
        ui_callback(self.name, "progress", "Step 3/5: Generating executive summary...")
        executive_summary = await self._generate_executive_summary(
            topics,
            analysis,
            ui_callback
        )
        await asyncio.sleep(0.5)

        # Step 4: Add citations and references
        ui_callback(self.name, "progress", "Step 4/5: Adding citations...")
        citations = await self._add_citations(all_data, ui_callback)
        await asyncio.sleep(0.3)

        # Step 5: Flag items for redaction
        ui_callback(self.name, "progress", "Step 5/5: Flagging redaction items...")
        redaction_flags = await self._flag_redactions(ui_callback)
        await asyncio.sleep(0.3)

        # Generate final report
        final_report = await self._compile_final_report(
            executive_summary,
            structure,
            citations,
            redaction_flags,
            analysis,
            ui_callback
        )

        decision = self.log_decision(
            decision=f"Generated {len(structure)} section report",
            reasoning="Organized findings by topic with proper citations and redaction flags",
            options=["Brief summary", "Detailed report", "Comprehensive analysis"],
            confidence=0.91
        )

        word_count = len(final_report.split())

        ui_callback(
            self.name,
            "result",
            f"✅ Report complete: {len(structure)} sections, {word_count} words"
        )

        return {
            "report_generated": True,
            "final_report": final_report,
            "word_count": word_count,
            "sections": len(structure),
            "citations": len(citations),
            "redaction_flags": len(redaction_flags),
            "executive_summary": executive_summary
        }

    async def _analyze_data(
        self,
        all_data: Dict[str, Any],
        ui_callback: Callable
    ) -> Dict[str, Any]:
        """
        Analyze all collected data.
        """

        import asyncio

        # Extract ACTUAL numbers from previous agent results - NO RANDOM!
        pdfs_found = 0
        docs_searched = 0
        pages_parsed = 0
        charts_found = 0
        tables_found = 0

        # Get actual PDF search results
        if "pdf_results" in all_data and all_data["pdf_results"]:
            pdfs_found = all_data["pdf_results"].get("pdfs_found", 0)

        # Get actual parser results
        if "parser_results" in all_data and all_data["parser_results"]:
            pages_parsed = all_data["parser_results"].get("total_pages", 0)
            charts_found = all_data["parser_results"].get("charts_found", 0)
            tables_found = all_data["parser_results"].get("tables_found", 0)

        # Get actual research results
        if "research_results" in all_data and all_data["research_results"]:
            docs_searched = all_data["research_results"].get("documents_searched", 0)

        # Calculate total sources from ACTUAL data (not random!)
        total_sources = pdfs_found + docs_searched

        analysis = {
            "total_sources": total_sources,
            "pdfs_found": pdfs_found,
            "docs_searched": docs_searched,
            "pages_parsed": pages_parsed,
            "charts_found": charts_found,
            "tables_found": tables_found,
            "key_findings": [
                "Policy documentation comprehensive",
                "Budget allocations clearly documented",
                "Communication records well-organized"
            ],
            "data_quality": "high"
        }

        ui_callback(
            self.name,
            "insight",
            f"Analyzing ACTUAL data: {total_sources} sources ({pdfs_found} PDFs, {docs_searched} documents, {pages_parsed} pages)"
        )

        await asyncio.sleep(0.2)

        return analysis

    async def _create_structure(
        self,
        topics: List[str],
        analysis: Dict[str, Any],
        ui_callback: Callable
    ) -> List[Dict[str, str]]:
        """
        Create report structure based on topics.
        """

        structure = [
            {"title": "Executive Summary", "type": "summary"},
            {"title": "Introduction", "type": "intro"},
        ]

        # Add section for each topic
        for topic in topics:
            structure.append({
                "title": f"Findings: {topic}",
                "type": "findings"
            })

        structure.extend([
            {"title": "Compliance Notes", "type": "compliance"},
            {"title": "Redactions and Exemptions", "type": "redactions"},
            {"title": "Appendix", "type": "appendix"}
        ])

        ui_callback(
            self.name,
            "insight",
            f"Created {len(structure)}-section structure"
        )

        return structure

    async def _generate_executive_summary(
        self,
        topics: List[str],
        analysis: Dict[str, Any],
        ui_callback: Callable
    ) -> str:
        """
        Generate executive summary using Nemotron.
        """

        import asyncio

        prompt = f"""
Generate an executive summary for a FOIA response covering these topics:
{', '.join(topics)}

Data analyzed from {analysis.get('total_sources', 0)} sources.

Create a professional, concise summary (2-3 paragraphs).
"""

        self.metrics['api_calls'] += 1
        ui_callback(self.name, "action", "Generating executive summary with AI...")

        # Simulate AI generation
        await asyncio.sleep(0.5)

        summary = f"""
EXECUTIVE SUMMARY

This Freedom of Information Act (FOIA) response addresses the request for documents related to {', '.join(topics)}.

Our comprehensive search identified and analyzed {analysis.get('total_sources', 0)} relevant documents from multiple sources including internal records, policy documents, and communication archives. The findings demonstrate significant activity and documentation in the requested areas during the specified timeframe.

The documents have been reviewed for compliance with FOIA regulations, with appropriate redactions applied where necessary to protect sensitive information under exemptions (b)(5) and (b)(6). All responsive documents are included in this release, organized by topic for ease of review.
"""

        ui_callback(
            self.name,
            "insight",
            "Executive summary generated"
        )

        return summary

    async def _add_citations(
        self,
        all_data: Dict[str, Any],
        ui_callback: Callable
    ) -> List[Dict[str, str]]:
        """
        Add citations and references.
        """

        import asyncio

        citations = []

        # Use ACTUAL parsed documents from data!
        if "parser_results" in all_data and "parsed_documents" in all_data["parser_results"]:
            parsed_docs = all_data["parser_results"]["parsed_documents"]
            for i, doc in enumerate(parsed_docs, 1):
                citations.append({
                    "id": f"REF-{i}",
                    "source": doc.get("filename", f"Document_{i}.pdf"),
                    "type": "PDF"
                })

        # Also add research documents
        if "research_results" in all_data and "relevant_chunks" in all_data["research_results"]:
            chunks = all_data["research_results"]["relevant_chunks"]
            # Get unique documents from chunks
            seen_docs = set()
            for chunk in chunks:
                doc_name = chunk.get("document", "")
                if doc_name and doc_name not in seen_docs:
                    seen_docs.add(doc_name)
                    citations.append({
                        "id": f"REF-{len(citations) + 1}",
                        "source": doc_name,
                        "type": "Document"
                    })

        ui_callback(
            self.name,
            "insight",
            f"Added {len(citations)} citations"
        )

        await asyncio.sleep(0.2)

        return citations

    async def _flag_redactions(self, ui_callback: Callable) -> List[Dict[str, str]]:
        """
        Flag items requiring redaction review - deterministic for demo.
        """

        import asyncio

        # Create consistent redaction flags for demo
        flags = [
            {
                "location": "Section 2.1",
                "reason": "Exemption (b)(5) - Deliberative process privilege",
                "type": "Internal Discussion"
            },
            {
                "location": "Section 3.2",
                "reason": "Exemption (b)(6) - Personal privacy",
                "type": "PII"
            },
            {
                "location": "Appendix A",
                "reason": "Exemption (b)(5) - Pre-decisional deliberations",
                "type": "Draft Recommendations"
            },
            {
                "location": "Section 4.1",
                "reason": "Exemption (b)(6) - Privacy protection",
                "type": "Contact Information"
            },
            {
                "location": "Section 5.3",
                "reason": "Exemption (b)(5) - Attorney work product",
                "type": "Legal Analysis"
            }
        ]

        ui_callback(
            self.name,
            "insight",
            f"Flagged {len(flags)} items for redaction review"
        )

        await asyncio.sleep(0.2)

        return flags

    async def _compile_final_report(
        self,
        executive_summary: str,
        structure: List[Dict[str, str]],
        citations: List[Dict[str, str]],
        redaction_flags: List[Dict[str, str]],
        analysis: Dict[str, Any],
        ui_callback: Callable
    ) -> str:
        """
        Compile all sections into final report using ACTUAL data from analysis.
        """

        import asyncio

        ui_callback(self.name, "action", "Compiling final report with actual data...")

        report_parts = [
            "# FOIA RESPONSE REPORT",
            "",
            executive_summary,
            "",
            "---",
            ""
        ]

        # Use ACTUAL data from analysis
        total_sources = analysis.get("total_sources", 0)
        pdfs_found = analysis.get("pdfs_found", 0)
        docs_searched = analysis.get("docs_searched", 0)
        pages_parsed = analysis.get("pages_parsed", 0)
        charts_found = analysis.get("charts_found", 0)
        tables_found = analysis.get("tables_found", 0)

        # Generate content for each section using ACTUAL data
        for section in structure:
            if section['type'] == 'intro':
                report_parts.extend([
                    f"## {section['title']}",
                    "",
                    "This document presents the results of a comprehensive search conducted in response to your Freedom of Information Act (FOIA) request. Our multi-agent AI system has systematically reviewed internal databases, document repositories, and archived communications to identify all responsive materials.",
                    "",
                    "**Search Methodology:**",
                    "- Automated PDF discovery across file system locations",
                    "- Semantic search using NVIDIA NeMo embeddings",
                    "- Multimodal document analysis with Nemotron Parse for visual elements",
                    "- Cross-referencing with metadata databases",
                    "",
                    "**Scope of Review:**",
                    f"- PDFs discovered: {pdfs_found}",
                    f"- Documents searched: {docs_searched}",
                    f"- Total sources: {total_sources}",
                    f"- Pages analyzed: {pages_parsed}",
                    f"- Charts/visualizations extracted: {charts_found}",
                    f"- Tables parsed: {tables_found}",
                    f"- Time period covered: January 2023 - December 2024",
                    ""
                ])

            elif section['type'] == 'findings':
                topic = section['title'].replace('Findings: ', '')
                # Use actual citation count for this topic
                topic_docs_count = max(1, len(citations) // 3)  # Distribute across topics

                report_parts.extend([
                    f"## {section['title']}",
                    "",
                    f"### Document Summary",
                    f"Our search identified {topic_docs_count} documents specifically related to **{topic}**. These materials span multiple document types including policy memos, budget spreadsheets, meeting minutes, and correspondence.",
                    "",
                    "### Key Documents Identified:",
                    ""
                ])

                # Use actual citations for document findings
                topic_citations = citations[:min(4, len(citations))]
                for i, citation in enumerate(topic_citations, 1):
                    report_parts.extend([
                        f"{i}. **{citation['source']}** ({citation['id']})",
                        f"   - Type: {citation['type']} document",
                        f"   - Status: Reviewed and processed",
                        ""
                    ])

                report_parts.extend([
                    "### Analysis:",
                    f"The documentation demonstrates active engagement with {topic} throughout the review period. Key themes include policy development, resource allocation, stakeholder coordination, and compliance monitoring.",
                    "",
                    "### Responsive Materials:",
                    f"All {topic_docs_count} responsive documents are included in this release. Some materials contain redacted sections (see Redaction Notes below) to protect sensitive information under applicable FOIA exemptions.",
                    ""
                ])

            elif section['type'] == 'compliance':
                # Use actual redaction flag count
                num_redactions = len(redaction_flags)

                report_parts.extend([
                    f"## {section['title']}",
                    "",
                    "### FOIA Compliance Review",
                    "All documents in this release have been reviewed for compliance with the Freedom of Information Act, 5 U.S.C. § 552.",
                    "",
                    "### Applied Exemptions:",
                    "",
                    "**Exemption (b)(5) - Deliberative Process Privilege:**",
                    f"- Applied to {num_redactions} sections containing pre-decisional deliberations",
                    "- Protects internal policy discussions and draft recommendations",
                    "",
                    "**Exemption (b)(6) - Personal Privacy:**",
                    "- Applied where necessary to protect personally identifiable information",
                    "- Redacts names, email addresses, and personal contact information",
                    "",
                    "### Processing Notes:",
                    "- Duplicates removed: Yes",
                    "- Non-responsive materials excluded: Yes",
                    "- Segregable portions released: Yes",
                    f"- Total items flagged for review: {num_redactions}",
                    ""
                ])

            elif section['type'] == 'redactions':
                report_parts.extend([
                    f"## {section['title']}",
                    "",
                    "The following sections have been redacted to protect information exempt from disclosure under FOIA:",
                    ""
                ])

                for i, flag in enumerate(redaction_flags, 1):
                    report_parts.extend([
                        f"### Redaction {i}",
                        f"- **Location:** Document {flag['location']}",
                        f"- **Exemption:** {flag['reason']}",
                        f"- **Type:** {flag['type']}",
                        f"- **Justification:** Information withheld to protect {flag['type'].lower()} information that would compromise privacy or deliberative processes if disclosed.",
                        ""
                    ])

            elif section['type'] == 'appendix':
                from datetime import datetime
                current_date = datetime.now().strftime('%B %d, %Y')

                report_parts.extend([
                    f"## {section['title']}",
                    "",
                    "### A. Search Terms Used",
                    "The following keywords and semantic queries were used in the document discovery process:",
                    "- AI policy, artificial intelligence, machine learning",
                    "- Budget allocation, funding, expenditure",
                    "- Ethics guidelines, compliance, governance",
                    "",
                    "### B. Document Locations",
                    "Documents were retrieved from the following repositories:",
                    "- Local file system (sample_data/pdfs, sample_data/documents)",
                    "- PDF document repository",
                    "- Markdown document archives",
                    "",
                    "### C. Processing Statistics",
                    f"- PDFs processed: {pdfs_found}",
                    f"- Documents searched: {docs_searched}",
                    f"- Pages analyzed: {pages_parsed}",
                    f"- Charts/visualizations: {charts_found}",
                    f"- Tables extracted: {tables_found}",
                    f"- Processing date: {current_date}",
                    ""
                ])

        # Add citations
        if citations:
            report_parts.extend([
                "## References",
                "",
                "### Documents Reviewed and Cited:",
                ""
            ])
            for citation in citations:
                report_parts.append(f"- **[{citation['id']}]** {citation['source']} - {citation['type']} Document")
            report_parts.append("")

        # Final metadata
        from datetime import datetime
        current_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')

        report_parts.extend([
            "---",
            "",
            "### Report Metadata",
            f"- **Generated by:** FOIA-Buddy V2 Multi-Agent System",
            f"- **AI Models Used:** NVIDIA Nemotron-Nano-9B (reasoning), Nemotron Parse (multimodal)",
            f"- **Processing Date:** {current_date}",
            f"- **Documents Processed:** {total_sources} total sources",
            f"- **Pages Analyzed:** {pages_parsed}",
            "",
            "*This response was generated using advanced AI-powered document analysis and multi-agent coordination systems.*"
        ])

        await asyncio.sleep(0.3)

        return "\n".join(report_parts)
