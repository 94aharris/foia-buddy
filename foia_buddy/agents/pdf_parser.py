from typing import List, Dict, Any, Optional
import time
import base64
import json
import io
import mimetypes
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class PDFParserAgent(BaseAgent):
    """
    Parses PDF documents using NVIDIA Nemotron Parse model to convert them to markdown.

    This agent uses the Nemotron Parse model for enhanced document understanding,
    including scanned PDFs, visual elements, and complex layouts. It makes it easier
    for other agents and end-users to evaluate document content by converting PDFs
    to well-formatted markdown with visual element descriptions.
    """

    def __init__(self, nvidia_client):
        super().__init__(
            name="pdf_parser",
            description="Converts PDF documents to markdown using NVIDIA Nemotron Parse model",
            nvidia_client=nvidia_client
        )
        self.parse_api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model_name = "nvidia/nemotron-parse"
        # Available parsing tools
        self.tools = [
            "markdown_bbox",     # Markdown with bounding boxes
            "markdown_no_bbox",  # Markdown without bounding boxes
            "detection_only",    # Detection only
        ]
        self.default_tool = "markdown_no_bbox"  # Default to markdown without bbox
        self.add_capability("pdf_parsing")
        self.add_capability("document_conversion")
        self.add_capability("markdown_generation")
        self.add_capability("visual_understanding")
        self.add_capability("ocr")

    def get_system_prompt(self) -> str:
        return """You are the PDF Parser Agent for FOIA-Buddy using NVIDIA Nemotron Parse.

Your role is to:
1. PARSE PDF documents using NVIDIA's specialized document parsing model
2. CONVERT PDFs to well-formatted markdown with visual element descriptions
3. EXTRACT text, tables, charts, diagrams, and structure from documents
4. DESCRIBE visual elements (charts, graphs, images) in natural language
5. HANDLE scanned documents with OCR-like capabilities
6. PROVIDE comprehensive markdown for other agents and end-users

When parsing PDFs:
- Extract all text accurately, including from scanned documents
- Preserve document structure (headings, lists, tables)
- Describe charts, graphs, and visual elements in detail
- Maintain formatting and layout information
- Handle complex multi-column layouts
- Convert tables to markdown format
- Flag any parsing errors or issues

Output markdown that is:
- Clean and well-formatted
- Includes detailed descriptions of visual elements
- Easy for other agents to analyze
- Readable for human reviewers
- Preserves important document metadata
- Accessible with alternative text for visual content"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute PDF parsing task."""
        start_time = time.time()

        try:
            # Get PDF paths from task context
            pdf_paths = task.context.get("pdf_paths", [])
            output_dir = task.context.get("output_dir", "parsed_pdfs")

            if not pdf_paths:
                return self._create_result(
                    task.task_id,
                    success=True,
                    data={
                        "parsed_count": 0,
                        "message": "No PDFs to parse"
                    },
                    reasoning="No PDF documents provided for parsing",
                    confidence=1.0,
                    start_time=start_time
                )

            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Parse each PDF
            parsed_results = []
            errors = []

            for pdf_path in pdf_paths:
                try:
                    result = await self._parse_pdf(pdf_path, output_path)
                    parsed_results.append(result)
                except Exception as e:
                    errors.append({
                        "pdf_path": pdf_path,
                        "error": str(e)
                    })

            result_data = {
                "parsed_count": len(parsed_results),
                "total_pdfs": len(pdf_paths),
                "parsed_documents": parsed_results,
                "errors": errors,
                "output_directory": str(output_path)
            }

            success = len(parsed_results) > 0
            reasoning = f"Successfully parsed {len(parsed_results)} of {len(pdf_paths)} PDF documents"

            if errors:
                reasoning += f" ({len(errors)} errors encountered)"

            return self._create_result(
                task.task_id,
                success=success,
                data=result_data,
                reasoning=reasoning,
                confidence=0.9 if not errors else 0.7,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during PDF parsing: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    async def _parse_pdf(self, pdf_path: str, output_dir: Path) -> Dict[str, Any]:
        """
        Parse a single PDF document using NVIDIA Nemotron VL model.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save markdown output

        Returns:
            Dictionary with parsing results
        """
        pdf_file = Path(pdf_path)

        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Convert PDF to images first (nemotron-parse requires images, not PDFs)
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError(
                "pdf2image library required for PDF parsing. "
                "Install with: pip install pdf2image\n"
                "Also requires poppler-utils: brew install poppler (macOS) or apt-get install poppler-utils (Linux)"
            )

        # Convert PDF pages to images
        images = convert_from_path(str(pdf_file), dpi=200)

        # Parse each page
        page_markdowns = []
        for page_num, image in enumerate(images, start=1):
            # Convert PIL Image to base64
            import io
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            b64_str = base64.b64encode(image_bytes).decode('ascii')

            # Call Parse model to convert page to markdown
            page_markdown = await self._call_vl_model(b64_str, "image/png")
            page_markdowns.append(f"# Page {page_num}\n\n{page_markdown}")

        # Combine all pages
        markdown_content = "\n\n---\n\n".join(page_markdowns)

        # Save markdown to file
        markdown_filename = pdf_file.stem + ".md"
        markdown_path = output_dir / markdown_filename

        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return {
            "pdf_path": pdf_path,
            "pdf_filename": pdf_file.name,
            "markdown_path": str(markdown_path),
            "markdown_filename": markdown_filename,
            "file_size": pdf_file.stat().st_size,
            "markdown_length": len(markdown_content),
            "pages_parsed": len(images),
            "status": "success"
        }

    def _read_file_as_base64(self, path: str) -> tuple[str, str]:
        """Read file and encode as base64."""
        with open(path, "rb") as f:
            data = f.read()

        b64 = base64.b64encode(data).decode("ascii")

        # Guess mime type from extension
        mime, _ = mimetypes.guess_type(path)
        if mime is None:
            # Default to PDF
            mime = "application/pdf"

        return b64, mime

    async def _call_vl_model(
        self,
        b64_str: str,
        mime: str,
        tool_name: Optional[str] = None
    ) -> str:
        """
        Call NVIDIA Nemotron Parse API to convert document to markdown.

        Args:
            b64_str: Base64-encoded document
            mime: MIME type of the document
            tool_name: Parsing tool to use (default: markdown_no_bbox)

        Returns:
            Markdown content
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")

        # Use default tool if not specified
        if tool_name is None:
            tool_name = self.default_tool

        # Validate tool name
        if tool_name not in self.tools:
            raise ValueError(f"Invalid tool name: {tool_name}. Must be one of {self.tools}")

        # Construct the content with HTML img tag (as per nemotron-parse API)
        data_uri = f"data:{mime};base64,{b64_str}"
        content = f'<img src="{data_uri}" />'

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.nvidia_client.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Prepare tool specification
        tool_spec = [{"type": "function", "function": {"name": tool_name}}]

        # Format content as array if needed (some models require this)
        # Try with simple string first, as shown in example
        message_content = content

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            "tools": tool_spec,
            "tool_choice": {"type": "function", "function": {"name": tool_name}},
            "max_tokens": 8000,  # Model max context is 9000 tokens
        }

        # Make API call
        response = requests.post(
            self.parse_api_url,
            headers=headers,
            json=payload,
            timeout=180  # Longer timeout for parsing processing
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(f"Nemotron Parse API error: {response.status_code} - {response.text}")

        # Extract markdown from response
        response_data = response.json()

        try:
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("No choices in Nemotron Parse response")

            message = choices[0].get("message", {})

            # For tool-based responses, extract from tool_calls
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                # Get the function arguments which contain the parsed content
                function_args = tool_calls[0].get("function", {}).get("arguments", "")
                if function_args:
                    # Parse the arguments as JSON
                    args_data = json.loads(function_args) if isinstance(function_args, str) else function_args
                    # The markdown content should be in the arguments
                    # Handle both dict and list responses
                    if isinstance(args_data, dict):
                        # The exact field name may vary, so we'll try common ones
                        content = args_data.get("markdown", args_data.get("content", args_data.get("text", "")))
                        if content:
                            return content.strip()
                    elif isinstance(args_data, list):
                        # If it's a list, extract text content
                        if args_data:
                            # Try to extract 'text' field from dict items
                            texts = []
                            for item in args_data:
                                if isinstance(item, dict) and 'text' in item:
                                    texts.append(item['text'])
                                elif isinstance(item, str):
                                    texts.append(item)
                            if texts:
                                return "\n\n".join(texts).strip()
                            else:
                                # Fallback to string representation
                                return str(args_data).strip()

            # Fallback to regular content if no tool calls
            content = message.get("content", "")
            if not content:
                raise ValueError("No content in Nemotron Parse response")

            return content.strip()

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"Error parsing Nemotron Parse response: {str(e)}")

    async def parse_multiple_pdfs(
        self,
        pdf_paths: List[str],
        output_dir: str = "parsed_pdfs"
    ) -> Dict[str, Any]:
        """
        Convenience method to parse multiple PDFs.

        Args:
            pdf_paths: List of PDF file paths
            output_dir: Directory to save markdown outputs

        Returns:
            Dictionary with parsing results
        """
        task = TaskMessage(
            task_id="batch_parse",
            agent_type="pdf_parser",
            instructions="Parse multiple PDF documents",
            context={
                "pdf_paths": pdf_paths,
                "output_dir": output_dir
            }
        )

        result = await self.execute(task)
        return result.data

    def get_parsed_markdown(self, markdown_path: str) -> str:
        """Read parsed markdown content from file."""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading markdown: {str(e)}"
