from typing import List, Dict, Any, Optional
import time
import base64
import mimetypes
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class PDFParserAgent(BaseAgent):
    """
    Parses PDF documents using NVIDIA Nemotron VL model to convert them to markdown.

    This agent uses the Vision-Language model for enhanced document understanding,
    including scanned PDFs, visual elements, and complex layouts. It makes it easier
    for other agents and end-users to evaluate document content by converting PDFs
    to well-formatted markdown with visual element descriptions.
    """

    def __init__(self, nvidia_client):
        super().__init__(
            name="pdf_parser",
            description="Converts PDF documents to markdown using NVIDIA Nemotron VL model",
            nvidia_client=nvidia_client
        )
        self.parse_api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model_name = "nvidia/nemotron-nano-12b-v2-vl"
        self.add_capability("pdf_parsing")
        self.add_capability("document_conversion")
        self.add_capability("markdown_generation")
        self.add_capability("visual_understanding")
        self.add_capability("ocr")

    def get_system_prompt(self) -> str:
        return """You are the PDF Parser Agent for FOIA-Buddy using NVIDIA Nemotron VL.

Your role is to:
1. PARSE PDF documents using vision-language understanding
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

        # Read PDF as base64
        b64_str, mime = self._read_file_as_base64(pdf_path)

        # Generate markdown using VL model
        markdown_content = await self._call_vl_model(b64_str, mime)

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
        mime: str
    ) -> str:
        """
        Call NVIDIA Nemotron VL API to convert document to markdown.

        Args:
            b64_str: Base64-encoded document
            mime: MIME type of the document

        Returns:
            Markdown content
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests library required. Install with: pip install requests")

        # Construct the content with data URI
        data_uri = f"data:{mime};base64,{b64_str}"

        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.nvidia_client.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Comprehensive prompt for document parsing
        parsing_prompt = """Convert this PDF document to well-formatted markdown. Follow these guidelines:

1. Extract all text content accurately
2. Preserve document structure (headings, subheadings, lists, tables)
3. Convert tables to markdown table format
4. For any charts, graphs, or diagrams, provide detailed descriptions in [Chart: description] or [Diagram: description] format
5. Maintain paragraph breaks and formatting
6. Preserve bullet points and numbered lists
7. Keep document metadata if visible (date, author, title, etc.)
8. For scanned content, use OCR to extract text accurately

Output only the markdown content without any additional commentary."""

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "/think"  # Enable thinking mode for better reasoning
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": parsing_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_uri
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 16384,  # Increased for longer documents
            "temperature": 0.5,  # Lower temperature for more accurate extraction
            "top_p": 1.0
        }

        # Make API call
        response = requests.post(
            self.parse_api_url,
            headers=headers,
            json=payload,
            timeout=180  # Longer timeout for VL processing
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(f"VL Model API error: {response.status_code} - {response.text}")

        # Extract markdown from response
        response_data = response.json()

        try:
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("No choices in VL model response")

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                raise ValueError("No content in VL model response")

            return content.strip()

        except (KeyError, IndexError) as e:
            raise Exception(f"Error parsing VL model response: {str(e)}")

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
