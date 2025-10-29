from typing import Dict, Any, List
import json
import time
from datetime import datetime
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class HTMLReportGeneratorAgent(BaseAgent):
    """Generates interactive HTML reports from processing metadata with Mermaid diagrams."""

    def __init__(self, nvidia_client):
        super().__init__(
            name="html_report_generator",
            description="Creates interactive HTML reports with visual diagrams from processing metadata",
            nvidia_client=nvidia_client
        )
        self.add_capability("html_generation")
        self.add_capability("visualization")
        self.add_capability("metadata_analysis")

    def get_system_prompt(self) -> str:
        return """You are the HTML Report Generator Agent for FOIA-Buddy.

Your role is to:
1. ANALYZE processing metadata from FOIA request processing
2. CREATE interactive HTML reports with visual elements
3. GENERATE Mermaid diagrams showing agent execution flows
4. PRESENT data in a clear, professional, and visually appealing format

Report Requirements:
- Professional HTML5 structure with embedded CSS
- Responsive design that works on all devices
- Interactive Mermaid.js diagrams showing agent workflows
- Clear presentation of processing metrics and timelines
- Detailed breakdown of each agent's contribution
- Visual indicators for success/failure states

Always create well-structured, accessible HTML with modern design principles."""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute HTML report generation task."""
        start_time = time.time()

        try:
            # Get metadata file path from task context
            metadata_path = task.context.get("metadata_path", "")
            output_path = task.context.get("output_path", "")

            if not metadata_path or not Path(metadata_path).exists():
                return self._create_result(
                    task.task_id,
                    success=False,
                    data={"error": f"Metadata file not found: {metadata_path}"},
                    reasoning="Cannot generate report without metadata file",
                    confidence=0.0,
                    start_time=start_time
                )

            # Read and parse metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Generate HTML report
            html_content = self._generate_html_report(metadata)

            # Save HTML report
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)

            result_data = {
                "html_content": html_content,
                "output_file": str(output_path) if output_path else None,
                "report_sections": [
                    "Summary",
                    "Agent Execution Timeline",
                    "Execution Flow Diagram",
                    "Detailed Agent Results"
                ],
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "metadata_processed": metadata_path
                }
            }

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning="Successfully generated interactive HTML report with execution diagram",
                confidence=0.95,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during HTML report generation: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    def _generate_html_report(self, metadata: Dict[str, Any]) -> str:
        """Generate the complete HTML report."""

        # Extract key information
        agent_results = metadata.get("agent_results", {})
        processing_start = metadata.get("processing_start", 0)
        total_time = metadata.get("processing_time", 0)
        input_file = metadata.get("input_file", "Unknown")
        output_dir = metadata.get("output_directory", "Unknown")
        status = metadata.get("status", "unknown")

        # Generate sections
        summary_html = self._generate_summary_section(metadata)
        timeline_html = self._generate_timeline_section(agent_results)
        mermaid_diagram = self._generate_mermaid_diagram(agent_results)
        details_html = self._generate_details_section(agent_results)

        # Build complete HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FOIA-Buddy Processing Report</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-weight: 600;
        }}

        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}

        .status-completed {{
            background: #10b981;
            color: white;
        }}

        .status-failed {{
            background: #ef4444;
            color: white;
        }}

        .status-unknown {{
            background: #6b7280;
            color: white;
        }}

        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-size: 2em;
            font-weight: 700;
        }}

        .timeline {{
            position: relative;
            padding-left: 40px;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #667eea;
        }}

        .timeline-item {{
            position: relative;
            margin-bottom: 30px;
            padding: 20px;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}

        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -47px;
            top: 20px;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid white;
            box-shadow: 0 0 0 3px #667eea;
        }}

        .timeline-item.success::before {{
            background: #10b981;
            box-shadow: 0 0 0 3px #10b981;
        }}

        .timeline-item.failed::before {{
            background: #ef4444;
            box-shadow: 0 0 0 3px #ef4444;
        }}

        .timeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .agent-name {{
            font-size: 1.3em;
            font-weight: 600;
            color: #667eea;
        }}

        .execution-time {{
            font-size: 0.9em;
            color: #6b7280;
            background: white;
            padding: 4px 12px;
            border-radius: 12px;
        }}

        .diagram-container {{
            background: #f9fafb;
            padding: 30px;
            border-radius: 10px;
            margin: 20px 0;
            display: flex;
            justify-content: center;
        }}

        .agent-details {{
            margin-top: 40px;
        }}

        .agent-card {{
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            transition: all 0.3s ease;
        }}

        .agent-card:hover {{
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
            border-color: #667eea;
        }}

        .agent-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .confidence-badge {{
            background: #fef3c7;
            color: #92400e;
            padding: 6px 12px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.85em;
        }}

        .confidence-high {{
            background: #d1fae5;
            color: #065f46;
        }}

        .data-section {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}

        .data-section h4 {{
            color: #667eea;
            margin-bottom: 10px;
        }}

        .data-section pre {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.9em;
        }}

        .reasoning-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
        }}

        .reasoning-box h4 {{
            color: #92400e;
            margin-bottom: 8px;
        }}

        .reasoning-box p {{
            color: #78350f;
            line-height: 1.6;
        }}

        footer {{
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .metrics {{
                grid-template-columns: 1fr;
            }}

            .header h1 {{
                font-size: 1.8em;
            }}

            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 FOIA-Buddy Processing Report</h1>
            <p>Intelligent Multi-Agent FOIA Request Processing</p>
        </div>

        <div class="content">
            {summary_html}
            {timeline_html}

            <div class="section">
                <h2 class="section-title">🔄 Agent Execution Flow</h2>
                <div class="diagram-container">
                    <div class="mermaid">
{mermaid_diagram}
                    </div>
                </div>
            </div>

            {details_html}
        </div>

        <footer>
            <p>Generated by FOIA-Buddy HTML Report Generator Agent</p>
            <p>Powered by NVIDIA Nemotron Models | Built for NVIDIA AI Agents Hackathon</p>
        </footer>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#667eea',
                primaryTextColor: '#fff',
                primaryBorderColor: '#764ba2',
                lineColor: '#667eea',
                secondaryColor: '#764ba2',
                tertiaryColor: '#f9fafb'
            }}
        }});
    </script>
</body>
</html>"""

        return html

    def _generate_summary_section(self, metadata: Dict[str, Any]) -> str:
        """Generate the summary section of the report."""

        status = metadata.get("status", "unknown")
        total_time = metadata.get("processing_time", 0)
        input_file = metadata.get("input_file", "Unknown")
        output_dir = metadata.get("output_directory", "Unknown")
        agent_results = metadata.get("agent_results", {})

        # Count successful agents
        successful_agents = sum(1 for result in agent_results.values()
                               if result.get("success", False))
        total_agents = len(agent_results)

        # Determine status class
        status_class = f"status-{status}" if status in ["completed", "failed"] else "status-unknown"

        return f"""
            <div class="section">
                <h2 class="section-title">📊 Processing Summary</h2>
                <div style="margin-bottom: 20px;">
                    <span class="status-badge {status_class}">{status.upper()}</span>
                </div>

                <div class="metrics">
                    <div class="metric-card">
                        <div class="metric-label">Total Processing Time</div>
                        <div class="metric-value">{total_time:.2f}s</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Agents Executed</div>
                        <div class="metric-value">{total_agents}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Successful Agents</div>
                        <div class="metric-value">{successful_agents}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-value">{(successful_agents/max(total_agents,1)*100):.0f}%</div>
                    </div>
                </div>

                <div style="margin-top: 20px; padding: 20px; background: #f9fafb; border-radius: 8px;">
                    <p><strong>Input File:</strong> {input_file}</p>
                    <p><strong>Output Directory:</strong> {output_dir}</p>
                    <p><strong>Processing Started:</strong> {datetime.fromtimestamp(metadata.get('processing_start', 0)).strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        """

    def _generate_timeline_section(self, agent_results: Dict[str, Any]) -> str:
        """Generate the timeline section showing agent execution order."""

        # Sort agents by execution order (using execution_time as proxy for start order)
        sorted_agents = sorted(
            agent_results.items(),
            key=lambda x: x[1].get("execution_time", 0)
        )

        timeline_items = []
        for agent_name, result in sorted_agents:
            success = result.get("success", False)
            execution_time = result.get("execution_time", 0)
            reasoning = result.get("reasoning", "No reasoning provided")
            confidence = result.get("confidence", 0)

            # Extract model information
            model = self._extract_model_info(result, agent_name)

            status_class = "success" if success else "failed"

            timeline_items.append(f"""
                <div class="timeline-item {status_class}">
                    <div class="timeline-header">
                        <div class="agent-name">
                            {agent_name.replace('_', ' ').title()}
                        </div>
                        <div class="execution-time">
                            ⏱️ {execution_time:.2f}s
                        </div>
                    </div>
                    <p><strong>Status:</strong> {'✅ Success' if success else '❌ Failed'}</p>
                    <p><strong>Confidence:</strong> {confidence:.0%}</p>
                    <p><strong>Model:</strong> {model}</p>
                    <p style="margin-top: 10px; color: #6b7280;">{reasoning[:200]}...</p>
                </div>
            """)

        return f"""
            <div class="section">
                <h2 class="section-title">⏱️ Execution Timeline</h2>
                <div class="timeline">
                    {''.join(timeline_items)}
                </div>
            </div>
        """

    def _generate_mermaid_diagram(self, agent_results: Dict[str, Any]) -> str:
        """Generate Mermaid diagram showing agent execution flow."""

        # Sort agents by execution order
        sorted_agents = sorted(
            agent_results.items(),
            key=lambda x: x[1].get("execution_time", 0)
        )

        # Build Mermaid flowchart
        diagram_lines = ["graph TD"]
        diagram_lines.append("    Start([FOIA Request Input]) --> Coordinator")

        previous_node = "Coordinator"

        for i, (agent_name, result) in enumerate(sorted_agents):
            if agent_name == "coordinator":
                # Style coordinator
                success = result.get("success", False)
                style = "fill:#667eea,stroke:#764ba2,stroke-width:3px,color:#fff"
                diagram_lines.append(f"    Coordinator[Coordinator Agent]")
                diagram_lines.append(f"    style Coordinator {style}")
                continue

            # Create node name
            node_id = agent_name.replace('_', '')
            display_name = agent_name.replace('_', ' ').title()
            success = result.get("success", False)

            # Determine node shape and style based on success
            if success:
                node_shape_start = "["
                node_shape_end = "]"
                style = "fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff"
            else:
                node_shape_start = "["
                node_shape_end = "]"
                style = "fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff"

            # Add node connection
            diagram_lines.append(f"    {previous_node} --> {node_id}{node_shape_start}{display_name}{node_shape_end}")
            diagram_lines.append(f"    style {node_id} {style}")

            previous_node = node_id

        # Add final node
        diagram_lines.append(f"    {previous_node} --> End([Report Generated])")
        diagram_lines.append(f"    style End fill:#764ba2,stroke:#667eea,stroke-width:3px,color:#fff")

        return "\n".join(diagram_lines)

    def _extract_model_info(self, result: Dict[str, Any], agent_name: str) -> str:
        """Extract model information from agent result."""
        data = result.get("data", {})

        # Check for generation_metadata with model_used
        if "generation_metadata" in data:
            model = data["generation_metadata"].get("model_used", "")
            if model:
                return model

        # Fallback based on agent type
        model_map = {
            "coordinator": "nvidia/nvidia-nemotron-nano-9b-v2",
            "local_pdf_search": "nvidia/nvidia-nemotron-nano-9b-v2",
            "pdf_parser": "nvidia/nemotron-nano-12b-v2-vl",
            "document_researcher": "nvidia/nvidia-nemotron-nano-9b-v2",
            "public_foia_search": "nvidia/nvidia-nemotron-nano-9b-v2",
            "report_generator": "nvidia/nvidia-nemotron-nano-9b-v2",
            "html_report_generator": "Direct Processing (Non-LLM)"
        }

        return model_map.get(agent_name, "nvidia/nvidia-nemotron-nano-9b-v2")

    def _generate_details_section(self, agent_results: Dict[str, Any]) -> str:
        """Generate detailed results section for each agent."""

        agent_cards = []

        for agent_name, result in agent_results.items():
            success = result.get("success", False)
            confidence = result.get("confidence", 0)
            execution_time = result.get("execution_time", 0)
            reasoning = result.get("reasoning", "No reasoning provided")
            data = result.get("data", {})

            # Extract model information
            model = self._extract_model_info(result, agent_name)

            # Determine confidence badge class
            confidence_class = "confidence-high" if confidence >= 0.8 else ""

            # Format data for display (limit size)
            data_str = json.dumps(data, indent=2, default=str)
            if len(data_str) > 2000:
                data_str = data_str[:2000] + "\n... (truncated)"

            agent_cards.append(f"""
                <div class="agent-card">
                    <div class="agent-card-header">
                        <h3>{agent_name.replace('_', ' ').title()}</h3>
                        <div>
                            <span class="status-badge {'status-completed' if success else 'status-failed'}">
                                {'Success' if success else 'Failed'}
                            </span>
                            <span class="confidence-badge {confidence_class}">
                                Confidence: {confidence:.0%}
                            </span>
                        </div>
                    </div>

                    <p><strong>Execution Time:</strong> {execution_time:.2f} seconds</p>
                    <p><strong>Model Used:</strong> <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">{model}</code></p>

                    <div class="reasoning-box">
                        <h4>🧠 Agent Reasoning</h4>
                        <p>{reasoning}</p>
                    </div>

                    <div class="data-section">
                        <h4>📦 Result Data</h4>
                        <pre>{data_str}</pre>
                    </div>
                </div>
            """)

        return f"""
            <div class="section agent-details">
                <h2 class="section-title">🔍 Detailed Agent Results</h2>
                {''.join(agent_cards)}
            </div>
        """
