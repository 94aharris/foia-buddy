"""
NVIDIA-themed styling for Streamlit application.
"""

import streamlit as st


# NVIDIA Brand Colors
NVIDIA_GREEN = "#76B900"
NVIDIA_DARK = "#1A1A1A"
NVIDIA_GRAY = "#666666"
NVIDIA_LIGHT = "#F5F5F5"
NVIDIA_BLACK = "#000000"


def apply_nvidia_theme():
    """
    Apply NVIDIA-themed styling to the Streamlit app.
    """

    st.markdown(f"""
    <style>
        /* Main theme */
        .stApp {{
            background-color: {NVIDIA_DARK};
            color: {NVIDIA_LIGHT};
        }}

        /* Headers */
        h1, h2, h3 {{
            color: {NVIDIA_GREEN} !important;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }}

        /* Agent cards */
        .agent-card {{
            background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
            border-left: 4px solid {NVIDIA_GREEN};
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}

        .agent-card-active {{
            background: linear-gradient(135deg, #2A3A2A 0%, #3A4A3A 100%);
            border-left: 4px solid {NVIDIA_GREEN};
            animation: pulse 2s infinite;
        }}

        /* Active agent pulse animation */
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(118, 185, 0, 0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(118, 185, 0, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(118, 185, 0, 0); }}
        }}

        /* Status indicators */
        .status-idle {{ color: {NVIDIA_GRAY}; }}
        .status-active {{ color: {NVIDIA_GREEN}; }}
        .status-thinking {{ color: #FFD700; }}
        .status-complete {{ color: #4CAF50; }}
        .status-error {{ color: #F44336; }}

        /* Reasoning tokens */
        .reasoning-token {{
            background-color: #2A2A2A;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            margin: 0.25rem 0;
            border-left: 3px solid {NVIDIA_GREEN};
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        /* Metrics */
        .metric-card {{
            background: linear-gradient(135deg, {NVIDIA_GREEN} 0%, #5A9000 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: white;
        }}

        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            color: white;
        }}

        /* Buttons */
        .stButton > button {{
            background-color: {NVIDIA_GREEN};
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 4px;
            font-weight: bold;
            transition: all 0.3s;
        }}

        .stButton > button:hover {{
            background-color: #5A9000;
            box-shadow: 0 4px 8px rgba(118, 185, 0, 0.3);
        }}

        /* Sidebar */
        .css-1d391kg, [data-testid="stSidebar"] {{
            background-color: #0A0A0A;
        }}

        /* Progress bars */
        .stProgress > div > div > div > div {{
            background-color: {NVIDIA_GREEN};
        }}

        /* Expander */
        .streamlit-expanderHeader {{
            background-color: #2A2A2A;
            border-radius: 4px;
        }}

        /* Code blocks */
        .stCodeBlock {{
            background-color: #1A1A1A;
            border-left: 3px solid {NVIDIA_GREEN};
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}

        .stTabs [data-baseweb="tab"] {{
            background-color: #2A2A2A;
            border-radius: 4px 4px 0 0;
            color: {NVIDIA_LIGHT};
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {NVIDIA_GREEN};
            color: white;
        }}

        /* Alert boxes */
        .alert-success {{
            background-color: rgba(118, 185, 0, 0.1);
            border-left: 4px solid {NVIDIA_GREEN};
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }}

        .alert-info {{
            background-color: rgba(33, 150, 243, 0.1);
            border-left: 4px solid #2196F3;
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }}

        /* Decision point styling */
        .decision-point {{
            background-color: #2A2A2A;
            border-left: 4px solid #FFD700;
            padding: 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }}

        /* Timeline */
        .timeline-event {{
            position: relative;
            padding-left: 30px;
            margin: 1rem 0;
        }}

        .timeline-event::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 5px;
            width: 12px;
            height: 12px;
            background-color: {NVIDIA_GREEN};
            border-radius: 50%;
        }}

        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}

        ::-webkit-scrollbar-track {{
            background: #1A1A1A;
        }}

        ::-webkit-scrollbar-thumb {{
            background: {NVIDIA_GREEN};
            border-radius: 5px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #5A9000;
        }}
    </style>
    """, unsafe_allow_html=True)


def get_status_emoji(status: str) -> str:
    """Get emoji for agent status."""
    status_emojis = {
        "idle": "⚪",
        "active": "🟢",
        "thinking": "🟡",
        "planning": "🔵",
        "executing": "⚡",
        "reflecting": "🟣",
        "complete": "✅",
        "error": "❌"
    }
    return status_emojis.get(status, "⚪")


def get_status_color(status: str) -> str:
    """Get color for agent status."""
    status_colors = {
        "idle": NVIDIA_GRAY,
        "active": NVIDIA_GREEN,
        "thinking": "#FFD700",
        "planning": "#2196F3",
        "executing": "#FF9800",
        "reflecting": "#9C27B0",
        "complete": "#4CAF50",
        "error": "#F44336"
    }
    return status_colors.get(status, NVIDIA_GRAY)
