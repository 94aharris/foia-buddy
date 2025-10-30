"""
Advanced visualizations using Plotly for demo impact.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
from models.messages import AgentHandoff
from ui.theme import NVIDIA_GREEN, NVIDIA_GRAY, NVIDIA_DARK


def create_coordination_flow_diagram(
    agent_statuses: Dict[str, Any],
    agent_order: List[str],
    handoffs: List[AgentHandoff]
) -> go.Figure:
    """
    Create an interactive coordination flow diagram showing agent relationships.
    """

    # Create figure
    fig = go.Figure()

    # Agent positions in a flow
    num_agents = len(agent_order)
    x_positions = [i * 2 for i in range(num_agents)]
    y_position = 0

    # Node colors based on status
    node_colors = []
    node_sizes = []

    for agent_name in agent_order:
        if agent_name in agent_statuses:
            status = agent_statuses[agent_name].status
            if status == "active":
                node_colors.append(NVIDIA_GREEN)
                node_sizes.append(60)
            elif status == "complete":
                node_colors.append("#4CAF50")
                node_sizes.append(50)
            elif status in ["thinking", "executing"]:
                node_colors.append("#FFD700")
                node_sizes.append(55)
            else:
                node_colors.append(NVIDIA_GRAY)
                node_sizes.append(45)
        else:
            node_colors.append(NVIDIA_GRAY)
            node_sizes.append(45)

    # Add nodes (agents)
    fig.add_trace(go.Scatter(
        x=x_positions,
        y=[y_position] * num_agents,
        mode='markers+text',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color='white')
        ),
        text=agent_order,
        textposition="bottom center",
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{text}</b><br>Click for details<extra></extra>',
        showlegend=False
    ))

    # Add edges (connections between agents)
    for i in range(num_agents - 1):
        fig.add_trace(go.Scatter(
            x=[x_positions[i], x_positions[i+1]],
            y=[y_position, y_position],
            mode='lines',
            line=dict(width=2, color=NVIDIA_GRAY),
            hoverinfo='skip',
            showlegend=False
        ))

    # Update layout
    fig.update_layout(
        title="Agent Coordination Flow",
        title_font=dict(size=20, color=NVIDIA_GREEN),
        showlegend=False,
        hovermode='closest',
        paper_bgcolor=NVIDIA_DARK,
        plot_bgcolor=NVIDIA_DARK,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=250,
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return fig


def create_metrics_timeline(timeline_events: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a timeline visualization of agent activities.
    """

    if not timeline_events:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="Timeline will appear as agents execute...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=NVIDIA_GRAY)
        )
        fig.update_layout(
            paper_bgcolor=NVIDIA_DARK,
            plot_bgcolor=NVIDIA_DARK,
            height=300
        )
        return fig

    # Extract data
    agents = [event.get('agent', 'Unknown') for event in timeline_events]
    actions = [event.get('action', 'Action') for event in timeline_events]
    timestamps = list(range(len(timeline_events)))

    # Create color map for agents
    unique_agents = list(set(agents))
    colors = px.colors.qualitative.Set2[:len(unique_agents)]
    agent_colors = {agent: colors[i % len(colors)] for i, agent in enumerate(unique_agents)}

    # Create timeline
    fig = go.Figure()

    for i, event in enumerate(timeline_events):
        agent = event.get('agent', 'Unknown')
        action = event.get('action', 'Action')

        fig.add_trace(go.Scatter(
            x=[i],
            y=[agent],
            mode='markers',  # Removed text from mode
            marker=dict(
                size=12,  # Reduced size
                color=agent_colors.get(agent, NVIDIA_GREEN),
                line=dict(width=1, color='white')
            ),
            hovertemplate=f'<b>{agent}</b><br>{action}<br>Step {i+1}<extra></extra>',
            showlegend=False
        ))

    # Connect with lines
    for agent in unique_agents:
        agent_events = [(i, e) for i, e in enumerate(timeline_events) if e.get('agent') == agent]
        if len(agent_events) > 1:
            x_vals = [i for i, _ in agent_events]
            y_vals = [agent] * len(agent_events)
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines',
                line=dict(width=2, color=agent_colors.get(agent, NVIDIA_GRAY), dash='dash'),
                hoverinfo='skip',
                showlegend=False
            ))

    fig.update_layout(
        title="Agent Execution Timeline",
        title_font=dict(size=20, color=NVIDIA_GREEN),
        xaxis=dict(title="Execution Step", color='white', gridcolor='#333333'),
        yaxis=dict(title="Agent", color='white', gridcolor='#333333'),
        paper_bgcolor=NVIDIA_DARK,
        plot_bgcolor=NVIDIA_DARK,
        height=400,
        hovermode='closest'
    )

    return fig


def create_metrics_dashboard(metrics: Dict[str, Any]) -> go.Figure:
    """
    Create a metrics dashboard with multiple indicators.
    """

    # Create subplots
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=4,
        subplot_titles=("Documents", "PDFs", "Pages", "Decisions"),
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
    )

    # Add indicators
    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=metrics.get("docs_scanned", 0),
        delta={'reference': metrics.get("docs_scanned", 0) - metrics.get("docs_scanned_delta", 0)},
        title={"text": "📄 Documents"},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=1, col=1)

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=metrics.get("pdfs_found", 0),
        delta={'reference': metrics.get("pdfs_found", 0) - metrics.get("pdfs_found_delta", 0)},
        title={"text": "🔍 PDFs"},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=1, col=2)

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=metrics.get("pages_parsed", 0),
        delta={'reference': metrics.get("pages_parsed", 0) - metrics.get("pages_parsed_delta", 0)},
        title={"text": "📊 Pages"},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=1, col=3)

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=metrics.get("decisions_made", 0),
        delta={'reference': metrics.get("decisions_made", 0) - metrics.get("decisions_delta", 0)},
        title={"text": "🎯 Decisions"},
        domain={'x': [0, 1], 'y': [0, 1]}
    ), row=1, col=4)

    fig.update_layout(
        paper_bgcolor=NVIDIA_DARK,
        plot_bgcolor=NVIDIA_DARK,
        font=dict(color='white'),
        height=200,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    return fig


def create_agent_performance_chart(agent_metrics: Dict[str, Dict[str, Any]]) -> go.Figure:
    """
    Create a bar chart showing agent performance metrics.
    """

    if not agent_metrics:
        fig = go.Figure()
        fig.add_annotation(
            text="Agent metrics will appear after execution...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=NVIDIA_GRAY)
        )
        fig.update_layout(
            paper_bgcolor=NVIDIA_DARK,
            plot_bgcolor=NVIDIA_DARK,
            height=300
        )
        return fig

    agents = list(agent_metrics.keys())
    execution_times = [agent_metrics[agent].get('execution_time', 0) for agent in agents]
    api_calls = [agent_metrics[agent].get('api_calls', 0) for agent in agents]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Execution Time (s)',
        x=agents,
        y=execution_times,
        marker_color=NVIDIA_GREEN
    ))

    fig.add_trace(go.Bar(
        name='API Calls',
        x=agents,
        y=api_calls,
        marker_color='#FFD700'
    ))

    fig.update_layout(
        title="Agent Performance Metrics",
        title_font=dict(size=20, color=NVIDIA_GREEN),
        xaxis=dict(title="Agent", color='white'),
        yaxis=dict(title="Value", color='white'),
        paper_bgcolor=NVIDIA_DARK,
        plot_bgcolor=NVIDIA_DARK,
        barmode='group',
        height=400,
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(0,0,0,0.3)'
        )
    )

    return fig


def create_full_workflow_graph(
    agent_statuses: Dict[str, Any],
    agent_order: List[str],
    timeline_events: List[Dict[str, Any]],
    handoffs: List[AgentHandoff]
) -> go.Figure:
    """
    Create a comprehensive workflow graph showing all agents, their connections,
    tasks, and execution flow in a visually stunning layout.
    """

    if not agent_statuses:
        fig = go.Figure()
        fig.add_annotation(
            text="Workflow graph will appear after processing completes...",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color=NVIDIA_GRAY)
        )
        fig.update_layout(
            paper_bgcolor=NVIDIA_DARK,
            plot_bgcolor=NVIDIA_DARK,
            height=600
        )
        return fig

    fig = go.Figure()

    # Vertical layout positions
    num_agents = len(agent_order)
    y_positions = [i * 1.5 for i in range(num_agents)]
    x_center = 5

    # Build node information
    node_info = {}
    for i, agent_name in enumerate(agent_order):
        if agent_name in agent_statuses:
            status = agent_statuses[agent_name]

            # Count tasks for this agent from timeline
            tasks = [e for e in timeline_events if e.get('agent') == agent_name]

            node_info[agent_name] = {
                'y': y_positions[i],
                'status': status.status,
                'progress': status.progress,
                'tasks': tasks,
                'task_count': len(tasks)
            }

    # Draw handoff connections with arrows
    for handoff in handoffs:
        from_agent = handoff.from_agent
        to_agent = handoff.to_agent

        if from_agent in node_info and to_agent in node_info:
            # Draw curved arrow
            y_from = node_info[from_agent]['y']
            y_to = node_info[to_agent]['y']

            # Create curved path
            num_points = 20
            x_vals = []
            y_vals = []

            for i in range(num_points):
                t = i / (num_points - 1)
                # Bezier curve
                x = x_center + 2 * (1 - t) * t
                y = y_from + (y_to - y_from) * t
                x_vals.append(x)
                y_vals.append(y)

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode='lines',
                line=dict(width=3, color='rgba(118, 185, 0, 0.4)'),
                hovertemplate=f'<b>Handoff</b><br>{from_agent} → {to_agent}<br>{handoff.task}<extra></extra>',
                showlegend=False
            ))

            # Add arrowhead
            fig.add_annotation(
                x=x_vals[-1],
                y=y_vals[-1],
                ax=x_vals[-2],
                ay=y_vals[-2],
                xref='x',
                yref='y',
                axref='x',
                ayref='y',
                showarrow=True,
                arrowhead=2,
                arrowsize=1.5,
                arrowwidth=3,
                arrowcolor='rgba(118, 185, 0, 0.6)'
            )

    # Draw sequential flow connections
    for i in range(num_agents - 1):
        if agent_order[i] in node_info and agent_order[i+1] in node_info:
            y1 = node_info[agent_order[i]]['y']
            y2 = node_info[agent_order[i+1]]['y']

            fig.add_trace(go.Scatter(
                x=[x_center, x_center],
                y=[y1, y2],
                mode='lines',
                line=dict(width=2, color=NVIDIA_GRAY, dash='dot'),
                hoverinfo='skip',
                showlegend=False
            ))

    # Draw agent nodes with detailed information
    for agent_name in agent_order:
        if agent_name not in node_info:
            continue

        info = node_info[agent_name]
        y_pos = info['y']
        status = info['status']
        progress = info['progress']
        task_count = info['task_count']

        # Status color
        if status == "complete":
            color = '#4CAF50'
            size = 50
        elif status in ["active", "thinking", "executing"]:
            color = NVIDIA_GREEN
            size = 55
        elif status == "error":
            color = '#F44336'
            size = 50
        else:
            color = NVIDIA_GRAY
            size = 45

        # Main agent node
        fig.add_trace(go.Scatter(
            x=[x_center],
            y=[y_pos],
            mode='markers+text',
            marker=dict(
                size=size,
                color=color,
                line=dict(width=3, color='white'),
                symbol='circle'
            ),
            text=[agent_name],
            textposition="middle right",
            textfont=dict(size=14, color='white', family='Arial Black'),
            hovertemplate=f'<b>{agent_name}</b><br>Status: {status}<br>Progress: {progress*100:.0f}%<br>Tasks: {task_count}<extra></extra>',
            showlegend=False
        ))

        # Progress indicator ring
        if progress > 0:
            theta = [i * 360 * progress / 100 for i in range(101)]
            r = [0.3] * 101

            # Convert to cartesian
            import math
            ring_x = [x_center + r[i] * math.cos(math.radians(theta[i])) for i in range(len(theta))]
            ring_y = [y_pos + r[i] * math.sin(math.radians(theta[i])) for i in range(len(theta))]

            fig.add_trace(go.Scatter(
                x=ring_x,
                y=ring_y,
                mode='lines',
                line=dict(width=4, color=NVIDIA_GREEN),
                hoverinfo='skip',
                showlegend=False
            ))

        # Task indicators (small dots showing activities)
        if info['tasks']:
            task_positions = []
            for j, task in enumerate(info['tasks'][:5]):  # Show max 5 tasks
                x_offset = 1.5 + j * 0.3
                task_positions.append((x_center + x_offset, y_pos))

            if task_positions:
                task_x = [pos[0] for pos in task_positions]
                task_y = [pos[1] for pos in task_positions]

                fig.add_trace(go.Scatter(
                    x=task_x,
                    y=task_y,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color='#FFD700',
                        line=dict(width=1, color='white'),
                        symbol='star'
                    ),
                    hovertemplate='<b>Task Activity</b><extra></extra>',
                    showlegend=False
                ))

    # Add legend for status indicators
    legend_items = [
        ("Complete", '#4CAF50'),
        ("Active", NVIDIA_GREEN),
        ("Processing", '#FFD700'),
        ("Idle", NVIDIA_GRAY)
    ]

    for i, (label, color) in enumerate(legend_items):
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color=color, line=dict(width=1, color='white')),
            name=label,
            showlegend=True
        ))

    # Update layout
    fig.update_layout(
        title={
            'text': "Complete Workflow Graph - Multi-Agent Execution Flow",
            'font': dict(size=24, color=NVIDIA_GREEN, family='Arial Black'),
            'x': 0.5,
            'xanchor': 'center'
        },
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='white', size=12),
            bgcolor='rgba(0,0,0,0.5)'
        ),
        paper_bgcolor=NVIDIA_DARK,
        plot_bgcolor=NVIDIA_DARK,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[0, 10]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-1, num_agents * 1.5]
        ),
        height=max(600, num_agents * 150),
        hovermode='closest',
        margin=dict(l=50, r=200, t=100, b=50)
    )

    return fig
