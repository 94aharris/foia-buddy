from typing import Dict, Any
import json
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class InteractiveUIGeneratorAgent(BaseAgent):
    """Generates an interactive tabbed UI with FOIA request, final report, and processing details."""

    def __init__(self, nvidia_client):
        super().__init__(
            name="interactive_ui_generator",
            description="Creates interactive tabbed UI for comprehensive FOIA processing visualization",
            nvidia_client=nvidia_client
        )
        self.add_capability("ui_generation")
        self.add_capability("markdown_rendering")
        self.add_capability("interactive_visualization")

    def get_system_prompt(self) -> str:
        return """You are the Interactive UI Generator Agent for FOIA-Buddy.

Your role is to:
1. CREATE a tabbed interface with FOIA request, final report, and processing workflow
2. RENDER markdown content beautifully with syntax highlighting
3. PROVIDE an intuitive, professional user experience
4. AUTO-OPEN the interface in the default browser when processing completes

Interface Requirements:
- Modern tabbed navigation (FOIA Request | Final Report | Processing Workflow)
- Beautiful markdown rendering with GitHub-flavored markdown support
- Responsive design that works on all screen sizes
- Smooth transitions and professional aesthetics
- Integration with existing processing_report.html via iframe/embed"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute interactive UI generation task."""
        start_time = time.time()

        try:
            # Get paths from task context
            output_dir = Path(task.context.get("output_dir", ""))
            input_file = task.context.get("input_file", "")
            auto_open = task.context.get("auto_open", True)

            if not output_dir.exists():
                return self._create_result(
                    task.task_id,
                    success=False,
                    data={"error": f"Output directory not found: {output_dir}"},
                    reasoning="Cannot generate UI without valid output directory",
                    confidence=0.0,
                    start_time=start_time
                )

            # Read source files
            foia_request_content = self._read_file(input_file)
            final_report_content = self._read_file(output_dir / "final_report.md")
            processing_report_path = output_dir / "processing_report.html"
            metadata_path = output_dir / "processing_metadata.json"

            # Check if processing report exists and read metadata
            has_processing_report = processing_report_path.exists()
            processing_metadata = {}
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        processing_metadata = json.load(f)
                except:
                    pass

            # Generate interactive UI HTML
            html_content = self._generate_interactive_ui(
                foia_request_content,
                final_report_content,
                has_processing_report,
                processing_metadata
            )

            # Save interactive UI
            ui_output_path = output_dir / "interactive_viewer.html"
            with open(ui_output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Auto-open in browser if requested
            if auto_open:
                try:
                    webbrowser.open(f"file://{ui_output_path.absolute()}")
                except Exception as e:
                    # Non-critical error - just log it
                    pass

            result_data = {
                "ui_file": str(ui_output_path),
                "auto_opened": auto_open,
                "tabs_generated": [
                    "FOIA Request",
                    "Final Report",
                    "Processing Workflow" if has_processing_report else None
                ],
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "output_directory": str(output_dir)
                }
            }

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning="Successfully generated interactive tabbed UI and opened in browser",
                confidence=0.95,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during interactive UI generation: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    def _read_file(self, file_path) -> str:
        """Read file content safely."""
        try:
            path = Path(file_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return "# Content Not Available\n\nThe requested content could not be loaded."

    def _generate_interactive_ui(
        self,
        foia_request: str,
        final_report: str,
        has_processing_report: bool,
        processing_metadata: Dict[str, Any]
    ) -> str:
        """Generate the interactive tabbed UI HTML."""

        # Escape content for safe embedding
        foia_request_safe = self._escape_for_js(foia_request)
        final_report_safe = self._escape_for_js(final_report)

        # Generate workflow HTML content from metadata
        workflow_html = self._generate_workflow_html(processing_metadata) if has_processing_report else ""

        # Generate tab buttons HTML
        tabs_html = """
            <button class="tab-button active" onclick="openTab(event, 'foia-request')">
                📄 FOIA Request
            </button>
            <button class="tab-button" onclick="openTab(event, 'final-report')">
                📋 Final Report
            </button>
        """

        if has_processing_report:
            tabs_html += """
            <button class="tab-button" onclick="openTab(event, 'processing-workflow')">
                🔄 Processing Workflow
            </button>
            """

        # Generate tab content HTML
        workflow_tab = ""
        if has_processing_report:
            workflow_tab = f"""
            <div id="processing-workflow" class="tab-content">
                <div class="workflow-container">
                    {workflow_html}
                </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FOIA-Buddy Interactive Viewer</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.0/github-markdown.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked@11.0.0/marked.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            height: 100vh;
            overflow: hidden;
        }}

        .app-container {{
            display: flex;
            flex-direction: column;
            height: 100vh;
        }}

        .header {{
            background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
            color: white;
            padding: 20px 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            z-index: 10;
        }}

        .header h1 {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .header p {{
            font-size: 1em;
            opacity: 0.95;
        }}

        .header .logo {{
            font-size: 1.5em;
        }}

        .tab-container {{
            background: #1e293b;
            border-bottom: 2px solid #334155;
            display: flex;
            padding: 0 40px;
            gap: 5px;
        }}

        .tab-button {{
            background: transparent;
            border: none;
            color: #94a3b8;
            padding: 15px 30px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .tab-button:hover {{
            background: #334155;
            color: #e2e8f0;
        }}

        .tab-button.active {{
            color: #10b981;
            border-bottom-color: #10b981;
            background: #0f172a;
        }}

        .content-container {{
            flex: 1;
            overflow: hidden;
            position: relative;
        }}

        .tab-content {{
            display: none;
            height: 100%;
            overflow-y: auto;
            background: #0f172a;
            padding: 40px;
        }}

        .tab-content.active {{
            display: block;
        }}

        .markdown-body {{
            background: #1e293b;
            color: #e2e8f0;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            max-width: 1000px;
            margin: 0 auto;
        }}

        .markdown-body h1,
        .markdown-body h2,
        .markdown-body h3,
        .markdown-body h4,
        .markdown-body h5,
        .markdown-body h6 {{
            color: #f1f5f9;
            border-bottom-color: #334155;
            margin-top: 24px;
            margin-bottom: 16px;
        }}

        .markdown-body h1 {{
            color: #10b981;
            font-size: 2.5em;
        }}

        .markdown-body h2 {{
            color: #34d399;
            font-size: 2em;
        }}

        .markdown-body a {{
            color: #10b981;
        }}

        .markdown-body a:hover {{
            color: #34d399;
        }}

        .markdown-body code {{
            background: #0f172a;
            color: #fbbf24;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
        }}

        .markdown-body pre {{
            background: #0f172a;
            border: 1px solid #334155;
        }}

        .markdown-body pre code {{
            color: #e2e8f0;
        }}

        .markdown-body blockquote {{
            color: #cbd5e1;
            border-left-color: #10b981;
            background: #1e293b;
        }}

        .markdown-body table tr {{
            background: #1e293b;
            border-top-color: #334155;
        }}

        .markdown-body table tr:nth-child(2n) {{
            background: #0f172a;
        }}

        .markdown-body table th,
        .markdown-body table td {{
            border-color: #334155;
        }}

        .markdown-body hr {{
            background-color: #334155;
            border: none;
            height: 2px;
        }}

        .markdown-body ul li::marker {{
            color: #10b981;
        }}

        .markdown-body strong {{
            color: #f1f5f9;
        }}

        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 12px;
        }}

        ::-webkit-scrollbar-track {{
            background: #1e293b;
        }}

        ::-webkit-scrollbar-thumb {{
            background: #475569;
            border-radius: 6px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: #64748b;
        }}

        /* Loading animation */
        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
            color: #94a3b8;
            font-size: 1.2em;
        }}

        /* Workflow container styles */
        .workflow-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .workflow-section {{
            background: #1e293b;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .workflow-section h2 {{
            color: #10b981;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #10b981;
        }}

        .workflow-section h3 {{
            color: #34d399;
            font-size: 1.3em;
            margin-top: 20px;
            margin-bottom: 15px;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}

        .metric-box {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}

        .metric-box .label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }}

        .metric-box .value {{
            font-size: 2em;
            font-weight: 700;
        }}

        .agent-timeline {{
            position: relative;
            padding-left: 30px;
            margin: 20px 0;
        }}

        .agent-timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #10b981;
        }}

        .agent-item {{
            position: relative;
            margin-bottom: 25px;
            padding: 15px 20px;
            background: #0f172a;
            border-radius: 8px;
            border-left: 4px solid #10b981;
        }}

        .agent-item::before {{
            content: '';
            position: absolute;
            left: -37px;
            top: 15px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #10b981;
            border: 3px solid #1e293b;
        }}

        .agent-item.success::before {{
            background: #10b981;
        }}

        .agent-item.failed::before {{
            background: #ef4444;
        }}

        .agent-name {{
            font-size: 1.2em;
            font-weight: 600;
            color: #10b981;
            margin-bottom: 8px;
        }}

        .agent-details {{
            font-size: 0.9em;
            color: #94a3b8;
            line-height: 1.6;
        }}

        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }}

        .status-success {{
            background: #10b981;
            color: white;
        }}

        .status-failed {{
            background: #ef4444;
            color: white;
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            .header {{
                padding: 15px 20px;
            }}

            .header h1 {{
                font-size: 1.5em;
            }}

            .tab-container {{
                padding: 0 20px;
                overflow-x: auto;
            }}

            .tab-button {{
                padding: 12px 20px;
                font-size: 0.9em;
                white-space: nowrap;
            }}

            .tab-content {{
                padding: 20px;
            }}

            .markdown-body {{
                padding: 20px;
            }}

            .workflow-section {{
                padding: 20px;
            }}

            .metric-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header">
            <h1><span class="logo">🤖</span> FOIA-Buddy Interactive Viewer</h1>
            <p>Multi-Agent AI System for FOIA Request Processing</p>
        </div>

        <div class="tab-container">
            {tabs_html}
        </div>

        <div class="content-container">
            <div id="foia-request" class="tab-content active">
                <div class="markdown-body" id="foia-request-content">
                    <div class="loading">Loading FOIA Request...</div>
                </div>
            </div>

            <div id="final-report" class="tab-content">
                <div class="markdown-body" id="final-report-content">
                    <div class="loading">Loading Final Report...</div>
                </div>
            </div>

            {workflow_tab}
        </div>
    </div>

    <script>
        // Configure marked for GitHub-flavored markdown
        marked.setOptions({{
            breaks: true,
            gfm: true,
            headerIds: true,
            mangle: false
        }});

        // Content data
        const foiaRequestMarkdown = `{foia_request_safe}`;
        const finalReportMarkdown = `{final_report_safe}`;

        // Render markdown content
        document.addEventListener('DOMContentLoaded', function() {{
            const foiaContent = document.getElementById('foia-request-content');
            const reportContent = document.getElementById('final-report-content');

            try {{
                foiaContent.innerHTML = marked.parse(foiaRequestMarkdown);
            }} catch (e) {{
                foiaContent.innerHTML = '<p style="color: #ef4444;">Error rendering FOIA request content.</p>';
            }}

            try {{
                reportContent.innerHTML = marked.parse(finalReportMarkdown);
            }} catch (e) {{
                reportContent.innerHTML = '<p style="color: #ef4444;">Error rendering final report content.</p>';
            }}
        }});

        // Tab switching function
        function openTab(evt, tabName) {{
            // Hide all tab contents
            const tabContents = document.getElementsByClassName('tab-content');
            for (let i = 0; i < tabContents.length; i++) {{
                tabContents[i].classList.remove('active');
            }}

            // Remove active class from all buttons
            const tabButtons = document.getElementsByClassName('tab-button');
            for (let i = 0; i < tabButtons.length; i++) {{
                tabButtons[i].classList.remove('active');
            }}

            // Show the selected tab
            document.getElementById(tabName).classList.add('active');
            evt.currentTarget.classList.add('active');
        }}

        // Keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.ctrlKey || e.metaKey) {{
                const tabs = ['foia-request', 'final-report', {'processing-workflow' if has_processing_report else 'null'}].filter(t => t !== null);
                const buttons = document.querySelectorAll('.tab-button');

                if (e.key === '1' && tabs[0]) {{
                    buttons[0].click();
                }} else if (e.key === '2' && tabs[1]) {{
                    buttons[1].click();
                }} else if (e.key === '3' && tabs[2]) {{
                    buttons[2].click();
                }}
            }}
        }});
    </script>
</body>
</html>"""

        return html

    def _escape_for_js(self, content: str) -> str:
        """Escape content for safe JavaScript embedding."""
        # Replace backticks and backslashes
        content = content.replace('\\', '\\\\')
        content = content.replace('`', '\\`')
        content = content.replace('${', '\\${')
        return content

    def _generate_workflow_html(self, metadata: Dict[str, Any]) -> str:
        """Generate workflow HTML content from processing metadata."""
        if not metadata:
            return "<p>No processing metadata available.</p>"

        # Extract key information
        agent_results = metadata.get("agent_results", {})
        status = metadata.get("status", "unknown")
        total_time = metadata.get("processing_time", 0)
        input_file = metadata.get("input_file", "Unknown")
        output_dir = metadata.get("output_directory", "Unknown")

        # Count successful agents
        successful_agents = sum(1 for result in agent_results.values() if result.get("success", False))
        total_agents = len(agent_results)

        # Generate summary section
        summary_html = f"""
        <div class="workflow-section">
            <h2>📊 Processing Summary</h2>
            <div class="metric-grid">
                <div class="metric-box">
                    <div class="label">Total Time</div>
                    <div class="value">{total_time:.1f}s</div>
                </div>
                <div class="metric-box">
                    <div class="label">Agents Executed</div>
                    <div class="value">{total_agents}</div>
                </div>
                <div class="metric-box">
                    <div class="label">Successful</div>
                    <div class="value">{successful_agents}</div>
                </div>
                <div class="metric-box">
                    <div class="label">Success Rate</div>
                    <div class="value">{(successful_agents/max(total_agents,1)*100):.0f}%</div>
                </div>
            </div>
            <p style="color: #94a3b8; margin-top: 20px;"><strong>Input:</strong> {input_file}</p>
            <p style="color: #94a3b8;"><strong>Output:</strong> {output_dir}</p>
            <p style="color: #94a3b8;"><strong>Status:</strong> <span class="status-badge status-{'success' if status == 'completed' else 'failed'}">{status.upper()}</span></p>
        </div>
        """

        # Generate agent timeline
        timeline_items = []
        for agent_name, result in agent_results.items():
            success = result.get("success", False)
            execution_time = result.get("execution_time", 0)
            reasoning = result.get("reasoning", "No reasoning provided")
            confidence = result.get("confidence", 0)

            # Get model used
            model = "Unknown"
            if "data" in result and isinstance(result["data"], dict):
                gen_meta = result["data"].get("generation_metadata", {})
                if isinstance(gen_meta, dict):
                    model = gen_meta.get("model_used", "Unknown")

            status_class = "success" if success else "failed"
            status_text = "✅ Success" if success else "❌ Failed"

            timeline_items.append(f"""
            <div class="agent-item {status_class}">
                <div class="agent-name">
                    {agent_name.replace('_', ' ').title()}
                    <span class="status-badge status-{status_class}">{status_text}</span>
                </div>
                <div class="agent-details">
                    <p><strong>Execution Time:</strong> {execution_time:.2f}s</p>
                    <p><strong>Confidence:</strong> {confidence:.0%}</p>
                    <p><strong>Model:</strong> {model}</p>
                    <p style="margin-top: 10px; font-style: italic;">{reasoning[:200]}{'...' if len(reasoning) > 200 else ''}</p>
                </div>
            </div>
            """)

        timeline_html = f"""
        <div class="workflow-section">
            <h2>⏱️ Agent Execution Timeline</h2>
            <div class="agent-timeline">
                {''.join(timeline_items)}
            </div>
        </div>
        """

        return summary_html + timeline_html
