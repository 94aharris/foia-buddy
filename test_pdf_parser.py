#!/usr/bin/env python3
"""
Test script for PDF Parser Agent using nvidia/nemotron-parse model.
"""

import asyncio
import os
from pathlib import Path
from openai import OpenAI

from foia_buddy.agents.pdf_parser import PDFParserAgent
from foia_buddy.models import TaskMessage


async def test_pdf_parser():
    """Test the PDF parser agent with a sample PDF."""

    # Get NVIDIA API key from environment
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("ERROR: NVIDIA_API_KEY not found in environment")
        print("Please set it in your .env file or export it")
        return

    # Initialize NVIDIA client
    nvidia_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

    # Create PDF parser agent
    print("=" * 80)
    print("Testing PDF Parser Agent with nvidia/nemotron-parse")
    print("=" * 80)
    print()

    parser = PDFParserAgent(nvidia_client)

    # Print agent info
    print(f"Agent Name: {parser.name}")
    print(f"Model: {parser.model_name}")
    print(f"Available Parsing Tools: {', '.join(parser.tools)}")
    print(f"Default Tool: {parser.default_tool}")
    print()

    # Find test PDF
    pdf_path = Path("sample_data/pdfs/_DOCUMENTS_1-FY2012_F-2004-02207_DOC_0C17731322_C17731322.pdf")

    if not pdf_path.exists():
        print(f"ERROR: Test PDF not found at {pdf_path}")
        return

    print(f"Test PDF: {pdf_path.name}")
    print(f"File Size: {pdf_path.stat().st_size / 1024:.2f} KB")
    print()

    # Create task message
    task = TaskMessage(
        task_id="test-001",
        agent_type="pdf_parser",
        instructions=f"Parse the PDF document at {pdf_path} and convert it to markdown.",
        context={
            "pdf_paths": [str(pdf_path)],
            "output_dir": "test_output/parsed_documents"
        }
    )

    # Execute the parsing
    print("Starting PDF parsing...")
    print("-" * 80)
    print()

    try:
        result = await parser.execute(task)

        print("Parsing completed!")
        print("=" * 80)
        print()
        print("RESULT:")
        print("-" * 80)
        print(f"Success: {result.success}")
        print(f"Agent: {result.agent_name}")
        print(f"Execution Time: {result.execution_time:.2f} seconds")
        print(f"Confidence: {result.confidence}")
        print()

        if result.success:
            print("REASONING:")
            print("-" * 80)
            print(result.reasoning)
            print()

            print("PARSED DATA:")
            print("-" * 80)
            print(f"Parsed Count: {result.data.get('parsed_count', 0)}")
            print(f"Total PDFs: {result.data.get('total_pdfs', 0)}")
            print(f"Output Directory: {result.data.get('output_directory', 'N/A')}")
            print()

            if result.data.get('errors'):
                print("ERRORS:")
                for error in result.data['errors']:
                    print(f"  - {error['pdf_path']}: {error['error']}")
                print()

            if result.data.get('parsed_documents'):
                print("PARSED DOCUMENTS:")
                for doc in result.data['parsed_documents']:
                    print(f"  - {doc.get('pdf_name', 'Unknown')}")
                    print(f"    Markdown file: {doc.get('markdown_path', 'N/A')}")
                    if 'content_preview' in doc:
                        preview = doc['content_preview'][:200]
                        print(f"    Preview: {preview}...")
                print()

        else:
            print(f"PARSING FAILED")
            print(f"Data: {result.data}")

    except Exception as e:
        print(f"ERROR during parsing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run the test
    asyncio.run(test_pdf_parser())
