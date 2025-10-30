"""
Streamlit App for FOIA-Buddy
Interactive web interface for submitting and processing FOIA requests using NVIDIA Nemotron agents.
"""

import streamlit as st
import asyncio
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import tempfile

from foia_buddy.utils import NvidiaClient
from foia_buddy.agents import (
    AgentRegistry,
    CoordinatorAgent,
    DocumentResearcherAgent,
    ReportGeneratorAgent,
    PublicFOIASearchAgent,
    LocalPDFSearchAgent,
    PDFParserAgent,
    HTMLReportGeneratorAgent,
    InteractiveUIGeneratorAgent,
)
from foia_buddy.models import TaskMessage


class StreamlitFOIAProcessor:
    """FOIA processor adapted for Streamlit with real-time UI updates."""

    def __init__(self, nvidia_api_key: str):
        self.nvidia_client = NvidiaClient(nvidia_api_key)
        self.registry = AgentRegistry()
        self._setup_agents()

    def _setup_agents(self):
        """Initialize and register all agents."""
        coordinator = CoordinatorAgent(self.nvidia_client)
        doc_researcher = DocumentResearcherAgent(self.nvidia_client)
        public_foia_search = PublicFOIASearchAgent(self.nvidia_client)
        local_pdf_search = LocalPDFSearchAgent(self.nvidia_client)
        pdf_parser = PDFParserAgent(self.nvidia_client)
        report_generator = ReportGeneratorAgent(self.nvidia_client)
        html_report_generator = HTMLReportGeneratorAgent(self.nvidia_client)
        interactive_ui_generator = InteractiveUIGeneratorAgent(self.nvidia_client)

        self.registry.register(coordinator)
        self.registry.register(doc_researcher)
        self.registry.register(public_foia_search)
        self.registry.register(local_pdf_search)
        self.registry.register(pdf_parser)
        self.registry.register(report_generator)
        self.registry.register(html_report_generator)
        self.registry.register(interactive_ui_generator)

    async def process_foia_request(self, foia_content: str, output_dir: str,
                                   progress_callback=None) -> Dict[str, Any]:
        """
        Process a FOIA request with progress updates to Streamlit UI.

        Args:
            foia_content: The FOIA request text
            output_dir: Output directory for results
            progress_callback: Function to call with progress updates
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {
            "processing_start": time.time(),
            "output_directory": output_dir,
            "agent_results": {},
            "status": "in_progress"
        }

        def update_progress(stage: str, message: str, progress: float = None):
            """Helper to update progress in UI."""
            if progress_callback:
                progress_callback(stage, message, progress)

        try:
            # Step 1: Coordinator
            update_progress("coordinator", "Analyzing FOIA request and creating execution plan...", 0.1)
            coordinator = self.registry.get_agent("coordinator")

            coord_task = TaskMessage(
                task_id="coord_001",
                agent_type="coordinator",
                instructions="Analyze FOIA request and create execution plan",
                context={"foia_request": foia_content}
            )

            coord_result = await coordinator.execute(coord_task)
            results["agent_results"]["coordinator"] = coord_result.dict()

            if not coord_result.success:
                results["status"] = "failed"
                results["error"] = "Coordination failed"
                return results

            update_progress("coordinator", "✅ Coordination complete", 0.2)

            # Step 2: Local PDF Search
            update_progress("local_pdf_search", "Searching local PDF directory...", 0.25)
            local_pdf_search = self.registry.get_agent("local_pdf_search")

            local_pdf_task = TaskMessage(
                task_id="local_pdf_search_001",
                agent_type="local_pdf_search",
                instructions="Search local PDF directory for relevant documents",
                context={
                    "foia_request": foia_content,
                    "coordination_plan": coord_result.data,
                    "max_pdfs": 20
                }
            )

            local_pdf_result = await local_pdf_search.execute(local_pdf_task)
            results["agent_results"]["local_pdf_search"] = local_pdf_result.dict()

            pdf_paths = []
            if local_pdf_result.success:
                pdfs_found = local_pdf_result.data.get('total_pdfs_found', 0)
                pdfs_selected = local_pdf_result.data.get('pdfs_selected', 0)
                update_progress("local_pdf_search",
                              f"✅ Found {pdfs_found} PDFs, selected {pdfs_selected} for parsing", 0.35)
                pdf_paths = local_pdf_result.data.get('pdf_paths', [])
            else:
                update_progress("local_pdf_search", "⚠️ No PDFs found, continuing...", 0.35)

            # Step 3: PDF Parsing
            parse_result = None
            if pdf_paths:
                update_progress("pdf_parser", f"Parsing {len(pdf_paths)} PDFs using NVIDIA Nemotron Parse...", 0.4)
                pdf_parser = self.registry.get_agent("pdf_parser")

                parsed_dir = output_path / "parsed_documents"
                parse_task = TaskMessage(
                    task_id="parse_001",
                    agent_type="pdf_parser",
                    instructions="Parse PDF documents to markdown using VL model",
                    context={
                        "pdf_paths": pdf_paths,
                        "output_dir": str(parsed_dir)
                    }
                )

                parse_result = await pdf_parser.execute(parse_task)
                results["agent_results"]["pdf_parser"] = parse_result.dict()

                if parse_result.success:
                    parsed_count = parse_result.data.get('parsed_count', 0)
                    update_progress("pdf_parser", f"✅ Successfully parsed {parsed_count} PDFs", 0.5)
                else:
                    update_progress("pdf_parser", "⚠️ PDF parsing encountered issues", 0.5)
            else:
                update_progress("pdf_parser", "ℹ️ No PDFs to parse, skipping...", 0.5)

            # Step 4: Document Research
            update_progress("document_researcher", "Researching local document repository...", 0.55)
            doc_researcher = self.registry.get_agent("document_researcher")

            research_task = TaskMessage(
                task_id="research_001",
                agent_type="document_researcher",
                instructions="Search for documents relevant to FOIA request",
                context={
                    "foia_request": foia_content,
                    "coordination_plan": coord_result.data,
                    "local_pdf_results": local_pdf_result.data if local_pdf_result.success else {},
                    "parsed_documents": parse_result.data if parse_result and parse_result.success else {}
                }
            )

            research_result = await doc_researcher.execute(research_task)
            results["agent_results"]["document_researcher"] = research_result.dict()

            if research_result.success:
                docs_found = research_result.data.get('relevant_documents_found', 0)
                update_progress("document_researcher", f"✅ Found {docs_found} relevant documents", 0.7)
            else:
                update_progress("document_researcher", "⚠️ Research encountered issues", 0.7)

            # Step 5: Report Generation
            update_progress("report_generator", "Generating comprehensive FOIA response report...", 0.75)
            report_generator = self.registry.get_agent("report_generator")

            report_task = TaskMessage(
                task_id="report_001",
                agent_type="report_generator",
                instructions="Generate comprehensive FOIA response report",
                context={
                    "foia_request": foia_content,
                    "research_results": research_result.data,
                    "local_pdf_results": local_pdf_result.data if local_pdf_result.success else {},
                    "parsed_pdf_results": parse_result.data if parse_result and parse_result.success else {},
                    "coordination_plan": coord_result.data
                }
            )

            report_result = await report_generator.execute(report_task)
            results["agent_results"]["report_generator"] = report_result.dict()

            if not report_result.success:
                results["status"] = "failed"
                results["error"] = "Report generation failed"
                return results

            update_progress("report_generator", "✅ Report generation complete", 0.9)

            # Step 6: Save outputs
            update_progress("saving", "Saving outputs to disk...", 0.95)
            self._save_outputs(output_path, report_result.data, results)

            # Generate HTML report
            html_generator = self.registry.get_agent("html_report_generator")
            metadata_path = output_path / "processing_metadata.json"
            html_output_path = output_path / "processing_report.html"

            html_task = TaskMessage(
                task_id="html_report_001",
                agent_type="html_report_generator",
                instructions="Generate interactive HTML report from processing metadata",
                context={
                    "metadata_path": str(metadata_path),
                    "output_path": str(html_output_path)
                }
            )

            html_result = await html_generator.execute(html_task)
            results["agent_results"]["html_report_generator"] = html_result.dict()

            # Generate interactive UI
            ui_generator = self.registry.get_agent("interactive_ui_generator")
            ui_task = TaskMessage(
                task_id="interactive_ui_001",
                agent_type="interactive_ui_generator",
                instructions="Generate interactive tabbed UI",
                context={
                    "output_dir": str(output_path),
                    "input_file": None,  # Using direct content, not file
                    "auto_open": False
                }
            )

            ui_result = await ui_generator.execute(ui_task)
            results["agent_results"]["interactive_ui_generator"] = ui_result.dict()

            results["status"] = "completed"
            results["processing_time"] = time.time() - results["processing_start"]

            update_progress("complete", "🎉 Processing complete!", 1.0)
            return results

        except Exception as e:
            results["error"] = str(e)
            results["status"] = "failed"
            update_progress("error", f"❌ Error: {str(e)}", 1.0)
            return results

    def _save_outputs(self, output_path: Path, report_data: Dict[str, Any], results: Dict[str, Any]):
        """Save all outputs to the specified directory."""
        # Save main report
        report_file = output_path / "final_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_data.get("report_content", "No report content generated"))

        # Save executive summary
        summary_file = output_path / "executive_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(report_data.get("executive_summary", "No summary available"))

        # Save compliance notes
        compliance_file = output_path / "compliance_notes.md"
        with open(compliance_file, 'w', encoding='utf-8') as f:
            f.write(report_data.get("compliance_notes", "No compliance notes"))

        # Save processing metadata
        metadata_file = output_path / "processing_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        # Save redaction flags if any
        if report_data.get("redaction_flags"):
            redaction_file = output_path / "redaction_review.txt"
            with open(redaction_file, 'w', encoding='utf-8') as f:
                f.write("REDACTION REVIEW REQUIRED\n")
                f.write("=" * 30 + "\n\n")
                for flag in report_data["redaction_flags"]:
                    f.write(f"- {flag}\n")


# Streamlit UI
def main():
    st.set_page_config(
        page_title="FOIA-Buddy Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #76B900;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background-color: #76B900;
    }
    .agent-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<div class="main-header">🤖 FOIA-Buddy Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent FOIA Request Processing with NVIDIA Nemotron Agents</div>',
                unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key input
        api_key = st.text_input(
            "NVIDIA API Key",
            type="password",
            value=os.environ.get("NVIDIA_API_KEY", ""),
            help="Enter your NVIDIA API key or set NVIDIA_API_KEY environment variable"
        )

        if not api_key:
            st.error("⚠️ API key required to process requests")
        else:
            st.success("✅ API key configured")

        st.divider()

        # Output directory
        default_output = os.path.join(os.getcwd(), "output", f"response-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        output_dir = st.text_input(
            "Output Directory",
            value=default_output,
            help="Directory where results will be saved"
        )

        st.divider()

        # Agent Status Display
        st.header("🤖 Agent Architecture")
        st.markdown("""
        **Active Agents:**
        - 🎯 Coordinator Agent
        - 📁 Local PDF Search Agent
        - 📄 PDF Parser Agent
        - 📚 Document Researcher Agent
        - 📝 Report Generator Agent
        - 🎨 HTML Report Generator
        - 🚀 Interactive UI Generator
        """)

        st.divider()

        # Model info
        st.header("🧠 NVIDIA Models")
        st.markdown("""
        **Reasoning & Coordination:**
        - `nvidia-nemotron-nano-9b-v2`

        **Document Parsing:**
        - `nvidia/nemotron-parse`
        """)

    # Initialize active tab in session state
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "📝 Submit Request"

    # Auto-switch to processing tab if processing started
    if st.session_state.get('processing', False) and st.session_state.active_tab == "📝 Submit Request":
        st.session_state.active_tab = "📊 Processing Status"

    # Tab selector
    selected_tab = st.radio(
        "Navigation",
        ["📝 Submit Request", "📊 Processing Status", "📄 View Results"],
        index=["📝 Submit Request", "📊 Processing Status", "📄 View Results"].index(st.session_state.active_tab),
        horizontal=True,
        label_visibility="collapsed"
    )

    st.session_state.active_tab = selected_tab
    st.divider()

    # Tab 1: Submit Request
    if selected_tab == "📝 Submit Request":
        st.header("Submit FOIA Request")

        # Request input method
        input_method = st.radio(
            "Choose input method:",
            ["Text Input", "File Upload"],
            horizontal=True
        )

        foia_content = None

        if input_method == "Text Input":
            foia_content = st.text_area(
                "Enter your FOIA request:",
                height=300,
                placeholder="# FOIA Request\n\nPursuant to the Freedom of Information Act...",
                help="Enter your FOIA request in markdown format"
            )
        else:
            uploaded_file = st.file_uploader(
                "Upload FOIA request file",
                type=["md", "txt"],
                help="Upload a markdown or text file containing your FOIA request"
            )
            if uploaded_file:
                foia_content = uploaded_file.read().decode('utf-8')
                st.text_area("File content preview:", value=foia_content[:500] + "...", height=200, disabled=True)

        # Requester information
        col1, col2 = st.columns(2)
        with col1:
            requester_name = st.text_input("Your Name (optional)")
        with col2:
            requester_email = st.text_input("Your Email (optional)")

        # Submit button
        if st.button("🚀 Process FOIA Request", type="primary", disabled=not (api_key and foia_content)):
            if foia_content:
                # Store in session state
                st.session_state.processing = True
                st.session_state.foia_content = foia_content
                st.session_state.output_dir = output_dir
                st.session_state.api_key = api_key
                st.session_state.active_tab = "📊 Processing Status"  # Switch to processing tab
                st.rerun()
            else:
                st.error("Please enter a FOIA request before submitting")

    # Tab 2: Processing Status
    elif selected_tab == "📊 Processing Status":
        st.header("Real-Time Processing Status")

        if st.session_state.get('processing', False):
            # Create progress tracking UI
            progress_bar = st.progress(0)
            status_text = st.empty()
            agent_status = st.empty()

            # Create processor
            processor = StreamlitFOIAProcessor(st.session_state.api_key)

            # Progress tracking
            progress_data = {
                'current_agent': '',
                'message': '',
                'progress': 0.0
            }

            def update_progress(stage, message, progress):
                progress_data['current_agent'] = stage
                progress_data['message'] = message
                progress_data['progress'] = progress or 0.0
                progress_bar.progress(progress_data['progress'])
                status_text.markdown(f"**Current Stage:** `{stage}`")
                agent_status.info(message)

            # Process the request
            try:
                results = asyncio.run(
                    processor.process_foia_request(
                        st.session_state.foia_content,
                        st.session_state.output_dir,
                        progress_callback=update_progress
                    )
                )

                # Store results
                st.session_state.results = results
                st.session_state.processing = False

                # Show completion
                if results.get('status') == 'completed':
                    st.balloons()
                    st.markdown('<div class="success-box">✅ <b>Processing Complete!</b><br/>Your FOIA response has been generated successfully.</div>',
                               unsafe_allow_html=True)
                    st.success(f"Processing time: {results.get('processing_time', 0):.2f} seconds")
                    st.info(f"📁 Results saved to: `{st.session_state.output_dir}`")
                else:
                    st.markdown(f'<div class="error-box">❌ <b>Processing Failed</b><br/>{results.get("error", "Unknown error")}</div>',
                               unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Fatal error: {str(e)}")
                st.session_state.processing = False

        elif st.session_state.get('results'):
            results = st.session_state.results
            st.success("✅ Latest processing completed successfully")

            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", results.get('status', 'Unknown').upper())
            with col2:
                st.metric("Processing Time", f"{results.get('processing_time', 0):.2f}s")
            with col3:
                agent_count = len(results.get('agent_results', {}))
                st.metric("Agents Used", agent_count)
            with col4:
                output_path = Path(results.get('output_directory', ''))
                file_count = len(list(output_path.glob('*'))) if output_path.exists() else 0
                st.metric("Files Generated", file_count)

            # Agent execution timeline
            st.subheader("📋 Agent Execution Timeline")
            for agent_name, agent_result in results.get('agent_results', {}).items():
                with st.expander(f"🤖 {agent_name.replace('_', ' ').title()}", expanded=False):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        success = agent_result.get('success', False)
                        st.markdown(f"**Status:** {'✅ Success' if success else '❌ Failed'}")
                        st.markdown(f"**Task ID:** `{agent_result.get('task_id', 'N/A')}`")
                    with col2:
                        st.json(agent_result.get('data', {}))
        else:
            st.info("👈 Submit a FOIA request in the 'Submit Request' tab to begin processing")

    # Tab 3: View Results
    elif selected_tab == "📄 View Results":
        st.header("Generated Reports & Documents")

        if st.session_state.get('results'):
            output_dir = st.session_state.results.get('output_directory', '')
            output_path = Path(output_dir)

            if output_path.exists():
                # Quick links
                st.subheader("📎 Quick Access")
                col1, col2, col3 = st.columns(3)

                html_report = output_path / "processing_report.html"
                interactive_viewer = output_path / "interactive_viewer.html"

                with col1:
                    if html_report.exists():
                        st.markdown(f"[🎨 View Processing Report]({html_report.as_uri()})")
                with col2:
                    if interactive_viewer.exists():
                        st.markdown(f"[🚀 Open Interactive Viewer]({interactive_viewer.as_uri()})")
                with col3:
                    st.markdown(f"[📁 Open Output Folder](file://{output_path.absolute()})")

                st.divider()

                # Display main documents
                st.subheader("📄 Generated Documents")

                # Final Report
                final_report = output_path / "final_report.md"
                if final_report.exists():
                    with st.expander("📝 Final FOIA Response Report", expanded=True):
                        with open(final_report, 'r', encoding='utf-8') as f:
                            st.markdown(f.read())

                # Executive Summary
                exec_summary = output_path / "executive_summary.md"
                if exec_summary.exists():
                    with st.expander("📊 Executive Summary"):
                        with open(exec_summary, 'r', encoding='utf-8') as f:
                            st.markdown(f.read())

                # Compliance Notes
                compliance = output_path / "compliance_notes.md"
                if compliance.exists():
                    with st.expander("⚖️ Compliance Notes"):
                        with open(compliance, 'r', encoding='utf-8') as f:
                            st.markdown(f.read())

                # Redaction Review
                redaction = output_path / "redaction_review.txt"
                if redaction.exists():
                    with st.expander("🔒 Redaction Review", expanded=True):
                        with open(redaction, 'r', encoding='utf-8') as f:
                            st.text(f.read())

                st.divider()

                # Parsed documents
                parsed_dir = output_path / "parsed_documents"
                if parsed_dir.exists():
                    st.subheader("📚 Parsed PDF Documents")
                    parsed_files = list(parsed_dir.glob("*.md"))

                    if parsed_files:
                        st.info(f"Found {len(parsed_files)} parsed documents")
                        selected_doc = st.selectbox(
                            "Select a document to view:",
                            parsed_files,
                            format_func=lambda x: x.name
                        )

                        if selected_doc:
                            with st.expander(f"📄 {selected_doc.name}", expanded=True):
                                with open(selected_doc, 'r', encoding='utf-8') as f:
                                    st.markdown(f.read())
                    else:
                        st.info("No parsed documents available")

                st.divider()

                # Download section
                st.subheader("⬇️ Download Results")

                # Create download buttons for key files
                col1, col2, col3 = st.columns(3)

                with col1:
                    if final_report.exists():
                        with open(final_report, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="📥 Download Final Report",
                                data=f.read(),
                                file_name="final_report.md",
                                mime="text/markdown"
                            )

                with col2:
                    metadata_file = output_path / "processing_metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="📥 Download Metadata",
                                data=f.read(),
                                file_name="processing_metadata.json",
                                mime="application/json"
                            )

                with col3:
                    if exec_summary.exists():
                        with open(exec_summary, 'r', encoding='utf-8') as f:
                            st.download_button(
                                label="📥 Download Summary",
                                data=f.read(),
                                file_name="executive_summary.md",
                                mime="text/markdown"
                            )
            else:
                st.error(f"Output directory not found: {output_dir}")
        else:
            st.info("👈 No results available. Submit a FOIA request in the 'Submit Request' tab")

    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 2rem 0;">
        <p>Built with ❤️ for the NVIDIA AI Agents Hackathon</p>
        <p>Powered by <b>NVIDIA Nemotron</b> • Multi-Agent Architecture • ReAct Patterns</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
