from typing import Dict, Any, List
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class LauncherUIGeneratorAgent(BaseAgent):
    """Generates a launcher UI for selecting and viewing FOIA processing reports."""

    def __init__(self, nvidia_client):
        super().__init__(
            name="launcher_ui_generator",
            description="Creates launcher UI for selecting and viewing FOIA reports",
            nvidia_client=nvidia_client
        )
        self.add_capability("ui_generation")
        self.add_capability("report_listing")

    def get_system_prompt(self) -> str:
        return """You are the Launcher UI Generator Agent for FOIA-Buddy.

Your role is to:
1. CREATE a launcher interface for selecting and viewing FOIA processing reports
2. SCAN the output directory for available reports
3. PROVIDE quick access buttons to view interactive reports
4. DISPLAY processing status and metadata for each report"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute launcher UI generation task."""
        start_time = time.time()

        try:
            # Get output directory from task context
            output_base_dir = Path(task.context.get("output_dir", "output"))
            auto_open = task.context.get("auto_open", False)

            if not output_base_dir.exists():
                output_base_dir.mkdir(parents=True, exist_ok=True)

            # Scan for available reports
            reports = self._scan_reports(output_base_dir)

            # Generate launcher HTML
            html_content = self._generate_launcher_html(reports, str(output_base_dir))

            # Save launcher UI
            launcher_path = output_base_dir / "index.html"
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Auto-open if requested
            if auto_open:
                try:
                    webbrowser.open(f"file://{launcher_path.absolute()}")
                except Exception:
                    pass

            result_data = {
                "launcher_file": str(launcher_path),
                "reports_found": len(reports),
                "auto_opened": auto_open,
                "generation_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "output_directory": str(output_base_dir)
                }
            }

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning=f"Successfully generated launcher UI with {len(reports)} reports",
                confidence=0.95,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during launcher UI generation: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    def _scan_reports(self, output_dir: Path) -> List[Dict[str, Any]]:
        """Scan output directory for available reports."""
        reports = []

        if not output_dir.exists():
            return reports

        # Look for subdirectories with interactive_viewer.html
        for item in output_dir.iterdir():
            if item.is_dir():
                viewer_path = item / "interactive_viewer.html"
                metadata_path = item / "processing_metadata.json"
                final_report_path = item / "final_report.md"

                if viewer_path.exists():
                    # Read metadata if available
                    status = "completed"
                    processing_time = 0.0
                    input_file = "Unknown"

                    if metadata_path.exists():
                        try:
                            import json
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                                status = metadata.get("status", "completed")
                                processing_time = metadata.get("processing_time", 0.0)
                                input_file = Path(metadata.get("input_file", "Unknown")).name
                        except:
                            pass

                    reports.append({
                        "name": item.name,
                        "path": str(item),
                        "viewer_path": str(viewer_path.relative_to(output_dir)),
                        "has_final_report": final_report_path.exists(),
                        "status": status,
                        "processing_time": processing_time,
                        "input_file": input_file,
                        "modified_time": datetime.fromtimestamp(viewer_path.stat().st_mtime)
                    })

        # Sort by modified time (newest first)
        reports.sort(key=lambda x: x["modified_time"], reverse=True)
        return reports

    def _generate_launcher_html(self, reports: List[Dict[str, Any]], output_dir: str) -> str:
        """Generate the launcher UI HTML."""

        # Generate report cards
        report_cards_html = ""
        if reports:
            for report in reports:
                status_color = "#10b981" if report["status"] == "completed" else "#ef4444"
                status_icon = "✅" if report["status"] == "completed" else "❌"

                report_cards_html += f"""
                <div class="report-card">
                    <div class="report-header">
                        <h3>{report["name"]}</h3>
                        <span class="status-badge" style="background: {status_color};">
                            {status_icon} {report["status"].upper()}
                        </span>
                    </div>
                    <div class="report-details">
                        <p><strong>Input:</strong> {report["input_file"]}</p>
                        <p><strong>Processing Time:</strong> {report["processing_time"]:.2f}s</p>
                        <p><strong>Last Modified:</strong> {report["modified_time"].strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    <div class="report-actions">
                        <a href="{report["viewer_path"]}" class="view-button" target="_blank">
                            🌐 View Report
                        </a>
                    </div>
                </div>
                """
        else:
            report_cards_html = """
            <div class="empty-state">
                <h3>No reports found</h3>
                <p>Process a FOIA request to generate reports that will appear here.</p>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FOIA-Buddy Launcher</title>
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
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 40px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }}

        .header h1 {{
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: #1e293b;
            padding: 25px;
            border-radius: 12px;
            border-left: 4px solid #10b981;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .stat-card .label {{
            color: #94a3b8;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}

        .stat-card .value {{
            color: #10b981;
            font-size: 2.5em;
            font-weight: 700;
        }}

        .reports-section {{
            margin-top: 40px;
        }}

        .reports-section h2 {{
            color: #10b981;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #10b981;
        }}

        .reports-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }}

        .report-card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}

        .report-card:hover {{
            border-color: #10b981;
            box-shadow: 0 8px 16px rgba(16, 185, 129, 0.2);
            transform: translateY(-2px);
        }}

        .report-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 20px;
            gap: 15px;
        }}

        .report-header h3 {{
            color: #e2e8f0;
            font-size: 1.3em;
            font-weight: 600;
            flex: 1;
        }}

        .status-badge {{
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            white-space: nowrap;
            color: white;
        }}

        .report-details {{
            margin-bottom: 20px;
            color: #94a3b8;
            font-size: 0.9em;
            line-height: 1.8;
        }}

        .report-details p {{
            margin-bottom: 5px;
        }}

        .report-details strong {{
            color: #cbd5e1;
        }}

        .report-actions {{
            display: flex;
            gap: 10px;
        }}

        .view-button {{
            display: inline-block;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.95em;
            transition: all 0.3s ease;
            flex: 1;
            text-align: center;
        }}

        .view-button:hover {{
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
            transform: translateY(-1px);
        }}

        .empty-state {{
            background: #1e293b;
            padding: 60px 40px;
            border-radius: 12px;
            text-align: center;
            border: 2px dashed #334155;
        }}

        .empty-state h3 {{
            color: #94a3b8;
            font-size: 1.5em;
            margin-bottom: 10px;
        }}

        .empty-state p {{
            color: #64748b;
            font-size: 1em;
        }}

        .footer {{
            margin-top: 60px;
            padding: 30px;
            text-align: center;
            color: #64748b;
            background: #1e293b;
            border-radius: 12px;
        }}

        .footer p {{
            margin-bottom: 5px;
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .reports-grid {{
                grid-template-columns: 1fr;
            }}

            .stats {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span>🤖</span> FOIA-Buddy Launcher</h1>
            <p>Multi-Agent AI System for FOIA Request Processing</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="label">Total Reports</div>
                <div class="value">{len(reports)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Output Directory</div>
                <div class="value" style="font-size: 1em; color: #94a3b8; word-break: break-all;">{output_dir}</div>
            </div>
        </div>

        <div class="reports-section">
            <h2>📊 Available Reports</h2>
            <div class="reports-grid">
                {report_cards_html}
            </div>
        </div>

        <div class="footer">
            <p><strong>FOIA-Buddy</strong> - Intelligent FOIA Request Processing</p>
            <p>Powered by NVIDIA Nemotron Models</p>
            <p style="margin-top: 15px; font-size: 0.9em;">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </div>

    <script>
        // Auto-refresh every 30 seconds to check for new reports
        setTimeout(() => {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>"""

        return html
