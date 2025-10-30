"""
FastAPI server for FOIA-Buddy API endpoints.

Provides REST API and WebSocket endpoints for:
- Submitting FOIA requests
- Tracking processing status in real-time
- Retrieving completed results
- Managing request history
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import asyncio
import uuid
import time
import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from .cli import FOIAProcessor
from .models import TaskMessage, ResultMessage


# Pydantic models for API requests/responses
class FOIARequestSubmission(BaseModel):
    """FOIA request submission model."""
    request_content: str = Field(..., description="FOIA request content in markdown format")
    requester_name: Optional[str] = Field(None, description="Name of the requester")
    requester_email: Optional[str] = Field(None, description="Email of the requester")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1-5)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class FOIARequestStatus(BaseModel):
    """FOIA request processing status."""
    request_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 - 1.0
    current_agent: Optional[str] = None
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


class FOIARequestResponse(BaseModel):
    """Response when submitting a FOIA request."""
    request_id: str
    status: str
    message: str
    estimated_time_minutes: int


class AgentUpdate(BaseModel):
    """Real-time agent update model."""
    request_id: str
    agent_name: str
    status: str
    message: str
    progress: float
    timestamp: datetime


# In-memory storage for request tracking
# In production, use Redis or a database
request_storage: Dict[str, Dict[str, Any]] = {}
request_status: Dict[str, FOIARequestStatus] = {}
websocket_connections: Dict[str, List[WebSocket]] = defaultdict(list)


# Initialize FastAPI app
app = FastAPI(
    title="FOIA-Buddy API",
    description="Agentic FOIA request processing using NVIDIA Nemotron models",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize FOIA processor
nvidia_api_key = os.getenv("NVIDIA_API_KEY")
if not nvidia_api_key:
    raise RuntimeError("NVIDIA_API_KEY environment variable must be set")

processor = FOIAProcessor(nvidia_api_key)


# Helper functions
def create_request_id() -> str:
    """Generate a unique request ID."""
    return f"foia-{uuid.uuid4().hex[:12]}"


async def send_websocket_update(request_id: str, update: Dict[str, Any]):
    """Send update to all WebSocket clients watching this request."""
    if request_id in websocket_connections:
        disconnected = []
        for ws in websocket_connections[request_id]:
            try:
                await ws.send_json(update)
            except Exception:
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            websocket_connections[request_id].remove(ws)


async def process_foia_request_background(request_id: str, request_content: str, metadata: Dict[str, Any]):
    """Background task to process FOIA request with real-time updates."""

    try:
        # Update status to processing
        request_status[request_id].status = "processing"
        request_status[request_id].updated_at = datetime.now()

        await send_websocket_update(request_id, {
            "type": "status_update",
            "status": "processing",
            "message": "Starting FOIA request processing...",
            "progress": 0.0
        })

        # Create output directory
        output_dir = f"output/{request_id}"
        os.makedirs(output_dir, exist_ok=True)

        # Save request content to temp file
        input_file = f"{output_dir}/request.md"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(request_content)

        # Track progress through agent execution
        agent_sequence = [
            ("coordinator", 0.1),
            ("local_pdf_search", 0.25),
            ("pdf_parser", 0.4),
            ("document_researcher", 0.6),
            ("report_generator", 0.8),
            ("html_report_generator", 0.9),
            ("interactive_ui_generator", 0.95),
            ("launcher_ui_generator", 1.0)
        ]

        # Create custom processor with progress callbacks
        class ProgressTrackingProcessor:
            def __init__(self, base_processor, request_id):
                self.processor = base_processor
                self.request_id = request_id

            async def process_with_tracking(self, input_file: str, output_dir: str):
                """Process with progress tracking."""

                # Update progress for each agent
                async def update_progress(agent_name: str, progress: float, message: str):
                    request_status[self.request_id].current_agent = agent_name
                    request_status[self.request_id].progress = progress
                    request_status[self.request_id].updated_at = datetime.now()

                    await send_websocket_update(self.request_id, {
                        "type": "agent_update",
                        "agent": agent_name,
                        "status": "running",
                        "message": message,
                        "progress": progress,
                        "timestamp": datetime.now().isoformat()
                    })

                # Hook into the processor to track progress
                # For now, we'll just run the processor and update at checkpoints
                result = await self.processor.process_foia_request(input_file, output_dir)

                return result

        # Process the request
        tracking_processor = ProgressTrackingProcessor(processor, request_id)

        # Simulate progress updates while processing
        async def simulate_progress():
            """Simulate progress updates based on expected agent sequence."""
            for agent_name, progress in agent_sequence:
                await asyncio.sleep(2)  # Wait a bit between updates

                if request_status[request_id].status == "processing":
                    request_status[request_id].current_agent = agent_name
                    request_status[request_id].progress = progress

                    await send_websocket_update(request_id, {
                        "type": "agent_update",
                        "agent": agent_name,
                        "status": "running",
                        "message": f"Processing with {agent_name}...",
                        "progress": progress
                    })

        # Run processing and progress updates concurrently
        progress_task = asyncio.create_task(simulate_progress())

        results = await processor.process_foia_request(input_file, output_dir)

        # Cancel progress simulation
        progress_task.cancel()

        # Store results
        request_storage[request_id]["results"] = results
        request_storage[request_id]["output_dir"] = output_dir

        # Update final status
        if results.get("status") == "completed":
            request_status[request_id].status = "completed"
            request_status[request_id].progress = 1.0
            request_status[request_id].agent_results = results.get("agent_results", {})

            await send_websocket_update(request_id, {
                "type": "completed",
                "status": "completed",
                "message": "FOIA request processing completed successfully!",
                "progress": 1.0,
                "output_dir": output_dir
            })
        else:
            request_status[request_id].status = "failed"
            request_status[request_id].error = results.get("error", "Unknown error")

            await send_websocket_update(request_id, {
                "type": "error",
                "status": "failed",
                "message": f"Processing failed: {results.get('error')}",
                "error": results.get("error")
            })

    except Exception as e:
        request_status[request_id].status = "failed"
        request_status[request_id].error = str(e)
        request_status[request_id].updated_at = datetime.now()

        await send_websocket_update(request_id, {
            "type": "error",
            "status": "failed",
            "message": f"Processing failed: {str(e)}",
            "error": str(e)
        })


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "FOIA-Buddy API",
        "version": "1.0.0",
        "description": "Agentic FOIA request processing using NVIDIA Nemotron models",
        "endpoints": {
            "submit": "POST /api/requests/submit",
            "status": "GET /api/requests/{request_id}/status",
            "results": "GET /api/requests/{request_id}/results",
            "list": "GET /api/requests",
            "websocket": "WS /api/ws/{request_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_requests": len([r for r in request_status.values() if r.status == "processing"])
    }


@app.post("/api/requests/submit", response_model=FOIARequestResponse)
async def submit_foia_request(
    request: FOIARequestSubmission,
    background_tasks: BackgroundTasks
):
    """
    Submit a new FOIA request for processing.

    Returns a request ID that can be used to track status and retrieve results.
    """

    # Generate request ID
    request_id = create_request_id()

    # Store request data
    request_storage[request_id] = {
        "request_content": request.request_content,
        "requester_name": request.requester_name,
        "requester_email": request.requester_email,
        "priority": request.priority,
        "metadata": request.metadata,
        "created_at": datetime.now(),
        "status": "pending"
    }

    # Initialize status tracking
    request_status[request_id] = FOIARequestStatus(
        request_id=request_id,
        status="pending",
        progress=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Add background processing task
    background_tasks.add_task(
        process_foia_request_background,
        request_id,
        request.request_content,
        request.metadata
    )

    return FOIARequestResponse(
        request_id=request_id,
        status="pending",
        message="FOIA request submitted successfully. Processing will begin shortly.",
        estimated_time_minutes=3
    )


@app.post("/api/requests/submit-file")
async def submit_foia_request_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    requester_name: Optional[str] = None,
    requester_email: Optional[str] = None,
    priority: int = 1
):
    """
    Submit a FOIA request from an uploaded file.

    Accepts markdown (.md) or text (.txt) files.
    """

    # Validate file type
    if not file.filename.endswith(('.md', '.txt')):
        raise HTTPException(status_code=400, detail="Only .md and .txt files are supported")

    # Read file content
    content = await file.read()
    request_content = content.decode('utf-8')

    # Create submission request
    submission = FOIARequestSubmission(
        request_content=request_content,
        requester_name=requester_name,
        requester_email=requester_email,
        priority=priority,
        metadata={"original_filename": file.filename}
    )

    return await submit_foia_request(submission, background_tasks)


@app.get("/api/requests/{request_id}/status", response_model=FOIARequestStatus)
async def get_request_status(request_id: str):
    """
    Get the current status of a FOIA request.

    Returns processing status, progress, and current agent information.
    """

    if request_id not in request_status:
        raise HTTPException(status_code=404, detail="Request not found")

    return request_status[request_id]


@app.get("/api/requests/{request_id}/results")
async def get_request_results(request_id: str):
    """
    Get the complete results of a processed FOIA request.

    Returns all generated reports, metadata, and agent results.
    """

    if request_id not in request_storage:
        raise HTTPException(status_code=404, detail="Request not found")

    if request_status[request_id].status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Request is not completed yet. Current status: {request_status[request_id].status}"
        )

    results = request_storage[request_id].get("results", {})
    output_dir = request_storage[request_id].get("output_dir", "")

    # Read generated files
    output_path = Path(output_dir)
    generated_files = {}

    if output_path.exists():
        # Read main report files
        for filename in ["final_report.md", "executive_summary.md", "compliance_notes.md",
                        "processing_metadata.json", "redaction_review.txt"]:
            file_path = output_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    generated_files[filename] = f.read()

    return {
        "request_id": request_id,
        "status": request_status[request_id].status,
        "results": results,
        "generated_files": generated_files,
        "output_directory": output_dir,
        "processing_time": results.get("processing_time", 0),
        "agent_results": results.get("agent_results", {})
    }


@app.get("/api/requests/{request_id}/files/{filename}")
async def get_request_file(request_id: str, filename: str):
    """
    Download a specific file from the request results.

    Supports downloading reports, HTML viewers, and parsed documents.
    """

    if request_id not in request_storage:
        raise HTTPException(status_code=404, detail="Request not found")

    output_dir = request_storage[request_id].get("output_dir", "")
    file_path = Path(output_dir) / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/api/requests/{request_id}/viewer")
async def get_interactive_viewer(request_id: str):
    """
    Get the interactive HTML viewer for a request.

    Returns the interactive tabbed UI with all results.
    """

    if request_id not in request_storage:
        raise HTTPException(status_code=404, detail="Request not found")

    output_dir = request_storage[request_id].get("output_dir", "")
    viewer_path = Path(output_dir) / "interactive_viewer.html"

    if not viewer_path.exists():
        raise HTTPException(status_code=404, detail="Interactive viewer not generated yet")

    return FileResponse(
        path=str(viewer_path),
        media_type="text/html"
    )


@app.get("/api/requests")
async def list_requests(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all FOIA requests with optional filtering.

    Parameters:
    - status: Filter by status (pending, processing, completed, failed)
    - limit: Maximum number of requests to return
    - offset: Number of requests to skip
    """

    requests = []
    for req_id, req_status in request_status.items():
        if status is None or req_status.status == status:
            requests.append({
                "request_id": req_id,
                "status": req_status.status,
                "progress": req_status.progress,
                "created_at": req_status.created_at.isoformat(),
                "updated_at": req_status.updated_at.isoformat(),
                "requester_name": request_storage[req_id].get("requester_name"),
                "priority": request_storage[req_id].get("priority", 1)
            })

    # Sort by creation time (newest first)
    requests.sort(key=lambda x: x["created_at"], reverse=True)

    # Apply pagination
    paginated_requests = requests[offset:offset + limit]

    return {
        "total": len(requests),
        "limit": limit,
        "offset": offset,
        "requests": paginated_requests
    }


@app.delete("/api/requests/{request_id}")
async def delete_request(request_id: str):
    """
    Delete a FOIA request and its associated data.

    Only completed or failed requests can be deleted.
    """

    if request_id not in request_storage:
        raise HTTPException(status_code=404, detail="Request not found")

    if request_status[request_id].status == "processing":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a request that is currently processing"
        )

    # Clean up files
    output_dir = request_storage[request_id].get("output_dir", "")
    if output_dir and Path(output_dir).exists():
        import shutil
        shutil.rmtree(output_dir)

    # Remove from storage
    del request_storage[request_id]
    del request_status[request_id]

    return {"message": "Request deleted successfully", "request_id": request_id}


@app.websocket("/api/ws/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    """
    WebSocket endpoint for real-time processing updates.

    Clients can connect to receive live updates about request processing.
    """

    await websocket.accept()

    # Add to connections list
    websocket_connections[request_id].append(websocket)

    try:
        # Send initial status
        if request_id in request_status:
            await websocket.send_json({
                "type": "connected",
                "request_id": request_id,
                "status": request_status[request_id].status,
                "progress": request_status[request_id].progress,
                "message": "Connected to live updates"
            })
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Request not found"
            })
            await websocket.close()
            return

        # Keep connection alive and wait for messages
        while True:
            # Wait for any client messages (like ping)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Handle ping
                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})

    except WebSocketDisconnect:
        # Remove from connections list
        if websocket in websocket_connections[request_id]:
            websocket_connections[request_id].remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in websocket_connections[request_id]:
            websocket_connections[request_id].remove(websocket)


@app.get("/api/statistics")
async def get_statistics():
    """
    Get system statistics and metrics.

    Returns processing statistics, agent performance, and system health.
    """

    total_requests = len(request_status)
    completed = len([r for r in request_status.values() if r.status == "completed"])
    processing = len([r for r in request_status.values() if r.status == "processing"])
    failed = len([r for r in request_status.values() if r.status == "failed"])
    pending = len([r for r in request_status.values() if r.status == "pending"])

    # Calculate average processing time for completed requests
    processing_times = []
    for req_id, req_data in request_storage.items():
        if request_status[req_id].status == "completed":
            results = req_data.get("results", {})
            if "processing_time" in results:
                processing_times.append(results["processing_time"])

    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

    return {
        "total_requests": total_requests,
        "completed": completed,
        "processing": processing,
        "failed": failed,
        "pending": pending,
        "average_processing_time_seconds": round(avg_processing_time, 2),
        "active_websocket_connections": sum(len(conns) for conns in websocket_connections.values())
    }


# Run server
if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("FOIA_API_HOST", "0.0.0.0")
    port = int(os.getenv("FOIA_API_PORT", "8000"))

    print(f"""
🚀 FOIA-Buddy API Server Starting...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API Documentation: http://{host}:{port}/docs
Health Check:      http://{host}:{port}/health
WebSocket:         ws://{host}:{port}/api/ws/{{request_id}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    uvicorn.run(
        "foia_buddy.server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
