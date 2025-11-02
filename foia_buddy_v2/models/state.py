"""
Application state management for Streamlit demo.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from models.messages import AgentStatus, DecisionPoint, AgentHandoff


@dataclass
class ApplicationState:
    """
    Global application state for the Streamlit demo.
    Tracks all agent activities and metrics in real-time.
    """

    # Agent states
    agent_statuses: Dict[str, AgentStatus] = field(default_factory=dict)

    # Execution tracking
    decision_points: List[DecisionPoint] = field(default_factory=list)
    agent_handoffs: List[AgentHandoff] = field(default_factory=list)
    reasoning_stream: List[str] = field(default_factory=list)

    # Global metrics
    metrics: Dict[str, Any] = field(default_factory=lambda: {
        "docs_scanned": 0,
        "docs_scanned_delta": 0,
        "pdfs_found": 0,
        "pdfs_found_delta": 0,
        "pages_parsed": 0,
        "pages_parsed_delta": 0,
        "decisions_made": 0,
        "decisions_delta": 0,
        "tools_called": 0,
        "api_calls": 0,
        "total_tokens": 0,
        "execution_time": 0.0
    })

    # Processing state
    is_processing: bool = False
    current_agent: str = ""
    foia_request: str = ""
    final_report: str = ""

    # Visualization data
    coordination_flow: List[Dict[str, Any]] = field(default_factory=list)
    timeline_events: List[Dict[str, Any]] = field(default_factory=list)

    # Live activity log for UI display
    activity_log: List[Dict[str, str]] = field(default_factory=list)

    def reset(self):
        """Reset state for new request."""
        self.agent_statuses = {}
        self.decision_points = []
        self.agent_handoffs = []
        self.reasoning_stream = []
        self.activity_log = []
        self.metrics = {
            "docs_scanned": 0,
            "docs_scanned_delta": 0,
            "pdfs_found": 0,
            "pdfs_found_delta": 0,
            "pages_parsed": 0,
            "pages_parsed_delta": 0,
            "decisions_made": 0,
            "decisions_delta": 0,
            "tools_called": 0,
            "api_calls": 0,
            "total_tokens": 0,
            "execution_time": 0.0
        }
        self.is_processing = False
        self.current_agent = ""
        self.final_report = ""
        self.coordination_flow = []
        self.timeline_events = []

    def update_metric(self, metric_name: str, value: int):
        """Update a metric and its delta."""
        if metric_name in self.metrics:
            old_value = self.metrics[metric_name]
            self.metrics[metric_name] = value
            delta_key = f"{metric_name}_delta"
            if delta_key in self.metrics:
                self.metrics[delta_key] = value - old_value

    def increment_metric(self, metric_name: str, amount: int = 1):
        """Increment a metric by amount."""
        if metric_name in self.metrics:
            old_value = self.metrics[metric_name]
            self.metrics[metric_name] = old_value + amount
            delta_key = f"{metric_name}_delta"
            if delta_key in self.metrics:
                self.metrics[delta_key] = amount

    def add_reasoning(self, text: str):
        """Add reasoning message to stream."""
        self.reasoning_stream.append(text)

    def add_activity_log(self, agent_name: str, event_type: str, message: str, icon: str = "ℹ️"):
        """Add entry to activity log for UI display."""
        self.activity_log.append({
            "agent": agent_name,
            "event": event_type,
            "message": message,
            "icon": icon
        })

    def add_decision(self, decision: DecisionPoint):
        """Add decision point."""
        self.decision_points.append(decision)
        self.increment_metric("decisions_made")

    def add_handoff(self, handoff: AgentHandoff):
        """Add agent handoff."""
        self.agent_handoffs.append(handoff)
