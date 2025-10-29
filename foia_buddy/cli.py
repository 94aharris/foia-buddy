import click
import os
import asyncio
from pathlib import Path
from typing import Dict, Any
import time
import json

from .utils import NvidiaClient
from .agents import (
    AgentRegistry,
    CoordinatorAgent,
    DocumentResearcherAgent,
    ReportGeneratorAgent,
    PublicFOIASearchAgent
)
from .models import TaskMessage, FOIARequest


class FOIAProcessor:
    """Main FOIA processing orchestrator."""

    def __init__(self, nvidia_api_key: str = None):
        self.nvidia_client = NvidiaClient(nvidia_api_key)
        self.registry = AgentRegistry()
        self._setup_agents()

    def _setup_agents(self):
        """Initialize and register all agents."""
        # Create agents
        coordinator = CoordinatorAgent(self.nvidia_client)
        doc_researcher = DocumentResearcherAgent(self.nvidia_client)
        public_foia_search = PublicFOIASearchAgent(self.nvidia_client)
        report_generator = ReportGeneratorAgent(self.nvidia_client)

        # Register agents
        self.registry.register(coordinator)
        self.registry.register(doc_researcher)
        self.registry.register(public_foia_search)
        self.registry.register(report_generator)

    async def process_foia_request(self, input_file: str, output_dir: str) -> Dict[str, Any]:
        """Process a FOIA request through the agent pipeline."""

        # Read FOIA request
        foia_content = self._read_foia_request(input_file)
        if not foia_content:
            return {"error": f"Could not read FOIA request from {input_file}"}

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {
            "processing_start": time.time(),
            "input_file": input_file,
            "output_directory": output_dir,
            "agent_results": {}
        }

        try:
            # Step 1: Coordinate the request
            click.echo("🤖 Starting FOIA request coordination...")
            coordinator = self.registry.get_agent("coordinator")

            coord_task = TaskMessage(
                task_id="coord_001",
                agent_type="coordinator",
                instructions="Analyze FOIA request and create execution plan",
                context={"foia_request": foia_content}
            )

            coord_result = await coordinator.execute(coord_task)
            results["agent_results"]["coordinator"] = coord_result.dict()

            if not coord_result.success:
                return {**results, "error": "Coordination failed", "status": "failed"}

            click.echo(f"✅ Coordination complete. Plan: {coord_result.data.get('execution_sequence', [])}")

            # Step 2: Search public FOIA library
            click.echo("🔍 Searching public FOIA library...")
            public_search = self.registry.get_agent("public_foia_search")

            public_task = TaskMessage(
                task_id="public_search_001",
                agent_type="public_foia_search",
                instructions="Search public FOIA library for previously released documents",
                context={
                    "foia_request": foia_content,
                    "coordination_plan": coord_result.data
                }
            )

            public_result = await public_search.execute(public_task)
            results["agent_results"]["public_foia_search"] = public_result.dict()

            if not public_result.success:
                click.echo("⚠️ Public FOIA search encountered issues, continuing...")
            else:
                click.echo(f"✅ Public search complete. Found {public_result.data.get('total_documents_found', 0)} publicly available documents")

            # Step 3: Execute local document research
            click.echo("📚 Starting local document research...")
            doc_researcher = self.registry.get_agent("document_researcher")

            research_task = TaskMessage(
                task_id="research_001",
                agent_type="document_researcher",
                instructions="Search for documents relevant to FOIA request",
                context={
                    "foia_request": foia_content,
                    "coordination_plan": coord_result.data,
                    "public_documents": public_result.data if public_result.success else {}
                }
            )

            research_result = await doc_researcher.execute(research_task)
            results["agent_results"]["document_researcher"] = research_result.dict()

            if not research_result.success:
                click.echo("⚠️ Local document research failed, continuing with available data...")

            click.echo(f"✅ Local research complete. Found {research_result.data.get('relevant_documents_found', 0)} relevant documents")

            # Step 4: Generate report
            click.echo("📝 Generating final report...")
            report_generator = self.registry.get_agent("report_generator")

            report_task = TaskMessage(
                task_id="report_001",
                agent_type="report_generator",
                instructions="Generate comprehensive FOIA response report",
                context={
                    "foia_request": foia_content,
                    "research_results": research_result.data,
                    "public_foia_results": public_result.data if public_result.success else {},
                    "coordination_plan": coord_result.data
                }
            )

            report_result = await report_generator.execute(report_task)
            results["agent_results"]["report_generator"] = report_result.dict()

            if not report_result.success:
                return {**results, "error": "Report generation failed", "status": "failed"}

            click.echo("✅ Report generation complete")

            # Step 5: Save outputs
            self._save_outputs(output_path, report_result.data, results)

            results["status"] = "completed"
            results["processing_time"] = time.time() - results["processing_start"]

            click.echo(f"🎉 FOIA processing complete! Results saved to: {output_dir}")
            return results

        except Exception as e:
            results["error"] = str(e)
            results["status"] = "failed"
            return results

    def _read_foia_request(self, file_path: str) -> str:
        """Read FOIA request from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            click.echo(f"Error reading FOIA request: {e}")
            return ""

    def _save_outputs(self, output_path: Path, report_data: Dict[str, Any], results: Dict[str, Any]):
        """Save all outputs to the specified directory."""

        # Save main report
        report_file = output_path / "final_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_data.get("report_content", "No report content generated"))

        # Save executive summary
        summary_file = output_path / "executive_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(report_data.get("executive_summary", "No summary available"))

        # Save compliance notes
        compliance_file = output_path / "compliance_notes.md"
        with open(compliance_file, 'w', encoding='utf-8') as f:
            f.write(report_data.get("compliance_notes", "No compliance notes"))

        # Save processing metadata
        metadata_file = output_path / "processing_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        # Save redaction flags if any
        if report_data.get("redaction_flags"):
            redaction_file = output_path / "redaction_review.txt"
            with open(redaction_file, 'w', encoding='utf-8') as f:
                f.write("REDACTION REVIEW REQUIRED\n")
                f.write("=" * 30 + "\n\n")
                for flag in report_data["redaction_flags"]:
                    f.write(f"- {flag}\n")


@click.command()
@click.option('-i', '--input', 'input_file', required=True,
              help='Path to the FOIA request markdown file')
@click.option('-o', '--output', 'output_dir', required=True,
              help='Output directory for results')
@click.option('--api-key', envvar='NVIDIA_API_KEY',
              help='NVIDIA API key (or set NVIDIA_API_KEY env var)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(input_file: str, output_dir: str, api_key: str, verbose: bool):
    """FOIA-Buddy: Agentic FOIA request processing using NVIDIA Nemotron."""

    if not api_key:
        click.echo("❌ Error: NVIDIA API key required. Set NVIDIA_API_KEY environment variable or use --api-key")
        return

    if not os.path.exists(input_file):
        click.echo(f"❌ Error: Input file not found: {input_file}")
        return

    click.echo("🚀 FOIA-Buddy Starting...")
    click.echo(f"📄 Input: {input_file}")
    click.echo(f"📁 Output: {output_dir}")

    processor = FOIAProcessor(api_key)

    # Run the async processor
    try:
        results = asyncio.run(processor.process_foia_request(input_file, output_dir))

        if verbose:
            click.echo("\n📊 Processing Results:")
            click.echo(json.dumps(results, indent=2, default=str))

        if results.get("status") == "completed":
            click.echo(f"\n✅ Success! Processing completed in {results.get('processing_time', 0):.2f} seconds")
        else:
            click.echo(f"\n❌ Failed: {results.get('error', 'Unknown error')}")

    except Exception as e:
        click.echo(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    main()