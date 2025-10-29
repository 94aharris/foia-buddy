# FOIA-Buddy 🤖

An intelligent, multi-agent system for processing Freedom of Information Act (FOIA) requests using NVIDIA Nemotron models. Built for the NVIDIA AI Agents Hackathon, FOIA-Buddy demonstrates advanced agentic workflows with autonomous reasoning, multi-step planning, and tool integration.

## 🎯 Project Overview

FOIA-Buddy automates the complex process of FOIA request analysis and response generation through coordinated AI agents. The system uses NVIDIA Nemotron models to:

- **Analyze** FOIA requests using advanced reasoning
- **Coordinate** multiple specialized agents using ReAct patterns
- **Search** public FOIA libraries for previously released documents
- **Download** relevant PDFs from public repositories automatically
- **Parse** PDFs to markdown using NVIDIA Parse Nemotron
- **Search** local document repositories with semantic understanding
- **Generate** comprehensive, compliant response reports
- **Flag** sensitive content requiring redaction review

## 🏆 NVIDIA Nemotron Integration

This project specifically leverages NVIDIA Nemotron models for their superior agentic capabilities:

- **Primary Model**: `nvidia-nemotron-nano-9b-v2` for reasoning and coordination
- **Parse Model**: `nvidia/nemotron-parse` for PDF to markdown conversion
- **Advanced Reasoning**: Thinking tokens for complex decision-making
- **Function Calling**: Agent-to-agent communication and tool use
- **Multi-Step Planning**: Autonomous workflow orchestration

## 🚀 Quick Start

### Prerequisites

```bash
# Set your NVIDIA API key
export NVIDIA_API_KEY="your_nvidia_api_key_here"

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Basic Usage

```bash
# Process a FOIA request
foia-buddy -i sample_data/foia-request.md -o response-1/

# With verbose output
foia-buddy -i sample_data/foia-request.md -o response-1/ --verbose
```

### Example Output Structure

```
response-1/
├── final_report.md           # Comprehensive FOIA response
├── executive_summary.md      # Executive summary of findings
├── compliance_notes.md       # Legal compliance information
├── redaction_review.txt      # Items flagged for redaction
├── processing_metadata.json  # Processing details and metrics
├── downloaded_pdfs/          # PDFs from public FOIA library
│   └── *.pdf                 # Downloaded public documents
└── parsed_documents/         # Markdown versions of PDFs
    └── *.md                  # Parsed document content
```

## 🤖 Agent Architecture

### Coordinator Agent

- **Role**: Orchestrates the entire FOIA processing workflow
- **Model**: `nvidia-nemotron-nano-9b-v2` with thinking tokens
- **Capabilities**: Request analysis, execution planning, agent coordination
- **Pattern**: ReAct (Reason → Act → Observe)

### Public FOIA Search Agent

- **Role**: Searches the State Department's public FOIA library for previously released documents
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Capabilities**: Web scraping, keyword extraction, precedent research, relevance scoring, PDF downloading
- **Features**: Multi-keyword search, result deduplication, case number extraction, automatic PDF download
- **Data Source**: https://foia.state.gov/FOIALIBRARY/SearchResults.aspx

### PDF Parser Agent

- **Role**: Converts PDF documents to markdown using NVIDIA Parse Nemotron
- **Model**: `nvidia/nemotron-parse`
- **Capabilities**: PDF parsing, document conversion, markdown generation
- **Features**: Text extraction, table preservation, structure maintenance, multi-page handling
- **Purpose**: Makes document content easier for other agents and end-users to evaluate

### Document Researcher Agent

- **Role**: Searches and analyzes local document repositories
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Capabilities**: Semantic search, relevance scoring, content extraction
- **Features**: PII detection, source attribution, bias awareness

### Report Generator Agent

- **Role**: Creates comprehensive FOIA response reports
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Capabilities**: Content synthesis, legal compliance, structured reporting
- **Outputs**: Executive summaries, compliance notes, redaction flags

## 🔧 Extensible Architecture

The system is designed for easy agent extension:

```python
from foia_buddy.agents import BaseAgent, AgentRegistry
from foia_buddy.utils import NvidiaClient

class CustomAgent(BaseAgent):
    def __init__(self, nvidia_client):
        super().__init__("custom_agent", "Description", nvidia_client)
        self.add_capability("custom_capability")

    async def execute(self, task):
        # Your agent logic here
        pass

# Register your agent
registry = AgentRegistry()
registry.register(CustomAgent(nvidia_client))
```

## 📊 Sample Demo

The project includes a complete sample demonstration:

- **FOIA Request**: AI policy documentation request (`sample_data/foia-request.md`)
- **Document Repository**: Government AI policy documents (`sample_data/documents/`)
- **Expected Output**: Professional FOIA response with source attribution

Try the demo:

```bash
foia-buddy -i sample_data/foia-request.md -o demo-output/
```

## 🎯 Hackathon Criteria Alignment

### ✅ Agentic Workflows

- **Multi-Agent Coordination**: Coordinator orchestrates specialized agents
- **Autonomous Reasoning**: Agents make independent decisions using Nemotron thinking
- **ReAct Patterns**: Reason → Act → Observe loops for complex problem-solving

### ✅ NVIDIA Nemotron Excellence

- **Primary Model**: Uses `nvidia-nemotron-nano-9b-v2` throughout
- **Advanced Features**: Thinking tokens for complex reasoning
- **Function Calling**: Agent communication and tool integration
- **Agentic Strengths**: Planning, reasoning, and autonomous decision-making

### ✅ Real-World Impact

- **Government Transparency**: Automates critical FOIA processing
- **Legal Compliance**: Ensures proper documentation and attribution
- **Efficiency Gains**: Reduces manual processing time significantly
- **Scalable Solution**: Extensible architecture for additional use cases

### ✅ Innovation Beyond Prompting

- **Multi-Step Workflows**: Complex coordination across multiple agents
- **Tool Integration**: File system operations, document analysis
- **Dynamic Planning**: Adaptive execution based on request complexity
- **State Management**: Persistent coordination across agent interactions

## 🔧 Technical Requirements

- Python 3.8+
- NVIDIA API access (get yours at build.nvidia.com)
- OpenAI-compatible client library
- Click for CLI interface
- Pydantic for data validation
- Requests and BeautifulSoup4 for web scraping
- Internet connection for public FOIA library access

## 📝 Development

### Project Structure

```
foia_buddy/
├── agents/              # Agent implementations
│   ├── base.py         # Base agent class and registry
│   ├── coordinator.py  # Main coordination agent
│   ├── public_foia_search.py   # Public FOIA library search agent
│   ├── pdf_parser.py   # PDF to markdown parser agent
│   ├── document_researcher.py  # Local document search agent
│   └── report_generator.py     # Report creation agent
├── models/             # Data models and messages
├── utils/              # NVIDIA client and utilities
└── cli.py              # Command-line interface
```

### Adding New Agents

1. Inherit from `BaseAgent`
2. Implement `execute()` and `get_system_prompt()` methods
3. Register capabilities with `add_capability()`
4. Register with the `AgentRegistry`

## 🏅 Competition Advantages

- **Pure Nemotron Focus**: Demonstrates Nemotron's agentic capabilities
- **Complete Workflow**: End-to-end FOIA processing automation
- **Extensible Design**: Easy to add new agents and capabilities
- **Real-World Utility**: Addresses actual government transparency needs
- **Advanced Reasoning**: Showcases thinking tokens and multi-step planning

## 📞 Support

For questions about FOIA-Buddy:

- Review the `PLAN.md` for detailed implementation notes
- Check sample outputs in the demo
- Examine agent implementations for extension patterns

Built with ❤️ for the NVIDIA AI Agents Hackathon
