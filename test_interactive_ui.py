#!/usr/bin/env python3
"""Test script for Interactive UI Generator Agent"""

import asyncio
from pathlib import Path
from foia_buddy.agents import InteractiveUIGeneratorAgent
from foia_buddy.utils import NvidiaClient
from foia_buddy.models import TaskMessage


async def test_interactive_ui():
    """Test the interactive UI generator with existing output data."""

    # Initialize client and agent
    nvidia_client = NvidiaClient()  # Will use env var
    ui_generator = InteractiveUIGeneratorAgent(nvidia_client)

    # Use existing output directory
    output_dir = "output/dos-response"
    input_file = "sample_data/foia-request.md"

    print(f"🧪 Testing Interactive UI Generator")
    print(f"📂 Output directory: {output_dir}")
    print(f"📄 Input file: {input_file}")

    # Create task
    task = TaskMessage(
        task_id="test_ui_001",
        agent_type="interactive_ui_generator",
        instructions="Generate interactive tabbed UI for testing",
        context={
            "output_dir": output_dir,
            "input_file": input_file,
            "auto_open": False  # Don't auto-open during testing
        }
    )

    # Execute
    print("\n⏳ Executing agent...")
    result = await ui_generator.execute(task)

    # Display results
    print(f"\n{'='*60}")
    print(f"Success: {result.success}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Reasoning: {result.reasoning}")

    if result.success:
        ui_file = result.data.get("ui_file", "")
        tabs = result.data.get("tabs_generated", [])

        print(f"\n✅ UI generated successfully!")
        print(f"📍 Location: {ui_file}")
        print(f"📑 Tabs: {', '.join([str(t) for t in tabs if t])}")
        print(f"\n🌐 To view, open: file://{Path(ui_file).absolute()}")
    else:
        print(f"\n❌ Error: {result.data.get('error', 'Unknown error')}")

    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    asyncio.run(test_interactive_ui())
