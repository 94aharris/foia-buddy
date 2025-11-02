"""
FOIA-Buddy V2 - Demo-Optimized Streamlit Application
Real-time multi-agent AI coordination for FOIA request processing.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path to enable proper imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import streamlit as st
import asyncio
import time
from datetime import datetime
import logging

# Configure logging for server-side visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    GRAY = '\033[90m'
    MAGENTA = '\033[35m'
    YELLOW = '\033[33m'

# Import our modules
from models.state import ApplicationState
from models.messages import TaskMessage, AgentStatus
from utils.nvidia_client import NvidiaClient
from agents.coordinator import CoordinatorAgent
from agents.pdf_searcher import PDFSearcherAgent
from agents.pdf_parser import PDFParserAgent
from agents.document_researcher import DocumentResearcherAgent
from agents.report_generator import ReportGeneratorAgent
from ui.theme import apply_nvidia_theme, NVIDIA_GREEN
from ui.components import (
    render_agent_status_card,
    render_reasoning_stream,
    render_live_metrics,
    render_decision_point,
    render_agent_coordination_status,
    render_phase_header,
    render_sidebar_status
)
from ui.visualizations import (
    create_coordination_flow_diagram,
    create_metrics_timeline,
    create_full_workflow_graph
)


# Page configuration
st.set_page_config(
    page_title="FOIA-Buddy V2 - Multi-Agent Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply NVIDIA theme
apply_nvidia_theme()


# Demo scenarios
DEMO_SCENARIOS = {
    "AI Policy Documents": {
        "request": """# FOIA Request: AI Policy Documents 2023-2024

Pursuant to the Freedom of Information Act, I request:
1. All internal documents related to AI policy development
2. Budget allocations for AI initiatives
3. Email communications regarding AI ethics guidelines""",
        "topics": ["AI policy", "budget data", "ethics guidelines"],
        "estimated_time": "2-3 minutes"
    },
    "Budget Transparency": {
        "request": """# FOIA Request: Department Budget Breakdown

I request all documents showing:
1. Annual budget allocations by program
2. Contracts over $100,000
3. Spending reports for Q3-Q4 2023""",
        "topics": ["budget allocations", "contracts", "spending reports"],
        "estimated_time": "1-2 minutes"
    },
    "Communications Records": {
        "request": """# FOIA Request: Leadership Communications

I request:
1. Meeting minutes from executive team meetings
2. External communications with partner organizations
3. Policy briefing documents""",
        "topics": ["meeting minutes", "communications", "policy briefings"],
        "estimated_time": "2-3 minutes"
    }
}


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'app_state' not in st.session_state:
        st.session_state.app_state = ApplicationState()

    if 'nvidia_client' not in st.session_state:
        st.session_state.nvidia_client = None

    if 'agents_initialized' not in st.session_state:
        st.session_state.agents_initialized = False

    if 'processing' not in st.session_state:
        st.session_state.processing = False

    if 'processing_step' not in st.session_state:
        st.session_state.processing_step = -1


def log_agent_event(agent_name: str, event_type: str, message, state=None):
    """
    Log agent events to terminal with color coding for visibility.
    Also adds to UI activity log if state is provided.
    """
    # Choose color based on event type
    if event_type in ["active", "thinking", "planning", "executing"]:
        color = Colors.OKCYAN
        icon = "🔵"
    elif event_type == "complete":
        color = Colors.OKGREEN
        icon = "✅"
    elif event_type == "error":
        color = Colors.FAIL
        icon = "❌"
    elif event_type in ["decision", "insight"]:
        color = Colors.MAGENTA
        icon = "🎯"
    elif event_type == "phase":
        color = Colors.YELLOW + Colors.BOLD
        icon = "📊"
    elif event_type == "agent_handoff":
        color = Colors.HEADER
        icon = "🔄"
    elif event_type == "reasoning":
        color = Colors.OKBLUE
        icon = "🧠"
    else:
        color = Colors.ENDC
        icon = "ℹ️"

    # Format the message
    msg_str = str(message)
    if hasattr(message, 'from_agent'):  # Agent handoff object
        msg_str = f"{message.from_agent} → {message.to_agent}: {message.task}"

    # Truncate long messages for cleaner output
    truncated_msg = msg_str
    if event_type == "reasoning" and len(msg_str) > 150:
        truncated_msg = msg_str[:150] + "..."

    # Log to terminal with color
    log_line = f"{color}{icon} [{agent_name:20s}] {event_type:15s} │ {truncated_msg}{Colors.ENDC}"
    logger.info(log_line)

    # Add to UI activity log (keep original message, not truncated)
    if state is not None:
        # Log most event types for visibility (avoid only very verbose ones)
        if event_type not in ["progress"]:  # Exclude only progress updates to reduce noise
            state.add_activity_log(agent_name, event_type, msg_str, icon)


def create_ui_callback(state: ApplicationState):
    """
    Create a callback function for agents to update UI state.
    Also logs all events to terminal for server-side visibility.
    """
    def callback(agent_name: str, event_type: str, message):
        # Log to terminal and UI activity log
        log_agent_event(agent_name, event_type, message, state)
        # Update agent status
        if agent_name not in state.agent_statuses:
            state.agent_statuses[agent_name] = AgentStatus(
                name=agent_name,
                status="idle"
            )

        agent_status = state.agent_statuses[agent_name]

        # Handle different event types
        if event_type in ["active", "thinking", "planning", "executing", "reflecting", "complete", "error"]:
            agent_status.status = event_type
            agent_status.current_task = str(message)

        elif event_type == "progress":
            agent_status.current_task = str(message)
            # Estimate progress
            if "1/" in str(message) or "Step 1" in str(message):
                agent_status.progress = 0.25
            elif "2/" in str(message) or "Step 2" in str(message):
                agent_status.progress = 0.5
            elif "3/" in str(message) or "Step 3" in str(message):
                agent_status.progress = 0.75
            elif "4/" in str(message) or "Step 4" in str(message) or "5/" in str(message):
                agent_status.progress = 0.9

        elif event_type == "reasoning":
            # Complete reasoning message (no longer streaming)
            state.add_reasoning(str(message))

        elif event_type in ["decision", "insight", "result"]:
            state.add_reasoning(f"[{agent_name}] {str(message)}")

        elif event_type == "agent_handoff":
            # Handle agent handoff - message is an AgentHandoff object
            if hasattr(message, 'from_agent'):
                state.add_handoff(message)
                state.add_reasoning(f"🔄 Handoff: {message.from_agent} → {message.to_agent}")

        elif event_type == "metric":
            # Parse metric updates
            if "Found" in str(message) and "PDFs" in str(message):
                try:
                    num = int(str(message).split("Found ")[1].split(" ")[0])
                    state.update_metric("pdfs_found", num)
                except:
                    pass

        elif event_type == "phase":
            state.add_reasoning(f"\n=== {str(message)} ===\n")

        # Update current agent
        if event_type in ["active", "thinking", "executing"]:
            state.current_agent = agent_name

        # Add timeline event (only for non-handoff events to avoid duplicates)
        if event_type != "agent_handoff":
            state.timeline_events.append({
                "agent": agent_name,
                "action": str(message),
                "timestamp": datetime.now().isoformat()
            })

        agent_status.last_updated = datetime.now().isoformat()

    return callback


def process_foia_request_sync(foia_request: str, topics: list, nvidia_client: NvidiaClient, state: ApplicationState, step: int):
    """
    Process FOIA request step by step for progressive UI updates.
    Returns the next step number or -1 when complete.
    """

    # Create UI callback
    ui_callback = create_ui_callback(state)

    # Initialize agents (store in session state to persist)
    if 'agents' not in st.session_state:
        coordinator = CoordinatorAgent(nvidia_client)
        pdf_searcher = PDFSearcherAgent(nvidia_client)
        pdf_parser = PDFParserAgent(nvidia_client)
        researcher = DocumentResearcherAgent(nvidia_client)
        report_gen = ReportGeneratorAgent(nvidia_client)

        coordinator.agents = {
            "PDFSearcher": pdf_searcher,
            "PDFParser": pdf_parser,
            "DocumentResearcher": researcher,
            "ReportGenerator": report_gen
        }

        st.session_state.agents = {
            "coordinator": coordinator,
            "pdf_searcher": pdf_searcher,
            "pdf_parser": pdf_parser,
            "researcher": researcher,
            "report_gen": report_gen
        }

    agents = st.session_state.agents

    # Execute based on current step
    if step == 0:
        # Step 0: Coordinator analysis
        coordinator_task = TaskMessage(
            task_id="foia_001",
            agent_name="Coordinator",
            instructions="Process this FOIA request using multi-agent coordination",
            context={"foia_request": foia_request, "topics": topics}
        )
        result = asyncio.run(agents["coordinator"].execute_with_streaming(coordinator_task, ui_callback))
        return 1 if result.success else -1

    elif step == 1:
        # Step 1: PDF Searcher
        pdf_task = TaskMessage(
            task_id="foia_001_pdf",
            agent_name="PDFSearcher",
            instructions="Search for relevant PDFs",
            context={"topics": topics}
        )
        pdf_result = asyncio.run(agents["pdf_searcher"].execute_with_streaming(pdf_task, ui_callback))
        if pdf_result.success:
            state.update_metric("docs_scanned", pdf_result.data.get("total_scanned", 23))
            state.update_metric("pdfs_found", pdf_result.data.get("pdfs_found", 8))
            st.session_state.pdf_result = pdf_result
            return 2
        return -1

    elif step == 2:
        # Step 2: PDF Parser
        parser_task = TaskMessage(
            task_id="foia_001_parse",
            agent_name="PDFParser",
            instructions="Parse discovered PDFs",
            context={"relevant_pdfs": st.session_state.get("pdf_result", {}).data.get("relevant_pdfs", [])}
        )
        parser_result = asyncio.run(agents["pdf_parser"].execute_with_streaming(parser_task, ui_callback))
        if parser_result.success:
            state.update_metric("pages_parsed", parser_result.data.get("total_pages", 142))
            st.session_state.parser_result = parser_result
            return 3
        return -1

    elif step == 3:
        # Step 3: Document Researcher
        research_task = TaskMessage(
            task_id="foia_001_research",
            agent_name="DocumentResearcher",
            instructions="Research additional documents",
            context={"topics": topics}
        )
        research_result = asyncio.run(agents["researcher"].execute_with_streaming(research_task, ui_callback))
        if research_result.success:
            st.session_state.research_result = research_result
            return 4
        return -1

    elif step == 4:
        # Step 4: Report Generator
        report_task = TaskMessage(
            task_id="foia_001_report",
            agent_name="ReportGenerator",
            instructions="Generate comprehensive FOIA response",
            context={
                "topics": topics,
                "all_data": {
                    "pdf_results": st.session_state.get("pdf_result", {}).data if hasattr(st.session_state.get("pdf_result", {}), 'data') else {},
                    "parser_results": st.session_state.get("parser_result", {}).data if hasattr(st.session_state.get("parser_result", {}), 'data') else {},
                    "research_results": st.session_state.get("research_result", {}).data if hasattr(st.session_state.get("research_result", {}), 'data') else {}
                }
            }
        )
        report_result = asyncio.run(agents["report_gen"].execute_with_streaming(report_task, ui_callback))
        if report_result.success:
            state.final_report = report_result.data.get("final_report", "")

        # Mark all as complete
        for agent_name in state.agent_statuses:
            state.agent_statuses[agent_name].status = "complete"
            state.agent_statuses[agent_name].progress = 1.0

        state.is_processing = False
        return -1  # Done

    return -1  # Shouldn't reach here


def main():
    """Main application."""

    # Print startup banner to terminal
    if 'startup_logged' not in st.session_state:
        logger.info(f"{Colors.OKGREEN}{Colors.BOLD}")
        logger.info("=" * 80)
        logger.info("🤖 FOIA-BUDDY V2 - Multi-Agent FOIA Processing System")
        logger.info("   Real-time agent coordination with NVIDIA Nemotron")
        logger.info("=" * 80)
        logger.info(f"{Colors.ENDC}")
        logger.info(f"{Colors.OKCYAN}Server started. All agent activity will be logged below.{Colors.ENDC}")
        logger.info("")
        st.session_state.startup_logged = True

    initialize_session_state()
    state = st.session_state.app_state

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        # <span style="color: {NVIDIA_GREEN};">🤖 FOIA-Buddy V2</span>
        ### Real-Time Multi-Agent FOIA Processing
        """, unsafe_allow_html=True)
    with col2:
        st.image("https://www.nvidia.com/content/dam/en-zz/Solutions/about-nvidia/logo-and-brand/01-nvidia-logo-vert-500x200-2c50-d@2x.png", width=150)

    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        # API Key input
        api_key = st.text_input(
            "NVIDIA API Key",
            type="password",
            value=os.getenv("NVIDIA_API_KEY", ""),
            help="Enter your NVIDIA API key"
        )

        if api_key:
            if st.session_state.nvidia_client is None:
                st.session_state.nvidia_client = NvidiaClient(api_key)
                st.success("✅ API key configured")
        else:
            st.warning("⚠️ Please enter your NVIDIA API key")

        st.markdown("---")

        # Demo scenario selector
        st.markdown("## 📋 Demo Scenarios")
        scenario_name = st.selectbox(
            "Select a scenario",
            list(DEMO_SCENARIOS.keys())
        )

        if st.button("🎲 Load Scenario"):
            scenario = DEMO_SCENARIOS[scenario_name]
            st.session_state.selected_request = scenario["request"]
            st.session_state.selected_topics = scenario["topics"]
            st.rerun()

        st.markdown("---")

        # Live Activity Log in sidebar
        st.markdown("## 📋 Live Activity Log")

        if state.activity_log:
            st.caption(f"{len(state.activity_log)} events")

            # Show most recent 15 log entries in reverse (newest first)
            recent_logs = state.activity_log[-15:]
            recent_logs.reverse()

            for log_entry in recent_logs:
                agent = log_entry['agent']
                event = log_entry['event']
                message = log_entry['message']
                icon = log_entry['icon']

                # Truncate for sidebar
                display_msg = message
                if len(message) > 60:
                    display_msg = message[:60] + "..."

                st.markdown(f"{icon} **{agent}**")
                st.caption(f"_{event}_ · {display_msg}")
                st.markdown("")  # Add spacing
        else:
            st.info("⏳ Waiting for activity...")

        st.markdown("---")

        # Status display
        if state.agent_statuses:
            render_sidebar_status(state.agent_statuses, state.metrics)

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("FOIA-Buddy V2 demonstrates advanced multi-agent AI coordination using NVIDIA Nemotron models.")
        st.markdown(f"**Models Used:**\n- Nemotron-Nano-9B (reasoning)\n- Nemotron Parse (multimodal)")

    # Main area
    st.markdown("---")

    # FOIA Request Input
    st.markdown("## 📝 FOIA Request Input")

    request_text = st.text_area(
        "Enter your FOIA request",
        value=st.session_state.get("selected_request", DEMO_SCENARIOS["AI Policy Documents"]["request"]),
        height=150,
        help="Enter the FOIA request text or load a demo scenario"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        process_button = st.button(
            "🚀 Process Request",
            disabled=state.is_processing or not api_key,
            type="primary"
        )
    with col2:
        if state.is_processing:
            st.info("⏳ Processing in progress...")

    # Process request
    if process_button and not state.is_processing:
        state.reset()
        state.is_processing = True
        state.foia_request = request_text
        st.session_state.processing_step = 0
        st.session_state.selected_topics = st.session_state.get("selected_topics", ["AI policy", "budget data", "ethics guidelines"])

        # Log processing start to terminal
        logger.info("")
        logger.info(f"{Colors.YELLOW}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        logger.info(f"{Colors.YELLOW}{Colors.BOLD}🚀 NEW FOIA REQUEST PROCESSING STARTED{Colors.ENDC}")
        logger.info(f"{Colors.YELLOW}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
        logger.info(f"{Colors.OKBLUE}Request: {request_text[:100]}...{Colors.ENDC}")
        logger.info(f"{Colors.OKBLUE}Topics: {', '.join(st.session_state.selected_topics)}{Colors.ENDC}")
        logger.info("")

        st.rerun()

    # Continue processing if in progress
    if state.is_processing and st.session_state.processing_step >= 0:
        topics = st.session_state.get("selected_topics", ["AI policy", "budget data", "ethics guidelines"])

        next_step = process_foia_request_sync(
            request_text,
            topics,
            st.session_state.nvidia_client,
            state,
            st.session_state.processing_step
        )

        st.session_state.processing_step = next_step

        if next_step >= 0:
            # More steps to process, trigger rerun
            time.sleep(0.5)  # Small delay to see the update
            st.rerun()
        else:
            # Processing complete
            st.session_state.processing_step = -1

            # Log completion to terminal
            logger.info("")
            logger.info(f"{Colors.OKGREEN}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
            logger.info(f"{Colors.OKGREEN}{Colors.BOLD}✅ FOIA REQUEST PROCESSING COMPLETED{Colors.ENDC}")
            logger.info(f"{Colors.OKGREEN}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
            logger.info(f"{Colors.OKGREEN}Total execution time: {state.metrics.get('execution_time', 0):.2f}s{Colors.ENDC}")
            logger.info(f"{Colors.OKGREEN}API calls made: {state.metrics.get('api_calls', 0)}{Colors.ENDC}")
            logger.info(f"{Colors.OKGREEN}Documents processed: {state.metrics.get('docs_scanned', 0)}{Colors.ENDC}")
            logger.info("")

    # Display processing status
    if state.is_processing or state.agent_statuses:
        st.markdown("---")

        # Agent coordination status
        agent_order = ["Coordinator", "PDFSearcher", "PDFParser", "DocumentResearcher", "ReportGenerator"]
        render_agent_coordination_status(state.agent_statuses, agent_order)

        st.markdown("---")

        # Final report
        if state.final_report:
            st.markdown("---")
            st.markdown("## 📄 Final FOIA Response")

            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                "📋 Full Report",
                "📊 Executive Summary",
                "🎭 Agent Status",
                "🧠 Agent Reasoning",
                "🔄 Coordination Flow",
                "⏱️ Execution Timeline",
                "📈 Workflow Graph",
                "💾 Download"
            ])

            with tab1:
                st.markdown(state.final_report)

            with tab2:
                # Extract executive summary
                if "EXECUTIVE SUMMARY" in state.final_report:
                    summary_start = state.final_report.find("EXECUTIVE SUMMARY")
                    summary_end = state.final_report.find("---", summary_start)
                    summary = state.final_report[summary_start:summary_end]
                    st.markdown(summary)
                else:
                    st.info("Executive summary not available")

            with tab3:
                # Agent Status
                st.markdown("### 🎭 Agent Status")
                for agent_name in agent_order:
                    if agent_name in state.agent_statuses:
                        render_agent_status_card(state.agent_statuses[agent_name])

            with tab4:
                # Agent Reasoning
                render_reasoning_stream(state.reasoning_stream, max_display=50)

            with tab5:
                # Coordination Flow
                st.markdown("### 🔄 Agent Coordination Flow")
                flow_fig = create_coordination_flow_diagram(
                    state.agent_statuses,
                    agent_order,
                    state.agent_handoffs
                )
                st.plotly_chart(flow_fig, width='stretch')

                # Add decision points
                if state.decision_points:
                    st.markdown("### 🎯 Agent Decisions")
                    for decision in state.decision_points:
                        render_decision_point(decision)

            with tab6:
                # Execution Timeline
                if state.timeline_events:
                    st.markdown("### ⏱️ Execution Timeline")
                    timeline_fig = create_metrics_timeline(state.timeline_events)
                    st.plotly_chart(timeline_fig, width='stretch')

                    # Add metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Events", len(state.timeline_events))
                    with col2:
                        st.metric("Active Agents", len(state.agent_statuses))
                    with col3:
                        st.metric("API Calls", state.metrics.get('api_calls', 0))
                else:
                    st.info("Timeline will appear after processing begins")

            with tab7:
                # Display comprehensive workflow graph
                st.markdown("### Complete Multi-Agent Workflow Graph")
                st.markdown("""
                This graph shows the complete execution flow of all agents involved in processing your FOIA request.
                - **Nodes** represent individual agents with their status
                - **Connections** show the flow of information between agents
                - **Stars** indicate task activities performed by each agent
                - **Progress rings** show completion status
                """)

                workflow_fig = create_full_workflow_graph(
                    state.agent_statuses,
                    agent_order,
                    state.timeline_events,
                    state.agent_handoffs
                )
                st.plotly_chart(workflow_fig, width='stretch')

                # Add summary statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Agents Deployed", len(state.agent_statuses))
                with col2:
                    completed_agents = sum(1 for s in state.agent_statuses.values() if s.status == "complete")
                    st.metric("Completed", completed_agents)
                with col3:
                    st.metric("Total Tasks", len(state.timeline_events))
                with col4:
                    st.metric("Handoffs", len(state.agent_handoffs))

            with tab8:
                st.download_button(
                    label="📥 Download Report (Markdown)",
                    data=state.final_report,
                    file_name=f"foia_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )

    else:
        # Welcome screen
        st.info("""
        👋 **Welcome to FOIA-Buddy V2!**

        This demo showcases advanced multi-agent AI coordination for FOIA request processing.

        **To get started:**
        1. Enter your NVIDIA API key in the sidebar
        2. Select a demo scenario or enter your own FOIA request
        3. Click "🚀 Process Request" to see the agents in action!

        **What you'll see:**
        - Real-time agent reasoning and decision-making
        - Live coordination between specialized agents
        - Visual document understanding with Nemotron Parse
        - Comprehensive FOIA response generation
        """)


if __name__ == "__main__":
    main()
