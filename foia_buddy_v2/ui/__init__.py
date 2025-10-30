"""UI components for FOIA-Buddy V2."""

from .theme import apply_nvidia_theme, get_status_emoji, get_status_color
from .components import (
    render_agent_status_card,
    render_reasoning_stream,
    render_live_metrics,
    render_decision_point,
    render_agent_coordination_status,
    render_timeline_event,
    render_phase_header,
    render_success_alert,
    render_info_alert,
    render_sidebar_status
)
from .visualizations import (
    create_coordination_flow_diagram,
    create_metrics_timeline,
    create_metrics_dashboard,
    create_agent_performance_chart
)

__all__ = [
    'apply_nvidia_theme',
    'get_status_emoji',
    'get_status_color',
    'render_agent_status_card',
    'render_reasoning_stream',
    'render_live_metrics',
    'render_decision_point',
    'render_agent_coordination_status',
    'render_timeline_event',
    'render_phase_header',
    'render_success_alert',
    'render_info_alert',
    'render_sidebar_status',
    'create_coordination_flow_diagram',
    'create_metrics_timeline',
    'create_metrics_dashboard',
    'create_agent_performance_chart'
]
