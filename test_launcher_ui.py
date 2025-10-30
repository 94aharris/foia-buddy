#!/usr/bin/env python3
"""Test script for Launcher UI Generator Agent"""

import asyncio
from pathlib import Path
from foia_buddy.agents import LauncherUIGeneratorAgent
from foia_buddy.utils import NvidiaClient
from foia_buddy.models import TaskMessage


async def test_launcher_ui():
    """Test the launcher UI generator with existing output data."""

    # Initialize client and agent
    nvidia_client = NvidiaClient()  # Will use env var
    launcher_generator = LauncherUIGeneratorAgent(nvidia_client)

    # Use existing output directory
    output_dir = "output"

    print(f"🧪 Testing Launcher UI Generator")
    print(f"📂 Output directory: {output_dir}")

    # Create task
    task = TaskMessage(
        task_id="test_launcher_001",
        agent_type="launcher_ui_generator",
        instructions="Generate launcher UI for testing",
        context={
            "output_dir": output_dir,
            "auto_open": False  # Don't auto-open during testing
        }
    )

    # Execute
    print("\n⏳ Executing agent...")
    result = await launcher_generator.execute(task)

    # Display results
    print(f"\n{'='*60}")
    print(f"Success: {result.success}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Reasoning: {result.reasoning}")

    if result.success:
        launcher_file = result.data.get("launcher_file", "")
        reports_found = result.data.get("reports_found", 0)

        print(f"\n✅ Launcher generated successfully!")
        print(f"📍 Location: {launcher_file}")
        print(f"📊 Reports found: {reports_found}")
        print(f"\n🌐 To view, open: file://{Path(launcher_file).absolute()}")
    else:
        print(f"\n❌ Error: {result.data.get('error', 'Unknown error')}")

    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    asyncio.run(test_launcher_ui())
