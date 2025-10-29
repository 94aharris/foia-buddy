# FOIA-Buddy Implementation Plan

## Overview
Build an agentic Python CLI application using NVIDIA Nemotron models to process FOIA requests with multi-agent orchestration, focusing on autonomous reasoning and extensible architecture.

## Core Architecture

### 1. Agent Framework
- **Base Agent Class**: Abstract interface for all agents
- **Agent Registry**: Dynamic agent discovery and registration
- **Communication Protocol**: Standardized message passing between agents

### 2. Core Agents

#### Coordinator Agent
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Purpose**: Analyze FOIA requests, create execution plans, orchestrate sub-agents
- **Workflow**: ReAct pattern (Reason → Act → Observe)
- **Capabilities**:
  - Parse FOIA request complexity
  - Generate search strategies
  - Coordinate parallel agent execution
  - Synthesize results

#### Document Researcher Agent
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Purpose**: Search and analyze local markdown documents
- **Capabilities**:
  - Semantic document search
  - Content relevance scoring
  - Extract relevant passages
  - Source tracking

#### Report Generator Agent
- **Model**: `nvidia-nemotron-nano-9b-v2`
- **Purpose**: Create comprehensive FOIA response reports
- **Capabilities**:
  - Synthesize findings from multiple sources
  - Generate structured reports
  - Track information sources
  - Format output for compliance

### 3. Extensibility Features
- **Plugin Architecture**: Easy addition of new agents
- **Configuration System**: YAML-based agent configuration
- **Hook System**: Pre/post processing hooks
- **Result Aggregation**: Standardized result format

## Technical Implementation

### Dependencies
- `openai` - NVIDIA API client
- `pydantic` - Data validation
- `click` - CLI interface
- `pyyaml` - Configuration
- `pathlib` - File operations

### Directory Structure
```
foia-buddy/
├── foia_buddy/
│   ├── __init__.py
│   ├── cli.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── coordinator.py
│   │   ├── document_researcher.py
│   │   └── report_generator.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── messages.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── nvidia_client.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── sample_data/
│   ├── foia-request.md
│   └── documents/
│       ├── doc1.md
│       ├── doc2.md
│       └── doc3.md
├── requirements.txt
├── setup.py
└── README.md
```

## CLI Interface
```bash
foia-buddy -i foia-request.md -o response-1/
```

## MVP Features
1. ✅ Parse FOIA request from markdown
2. ✅ Coordinate multiple agents using Nemotron reasoning
3. ✅ Search local document repository
4. ✅ Generate comprehensive report
5. ✅ Extensible agent architecture
6. ✅ Structured output directory

## Nemotron Integration Points
- **Reasoning**: Complex decision-making for agent coordination
- **Function Calling**: Agent-to-agent communication
- **Tool Use**: File system operations and document analysis
- **Planning**: Multi-step workflow orchestration

## Future Extensions
- Web search agent (Tavily integration)
- Vector database agent (RAG)
- PII detection/redaction agent
- Email notification agent
- Database integration agent

## Success Metrics
- Autonomous multi-agent coordination
- Extensible plugin system
- Real FOIA request processing
- Demonstrates Nemotron's agentic capabilities