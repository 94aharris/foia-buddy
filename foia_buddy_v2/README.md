# FOIA-Buddy V2 - Multi-Agent FOIA Processing Demo

A **demo-first, visually stunning Streamlit application** that showcases advanced multi-agent AI coordination for FOIA (Freedom of Information Act) request processing using NVIDIA Nemotron models.

![Demo Status](https://img.shields.io/badge/status-demo-green)
![NVIDIA](https://img.shields.io/badge/powered%20by-NVIDIA%20Nemotron-76B900)

## 🎯 Project Vision

FOIA-Buddy V2 is NOT just a CLI tool with a UI wrapper - it's a **live demonstration platform** that makes agent reasoning, coordination, and decision-making **transparently visible** to judges and users in real-time.

## ✨ Key Features

### 🧠 Real-Time Agent Reasoning
- **Live thinking tokens** from Nemotron models
- **Visible decision-making** with reasoning explanations
- **Step-by-step planning** exposed to users

### 🎭 Multi-Agent Orchestration
- **Coordinator Agent** - Orchestrates workflow
- **PDF Searcher** - Discovers relevant documents
- **PDF Parser** - Multimodal document understanding with Nemotron Parse
- **Document Researcher** - Semantic search across repositories
- **Report Generator** - Synthesizes comprehensive FOIA responses

### 📊 Beautiful Visualizations
- **Interactive coordination diagrams** showing agent handoffs
- **Real-time metrics dashboard** with animated updates
- **Execution timeline** tracking agent activities
- **Decision point visualization** with reasoning

### 🎨 NVIDIA-Themed UI
- Professional NVIDIA green and dark theme
- Smooth animations and transitions
- Responsive layout optimized for demos

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- NVIDIA API key ([Get one here](https://build.nvidia.com/))

### Installation

```bash
# Clone or navigate to the project
cd foia_buddy_v2

# Install dependencies
pip install -r requirements.txt

# Set your NVIDIA API key
export NVIDIA_API_KEY="your_key_here"

# Run the application
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Using the Demo

1. **Enter API Key**: Input your NVIDIA API key in the sidebar
2. **Select Scenario**: Choose from pre-loaded demo scenarios or enter your own
3. **Process Request**: Click "🚀 Process Request" and watch the magic happen!

## 📁 Project Structure

```
foia_buddy_v2/
├── app.py                      # Main Streamlit application
├── agents/                     # Agent implementations
│   ├── base_agent.py          # Base agent with streaming
│   ├── coordinator.py         # Orchestration agent
│   ├── pdf_searcher.py        # PDF discovery
│   ├── pdf_parser.py          # Multimodal parsing
│   ├── document_researcher.py # Semantic search
│   ├── report_generator.py    # Report synthesis
│   └── decision_logger.py     # Decision tracking
├── ui/                        # UI components
│   ├── components.py          # Reusable UI components
│   ├── visualizations.py      # Plotly charts and graphs
│   └── theme.py               # NVIDIA styling
├── models/                    # Data models
│   ├── messages.py            # Agent messages
│   └── state.py               # Application state
├── utils/                     # Utilities
│   ├── nvidia_client.py       # NVIDIA API client
│   └── logger.py              # Enhanced logging
├── sample_data/               # Demo data
│   ├── pdfs/                  # Sample PDFs
│   └── documents/             # Sample documents
└── requirements.txt           # Python dependencies
```

## 🎬 Demo Scenarios

### 1. AI Policy Documents
Request for AI policy documents, budget allocations, and ethics guidelines.
**Expected time**: 2-3 minutes

### 2. Budget Transparency
Request for budget allocations, contracts, and spending reports.
**Expected time**: 1-2 minutes

### 3. Communications Records
Request for meeting minutes, communications, and policy briefings.
**Expected time**: 2-3 minutes

## 🏆 Hackathon Optimization

This application is specifically designed for hackathon demos with:

- ✅ **Visual Impact** - Immediately clear it's multi-agent
- ✅ **Reasoning Visibility** - Nemotron thinking tokens clearly shown
- ✅ **Real-Time Updates** - Smooth, responsive UI with live feedback
- ✅ **Clear Differentiation** - Obviously NOT a simple chatbot
- ✅ **Technical Depth** - Complex agentic workflows made comprehensible
- ✅ **Demo Speed** - Complete workflow in 90-120 seconds
- ✅ **Wow Factor** - Visual elements that impress

## 🎯 Key Technologies

- **NVIDIA Nemotron-70B** - Advanced reasoning with thinking tokens
- **NVIDIA Nemotron Parse** - Multimodal document understanding (VL model)
- **Streamlit** - Interactive web application framework
- **Plotly** - Interactive visualizations
- **AsyncIO** - Asynchronous agent execution

## 📊 What You'll See During Execution

1. **Request Analysis** (20s) - Coordinator extracts topics and plans workflow
2. **PDF Search** (15s) - Discovers and ranks relevant documents
3. **PDF Parsing** (30s) - Extracts text, tables, charts with visual understanding
4. **Document Research** (20s) - Semantic search across repositories
5. **Report Generation** (30s) - Synthesizes comprehensive FOIA response
6. **Results Display** (5s) - Final report with download options

**Total Demo Time: ~2 minutes** ⏱️

## 🎨 Customization

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`
2. Implement `_generate_plan` and `_execute_plan` methods
3. Register the agent in the coordinator
4. Add to the agent order in `app.py`

### Adding Demo Scenarios

Edit the `DEMO_SCENARIOS` dictionary in `app.py`:

```python
DEMO_SCENARIOS = {
    "Your Scenario": {
        "request": "Your FOIA request text...",
        "topics": ["topic1", "topic2"],
        "estimated_time": "2 minutes"
    }
}
```

## 🔧 Configuration

### Environment Variables

- `NVIDIA_API_KEY` - Your NVIDIA API key (required)

### Streamlit Configuration

The app uses wide layout and expanded sidebar by default. Modify in `app.py`:

```python
st.set_page_config(
    page_title="FOIA-Buddy V2",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

## 📝 Notes for Production

This is a **demo-optimized** application. For production use:

1. **Add real PDF parsing** - Integrate actual PDF libraries and Nemotron Parse API
2. **Add authentication** - Secure API key management
3. **Add error handling** - Robust error recovery
4. **Add data persistence** - Save processed requests
5. **Add rate limiting** - Protect API quotas
6. **Add logging** - Comprehensive activity logs
7. **Add testing** - Unit and integration tests

## 🤝 Contributing

This is a hackathon demo project. Feel free to:
- Add new agents
- Improve visualizations
- Add more demo scenarios
- Enhance UI components

## 📄 License

This project is created for the NVIDIA Nemotron Hackathon.

## 🙏 Acknowledgments

- **NVIDIA** for Nemotron models and API access
- **Streamlit** for the amazing app framework
- **Plotly** for beautiful visualizations

## 🎤 Demo Presentation Tips

When presenting to judges:

1. **Start with the problem** - "FOIA requests are complex and time-consuming"
2. **Show the solution** - "Multi-agent AI makes it transparent and efficient"
3. **Point to reasoning** - "Notice the real-time thinking tokens"
4. **Highlight coordination** - "See how agents hand off tasks"
5. **Show multimodal** - "Nemotron Parse understands charts and tables"
6. **Emphasize speed** - "Complete workflow in under 2 minutes"

## 📞 Support

For questions or issues:
- Review the code documentation
- Check sample scenarios
- Verify API key is set correctly

---

**Built with ❤️ for NVIDIA Nemotron Hackathon**

*Showcasing the power of multi-agent AI coordination with transparent, visible reasoning*
