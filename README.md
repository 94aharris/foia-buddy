# FOIA-Buddy 🤖

An intelligent, multi-agent system for processing Freedom of Information Act (FOIA) requests using NVIDIA Nemotron models. Built for the NVIDIA AI Agents Hackathon, FOIA-Buddy demonstrates advanced agentic workflows with autonomous reasoning, multi-step planning, and tool integration.

## 🎯 Project Overview

FOIA-Buddy automates the complex process of FOIA request analysis and response generation through coordinated AI agents. The system uses NVIDIA Nemotron models to:

- **Analyze** FOIA requests using advanced reasoning
- **Coordinate** multiple specialized agents using ReAct patterns
- **Search** local PDF directories for relevant documents
- **Parse** PDFs to markdown using NVIDIA Nemotron VL (Vision-Language model)
- **Search** local markdown document repositories with semantic understanding
- **Generate** comprehensive, compliant response reports
- **Flag** sensitive content requiring redaction review

> **Note**: Public FOIA library search is currently unavailable due to API limitations. The system demonstrates PDF parsing capability using local PDFs from `sample_data/pdfs/`.

## 🏆 NVIDIA Nemotron Integration

This project specifically leverages NVIDIA Nemotron models for their superior agentic capabilities:

- **Primary Model**: `nvidia/nvidia-nemotron-nano-9b-v2` for reasoning and coordination
  - Powers 5 intelligent agents: Coordinator, Local PDF Search, Document Researcher, Public FOIA Search, and Report Generator
  - Thinking tokens (512-1024 tokens) enable complex multi-step reasoning
- **Document Parse Model**: `nvidia/nemotron-parse` for PDF parsing and document understanding
  - Specialized model for document parsing with multiple output modes
  - Handles scanned documents with OCR-like capabilities
  - Describes charts, graphs, and visual elements in natural language
  - Preserves document structure while extracting text from complex layouts
  - Superior to text-only parsing for real-world government documents
  - Supports markdown with/without bounding boxes and detection-only modes
- **Advanced Reasoning**: Thinking tokens for complex decision-making and step-by-step planning
- **Function Calling**: Agent-to-agent communication and tool use (planned feature)
- **Multi-Step Planning**: Autonomous workflow orchestration with ReAct patterns

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

### PDF Parsing with NVIDIA Nemotron Parse

To demonstrate the enhanced PDF parsing capability with specialized document understanding:

1. **Add PDFs** to `sample_data/pdfs/` directory (including scanned documents!)
2. **Run the processor** - it will automatically:
   - Find PDFs in the directory
   - Rank them by relevance to the FOIA request
   - Parse them to markdown using **NVIDIA Nemotron Parse** (specialized document parsing model)
   - Extract text from scanned documents with OCR-like capabilities
   - Describe visual elements (charts, graphs) in natural language
   - Include parsed content with visual descriptions in the final report

```bash
# Add your PDFs
cp your-document.pdf sample_data/pdfs/

# Process - PDFs will be automatically discovered and parsed
foia-buddy -i sample_data/foia-request.md -o response-1/
```

The parsed markdown files will be saved to `response-1/parsed_documents/` for review and analysis.

### Example Output Structure

```
response-1/
├── final_report.md           # Comprehensive FOIA response (nvidia-nemotron-nano-9b-v2)
├── executive_summary.md      # Executive summary of findings
├── compliance_notes.md       # Legal compliance information
├── redaction_review.txt      # Items flagged for redaction
├── processing_metadata.json  # Processing details and agent metrics
├── processing_report.html    # Interactive HTML report with Mermaid diagram and model info
├── downloaded_pdfs/          # PDFs from public FOIA library (if available)
│   └── *.pdf                 # Downloaded public documents
└── parsed_documents/         # Markdown versions of PDFs (nvidia/nemotron-parse)
    └── *.md                  # Parsed document content with visual descriptions
```

## 🤖 Agent Architecture

### Models Used

FOIA-Buddy leverages multiple NVIDIA models for different tasks:

| Agent | Model | Purpose |
|-------|-------|---------|
| **Coordinator Agent** | `nvidia/nvidia-nemotron-nano-9b-v2` | Request analysis, execution planning, agent orchestration |
| **Local PDF Search Agent** | `nvidia/nvidia-nemotron-nano-9b-v2` | Local PDF discovery, filename analysis, relevance ranking |
| **PDF Parser Agent** | `nvidia/nemotron-parse` | PDF to markdown conversion with visual understanding, OCR |
| **Document Researcher Agent** | `nvidia/nvidia-nemotron-nano-9b-v2` | Semantic search, document analysis, relevance scoring |
| **Public FOIA Search Agent** | `nvidia/nvidia-nemotron-nano-9b-v2` | Web scraping analysis, document relevance determination |
| **Report Generator Agent** | `nvidia/nvidia-nemotron-nano-9b-v2` | Report synthesis, compliance analysis, content generation |
| **HTML Report Generator** | Non-LLM (Direct Processing) | HTML generation, Mermaid diagram creation |

**Key Model Features:**
- **nvidia-nemotron-nano-9b-v2**: Advanced reasoning model with thinking tokens (512-1024 tokens) for complex decision-making
  - Enables step-by-step reasoning before generating responses
  - Used for 5 LLM-powered agents (Coordinator, Local PDF Search, Researcher, Report Generator, Public Search)
  - Temperature: 0.6, Top-p: 0.95 for balanced creativity and accuracy
- **nvidia/nemotron-parse**: Specialized document parsing model for multimodal document understanding
  - Handles scanned PDFs and image-based documents with OCR capabilities
  - Describes visual elements (charts, graphs, diagrams) in natural language
  - Converts PDF pages to markdown while preserving structure and visual context
  - Supports multiple parsing modes: markdown_bbox, markdown_no_bbox, detection_only
  - Max tokens: 16384 for accurate long-form document extraction

### Coordinator Agent

- **Role**: Orchestrates the entire FOIA processing workflow
- **Model**: `nvidia-nemotron-nano-9b-v2` with thinking tokens
- **Capabilities**: Request analysis, execution planning, agent coordination
- **Pattern**: ReAct (Reason → Act → Observe)

### Local PDF Search Agent

- **Role**: Searches local PDF directory for documents relevant to FOIA requests
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Capabilities**: Local file discovery, filename analysis, relevance ranking
- **Features**: Recursive PDF search, keyword matching, AI-powered relevance scoring
- **Data Source**: `sample_data/pdfs/` directory

### PDF Parser Agent

- **Role**: Converts PDF documents to markdown using NVIDIA Nemotron Parse model
- **Model**: `nvidia/nemotron-parse` (Specialized Document Parser)
- **Capabilities**: PDF parsing, visual understanding, document conversion, markdown generation, OCR
- **Features**:
  - Extracts text from native and scanned PDFs
  - Describes charts, graphs, and visual elements in natural language (e.g., "[Chart: Budget allocation breakdown showing 45% for operations]")
  - Handles complex multi-column layouts
  - Preserves tables and document structure
  - Superior handling of real-world government documents (often scanned or image-heavy)
  - Supports multiple parsing modes (markdown_bbox, markdown_no_bbox, detection_only)
- **Purpose**: Makes document content easier for other agents and end-users to evaluate, with enhanced visual understanding

### Public FOIA Search Agent

- **Role**: Searches public FOIA libraries for previously released documents
- **Model**: `nvidia/nvidia-nemotron-nano-9b-v2`
- **Capabilities**: Web scraping, document discovery, relevance analysis, PDF downloading
- **Features**: Semantic search of public databases, automated PDF retrieval
- **Status**: Currently limited due to API availability (see Limitations section)

### Document Researcher Agent

- **Role**: Searches and analyzes local document repositories
- **Model**: `nvidia/nvidia-nemotron-nano-9b-v2`
- **Capabilities**: Semantic search, relevance scoring, content extraction
- **Features**: PII detection, source attribution, bias awareness

### Report Generator Agent

- **Role**: Creates comprehensive FOIA response reports
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Capabilities**: Content synthesis, legal compliance, structured reporting
- **Outputs**: Executive summaries, compliance notes, redaction flags

### HTML Report Generator Agent

- **Role**: Creates interactive HTML reports with visual execution diagrams
- **Model**: Direct processing (non-LLM agent)
- **Capabilities**: HTML generation, Mermaid diagram creation, metadata visualization
- **Features**:
  - Responsive design with modern UI
  - Execution timeline with model information
  - Interactive Mermaid.js flow diagrams
  - Detailed metrics and agent reasoning display
- **Outputs**: Interactive HTML report (`processing_report.html`) with embedded diagrams showing complete agent workflow execution

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
  - Required for `nvidia-nemotron-nano-9b-v2` (reasoning/coordination)
  - Required for `nvidia/nemotron-parse` (PDF parsing with visual understanding)
- OpenAI-compatible client library
- Click for CLI interface
- Pydantic for data validation
- Requests and BeautifulSoup4 for HTML parsing
- Local PDF files in `sample_data/pdfs/` for demonstration

## 📝 Development

### Project Structure

```
foia_buddy/
├── agents/              # Agent implementations
│   ├── base.py         # Base agent class and registry
│   ├── coordinator.py  # Main coordination agent
│   ├── local_pdf_search.py     # Local PDF directory search agent
│   ├── pdf_parser.py   # PDF to markdown parser agent (Nemotron VL)
│   ├── document_researcher.py  # Local markdown document search agent
│   ├── report_generator.py     # Report creation agent
│   └── html_report_generator.py # HTML visualization report agent
├── models/             # Data models and messages
├── utils/              # NVIDIA client and utilities
└── cli.py              # Command-line interface

sample_data/
├── pdfs/               # Place PDF files here for parsing
│   └── README.md       # Instructions for adding PDFs
├── documents/          # Markdown documents for research
└── foia-request.md     # Sample FOIA request
```

### Adding New Agents

1. Inherit from `BaseAgent`
2. Implement `execute()` and `get_system_prompt()` methods
3. Register capabilities with `add_capability()`
4. Register with the `AgentRegistry`

## 🏅 Competition Advantages

- **Pure Nemotron Focus**: Demonstrates Nemotron's agentic and multimodal capabilities
- **Complete Workflow**: End-to-end FOIA processing automation
- **Extensible Design**: Easy to add new agents and capabilities
- **Real-World Utility**: Addresses actual government transparency needs
- **Advanced Reasoning**: Showcases thinking tokens and multi-step planning
- **Specialized Parsing**: Showcases NVIDIA Nemotron Parse for document parsing with visual understanding and OCR

## 📝 Current Limitations & Future Work

### Current Implementation

✅ **Working Features:**
- Local PDF search and discovery
- PDF-to-markdown conversion using NVIDIA Nemotron Parse (specialized document parsing model)
- Visual element description (charts, graphs) in parsed documents
- OCR-like capabilities for scanned PDFs
- Multiple parsing modes (markdown with/without bounding boxes, detection only)
- Local markdown document research
- Multi-agent coordination with ReAct pattern
- Comprehensive report generation
- Interactive HTML reports with execution diagrams showing models used

⚠️ **Known Limitations:**
- **Public FOIA Library Search**: The State Department's FOIA portal (foia.state.gov) does not have a working public API for automated searches. All GET/POST requests return zero results.
  - **Current Solution**: Demonstrate PDF parsing with local PDFs from `sample_data/pdfs/`
  - **Future Enhancement**: Integrate with FOIA.gov API or other public FOIA databases

### Future Enhancements

- Integration with FOIA.gov API
- Support for additional document formats (DOCX, TXT, images)
- Advanced redaction analysis
- Multi-language support
- Enhanced visualization and reporting

## 📞 Support

For questions about FOIA-Buddy:

- Review the `PLAN.md` for detailed implementation notes
- Check sample outputs in the demo
- Examine agent implementations for extension patterns

Built with ❤️ for the NVIDIA AI Agents Hackathon
