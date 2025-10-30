"""
Reusable Streamlit UI components for demo visualization.
"""

import streamlit as st
from typing import Dict, Any, List
from models.messages import AgentStatus, DecisionPoint
from ui.theme import get_status_emoji, get_status_color, NVIDIA_GREEN


def render_agent_status_card(agent_status: AgentStatus):
    """
    Render an agent status card showing current state and progress.
    """

    status_emoji = get_status_emoji(agent_status.status)
    status_color = get_status_color(agent_status.status)

    card_class = "agent-card-active" if agent_status.status in ["active", "thinking", "executing"] else "agent-card"

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: {NVIDIA_GREEN};">{status_emoji} {agent_status.name}</h3>
                <p style="margin: 0.5rem 0; color: {status_color}; font-weight: bold;">
                    {agent_status.status.upper()}
                </p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; font-size: 2em; color: {status_color};">
                    {int(agent_status.progress * 100)}%
                </p>
            </div>
        </div>
        <p style="margin: 0.5rem 0; color: #CCCCCC;">
            {agent_status.current_task or "Waiting..."}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show progress bar
    if agent_status.progress > 0 and agent_status.status not in ["complete", "error"]:
        st.progress(agent_status.progress)


def render_reasoning_stream(reasoning_tokens: List[str], max_display: int = 20):
    """
    Render live reasoning stream with color-coded tokens.
    """

    st.markdown("### 🧠 Agent Reasoning (Live)")

    # Create scrollable container
    if reasoning_tokens:
        # Show most recent tokens
        recent_tokens = reasoning_tokens[-max_display:]

        for token in recent_tokens:
            # Classify token type and apply styling
            if "analyzing" in token.lower() or "analysis" in token.lower():
                st.markdown(f'<div class="reasoning-token">🔵 <strong>Analysis:</strong> {token}</div>', unsafe_allow_html=True)
            elif "planning" in token.lower() or "plan" in token.lower():
                st.markdown(f'<div class="reasoning-token">🟢 <strong>Planning:</strong> {token}</div>', unsafe_allow_html=True)
            elif "executing" in token.lower() or "action" in token.lower():
                st.markdown(f'<div class="reasoning-token">🟡 <strong>Action:</strong> {token}</div>', unsafe_allow_html=True)
            elif "reflecting" in token.lower() or "evaluation" in token.lower():
                st.markdown(f'<div class="reasoning-token">🟣 <strong>Reflection:</strong> {token}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="reasoning-token">💭 {token}</div>', unsafe_allow_html=True)
    else:
        st.info("Waiting for agent reasoning to begin...")


def render_live_metrics(metrics: Dict[str, Any]):
    """
    Render animated metric cards with real-time updates.
    """

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📄 Documents Scanned",
            value=metrics.get("docs_scanned", 0),
            delta=metrics.get("docs_scanned_delta", 0) if metrics.get("docs_scanned_delta", 0) != 0 else None
        )

    with col2:
        st.metric(
            label="🔍 PDFs Found",
            value=metrics.get("pdfs_found", 0),
            delta=metrics.get("pdfs_found_delta", 0) if metrics.get("pdfs_found_delta", 0) != 0 else None
        )

    with col3:
        st.metric(
            label="📊 Pages Parsed",
            value=metrics.get("pages_parsed", 0),
            delta=metrics.get("pages_parsed_delta", 0) if metrics.get("pages_parsed_delta", 0) != 0 else None
        )

    with col4:
        st.metric(
            label="🎯 Agent Decisions",
            value=metrics.get("decisions_made", 0),
            delta=metrics.get("decisions_delta", 0) if metrics.get("decisions_delta", 0) != 0 else None
        )


def render_decision_point(decision: DecisionPoint):
    """
    Render a decision point with reasoning and options.
    """

    with st.expander(f"🎯 {decision.agent_name} Decision: {decision.decision}"):
        st.markdown(f"**Reasoning:** {decision.reasoning}")

        st.markdown("**Options Considered:**")
        for option in decision.options_considered:
            if option == decision.decision:
                st.markdown(f"✅ {option} ← **Selected**")
            else:
                st.markdown(f"⚪ {option}")

        if decision.confidence > 0:
            st.markdown(f"**Confidence:** {decision.confidence:.0%}")
            st.progress(decision.confidence)


def render_agent_coordination_status(agent_statuses: Dict[str, AgentStatus], agent_order: List[str]):
    """
    Render a horizontal view of agent coordination status.
    """

    st.markdown("### 🎭 Agent Coordination Pipeline")

    cols = st.columns(len(agent_order))

    for idx, agent_name in enumerate(agent_order):
        with cols[idx]:
            if agent_name in agent_statuses:
                status = agent_statuses[agent_name]
                emoji = get_status_emoji(status.status)
                color = get_status_color(status.status)

                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background-color: #2A2A2A; border-radius: 8px; border-top: 4px solid {color};">
                    <div style="font-size: 2em;">{emoji}</div>
                    <div style="font-weight: bold; margin: 0.5rem 0;">{agent_name}</div>
                    <div style="color: {color}; font-size: 0.8em;">{status.status.upper()}</div>
                </div>
                """, unsafe_allow_html=True)

                if idx < len(agent_order) - 1:
                    st.markdown("<div style='text-align: center; font-size: 1.5em;'>→</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background-color: #1A1A1A; border-radius: 8px;">
                    <div style="font-size: 2em;">⚪</div>
                    <div style="font-weight: bold; margin: 0.5rem 0;">{agent_name}</div>
                    <div style="color: #666666; font-size: 0.8em;">PENDING</div>
                </div>
                """, unsafe_allow_html=True)


def render_timeline_event(event: Dict[str, Any]):
    """
    Render a timeline event.
    """

    st.markdown(f"""
    <div class="timeline-event">
        <strong>{event.get('agent', 'System')}</strong> - {event.get('action', 'Action')}
        <br>
        <small style="color: #999999;">{event.get('timestamp', '')}</small>
    </div>
    """, unsafe_allow_html=True)


def render_phase_header(phase_number: int, phase_name: str, description: str = ""):
    """
    Render a prominent phase header.
    """

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {NVIDIA_GREEN} 0%, #5A9000 100%);
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                color: white;">
        <h2 style="margin: 0; color: white !important;">Phase {phase_number}: {phase_name}</h2>
        {f'<p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)


def render_success_alert(message: str):
    """Render a success alert."""
    st.markdown(f"""
    <div class="alert-success">
        ✅ <strong>Success:</strong> {message}
    </div>
    """, unsafe_allow_html=True)


def render_info_alert(message: str):
    """Render an info alert."""
    st.markdown(f"""
    <div class="alert-info">
        ℹ️ <strong>Info:</strong> {message}
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_status(agent_statuses: Dict[str, AgentStatus], metrics: Dict[str, Any]):
    """
    Render compact status view in sidebar.
    """

    st.sidebar.markdown("### 📊 System Status")

    # Agent status indicators
    for agent_name, status in agent_statuses.items():
        emoji = get_status_emoji(status.status)
        st.sidebar.markdown(f"{emoji} **{agent_name}**: {status.status}")

    st.sidebar.markdown("---")

    # Key metrics
    st.sidebar.markdown("### 📈 Key Metrics")
    st.sidebar.markdown(f"**Documents:** {metrics.get('docs_scanned', 0)}")
    st.sidebar.markdown(f"**PDFs:** {metrics.get('pdfs_found', 0)}")
    st.sidebar.markdown(f"**Pages:** {metrics.get('pages_parsed', 0)}")
    st.sidebar.markdown(f"**Decisions:** {metrics.get('decisions_made', 0)}")
    st.sidebar.markdown(f"**API Calls:** {metrics.get('api_calls', 0)}")
