# FOIA-Buddy API Documentation

Complete API reference for the FOIA-Buddy FastAPI server.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Request Submission](#request-submission)
  - [Status Tracking](#status-tracking)
  - [Results Retrieval](#results-retrieval)
  - [Request Management](#request-management)
  - [System Information](#system-information)
- [WebSocket API](#websocket-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## Getting Started

### Starting the Server

```bash
# Set your NVIDIA API key
export NVIDIA_API_KEY="your_nvidia_api_key_here"

# Start the server
python -m foia_buddy.server

# Or use the startup script
./start_server.sh
```

The server will start at `http://localhost:8000` by default.

### Configuration

Environment variables:
- `NVIDIA_API_KEY` (required): Your NVIDIA API key
- `FOIA_API_HOST` (optional, default: `0.0.0.0`): Server host
- `FOIA_API_PORT` (optional, default: `8000`): Server port

### Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Authentication

Currently, the API uses the NVIDIA API key set via environment variable. No per-request authentication is required.

**Future Enhancement**: Add API key authentication for production deployments.

---

## API Endpoints

### Request Submission

#### Submit FOIA Request (JSON)

Submit a new FOIA request with text content.

**Endpoint:** `POST /api/requests/submit`

**Request Body:**
```json
{
  "request_content": "# FOIA Request\n\nI request documents related to...",
  "requester_name": "John Doe",
  "requester_email": "john.doe@example.com",
  "priority": 1,
  "metadata": {
    "department": "Research",
    "reference": "REQ-2024-001"
  }
}
```

**Parameters:**
- `request_content` (string, required): FOIA request in markdown format
- `requester_name` (string, optional): Name of requester
- `requester_email` (string, optional): Email of requester
- `priority` (integer, optional, 1-5): Priority level (default: 1)
- `metadata` (object, optional): Additional metadata

**Response:**
```json
{
  "request_id": "foia-abc123def456",
  "status": "pending",
  "message": "FOIA request submitted successfully. Processing will begin shortly.",
  "estimated_time_minutes": 3
}
```

**Status Codes:**
- `200 OK`: Request submitted successfully
- `400 Bad Request`: Invalid request data
- `500 Internal Server Error`: Server error

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/requests/submit \
  -H "Content-Type: application/json" \
  -d '{
    "request_content": "# FOIA Request\n\nI request all documents related to AI policy.",
    "requester_name": "Jane Smith",
    "priority": 2
  }'
```

---

#### Submit FOIA Request (File Upload)

Submit a FOIA request by uploading a file.

**Endpoint:** `POST /api/requests/submit-file`

**Request:** Multipart form data
- `file` (file, required): Markdown (.md) or text (.txt) file
- `requester_name` (string, optional): Name of requester
- `requester_email` (string, optional): Email of requester
- `priority` (integer, optional): Priority level (1-5)

**Response:** Same as JSON submission

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/requests/submit-file \
  -F "file=@/path/to/foia-request.md" \
  -F "requester_name=John Doe" \
  -F "requester_email=john@example.com"
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/api/requests/submit-file"

with open("foia-request.md", "rb") as f:
    files = {"file": f}
    data = {
        "requester_name": "John Doe",
        "requester_email": "john@example.com",
        "priority": 1
    }
    response = requests.post(url, files=files, data=data)

print(response.json())
```

---

### Status Tracking

#### Get Request Status

Get the current processing status of a FOIA request.

**Endpoint:** `GET /api/requests/{request_id}/status`

**Parameters:**
- `request_id` (path): The request ID returned from submission

**Response:**
```json
{
  "request_id": "foia-abc123def456",
  "status": "processing",
  "progress": 0.65,
  "current_agent": "document_researcher",
  "agent_results": {
    "coordinator": { ... },
    "local_pdf_search": { ... }
  },
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:32:15",
  "error": null
}
```

**Status Values:**
- `pending`: Request queued, not yet started
- `processing`: Currently being processed
- `completed`: Processing finished successfully
- `failed`: Processing failed (see `error` field)

**Progress:** Float between 0.0 and 1.0 representing completion percentage

**Example (cURL):**
```bash
curl http://localhost:8000/api/requests/foia-abc123def456/status
```

**Example (Python):**
```python
import requests
import time

request_id = "foia-abc123def456"
url = f"http://localhost:8000/api/requests/{request_id}/status"

# Poll until complete
while True:
    response = requests.get(url)
    status = response.json()

    print(f"Status: {status['status']}, Progress: {status['progress']*100:.1f}%")

    if status['status'] in ['completed', 'failed']:
        break

    time.sleep(2)
```

---

### Results Retrieval

#### Get Complete Results

Retrieve all results from a completed FOIA request.

**Endpoint:** `GET /api/requests/{request_id}/results`

**Parameters:**
- `request_id` (path): The request ID

**Response:**
```json
{
  "request_id": "foia-abc123def456",
  "status": "completed",
  "results": {
    "processing_start": 1705315800.0,
    "processing_time": 167.5,
    "agent_results": { ... }
  },
  "generated_files": {
    "final_report.md": "# FOIA Response Report\n...",
    "executive_summary.md": "## Executive Summary\n...",
    "compliance_notes.md": "## Compliance Notes\n...",
    "processing_metadata.json": "{ ... }",
    "redaction_review.txt": "REDACTION REVIEW\n..."
  },
  "output_directory": "output/foia-abc123def456",
  "processing_time": 167.5,
  "agent_results": { ... }
}
```

**Status Codes:**
- `200 OK`: Results retrieved successfully
- `400 Bad Request`: Request not completed yet
- `404 Not Found`: Request ID not found

**Example (cURL):**
```bash
curl http://localhost:8000/api/requests/foia-abc123def456/results
```

---

#### Download Specific File

Download a specific file from the request results.

**Endpoint:** `GET /api/requests/{request_id}/files/{filename}`

**Parameters:**
- `request_id` (path): The request ID
- `filename` (path): Name of the file to download

**Available Files:**
- `final_report.md` - Comprehensive FOIA response
- `executive_summary.md` - Executive summary
- `compliance_notes.md` - Legal compliance notes
- `processing_metadata.json` - Processing metadata
- `redaction_review.txt` - Redaction flags
- `interactive_viewer.html` - Interactive UI
- `processing_report.html` - HTML report with diagrams

**Response:** File download (application/octet-stream)

**Example (cURL):**
```bash
# Download final report
curl http://localhost:8000/api/requests/foia-abc123def456/files/final_report.md \
  -o final_report.md

# Download all files
for file in final_report.md executive_summary.md compliance_notes.md; do
  curl http://localhost:8000/api/requests/foia-abc123def456/files/$file -o $file
done
```

---

#### Get Interactive Viewer

Get the interactive HTML viewer for a request.

**Endpoint:** `GET /api/requests/{request_id}/viewer`

**Parameters:**
- `request_id` (path): The request ID

**Response:** HTML page (text/html)

**Example:**
Open in browser: `http://localhost:8000/api/requests/foia-abc123def456/viewer`

---

### Request Management

#### List All Requests

List all FOIA requests with optional filtering.

**Endpoint:** `GET /api/requests`

**Query Parameters:**
- `status` (string, optional): Filter by status (`pending`, `processing`, `completed`, `failed`)
- `limit` (integer, optional, default: 50): Maximum number of results
- `offset` (integer, optional, default: 0): Number of results to skip

**Response:**
```json
{
  "total": 15,
  "limit": 50,
  "offset": 0,
  "requests": [
    {
      "request_id": "foia-abc123def456",
      "status": "completed",
      "progress": 1.0,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:35:00",
      "requester_name": "John Doe",
      "priority": 1
    },
    ...
  ]
}
```

**Example (cURL):**
```bash
# List all requests
curl http://localhost:8000/api/requests

# List only completed requests
curl http://localhost:8000/api/requests?status=completed

# Pagination
curl http://localhost:8000/api/requests?limit=10&offset=20
```

---

#### Delete Request

Delete a FOIA request and its associated data.

**Endpoint:** `DELETE /api/requests/{request_id}`

**Parameters:**
- `request_id` (path): The request ID

**Response:**
```json
{
  "message": "Request deleted successfully",
  "request_id": "foia-abc123def456"
}
```

**Status Codes:**
- `200 OK`: Request deleted successfully
- `400 Bad Request`: Cannot delete processing request
- `404 Not Found`: Request not found

**Example (cURL):**
```bash
curl -X DELETE http://localhost:8000/api/requests/foia-abc123def456
```

---

### System Information

#### Health Check

Check server health and status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "active_requests": 2
}
```

**Example (cURL):**
```bash
curl http://localhost:8000/health
```

---

#### Get Statistics

Get system statistics and metrics.

**Endpoint:** `GET /api/statistics`

**Response:**
```json
{
  "total_requests": 25,
  "completed": 18,
  "processing": 2,
  "failed": 3,
  "pending": 2,
  "average_processing_time_seconds": 165.4,
  "active_websocket_connections": 3
}
```

**Example (cURL):**
```bash
curl http://localhost:8000/api/statistics
```

---

## WebSocket API

Real-time updates for request processing.

### Connect to WebSocket

**Endpoint:** `WS /api/ws/{request_id}`

**Parameters:**
- `request_id` (path): The request ID to watch

### Message Types

#### Connected
Sent immediately after connection:
```json
{
  "type": "connected",
  "request_id": "foia-abc123def456",
  "status": "processing",
  "progress": 0.35,
  "message": "Connected to live updates"
}
```

#### Agent Update
Sent when an agent starts or updates:
```json
{
  "type": "agent_update",
  "agent": "pdf_parser",
  "status": "running",
  "message": "Processing with pdf_parser...",
  "progress": 0.5,
  "timestamp": "2024-01-15T10:32:00"
}
```

#### Completed
Sent when processing completes:
```json
{
  "type": "completed",
  "status": "completed",
  "message": "FOIA request processing completed successfully!",
  "progress": 1.0,
  "output_dir": "output/foia-abc123def456"
}
```

#### Error
Sent when an error occurs:
```json
{
  "type": "error",
  "status": "failed",
  "message": "Processing failed: Connection timeout",
  "error": "Connection timeout"
}
```

#### Keepalive
Sent every 30 seconds to keep connection alive:
```json
{
  "type": "keepalive"
}
```

### Example (JavaScript)

```javascript
const requestId = "foia-abc123def456";
const ws = new WebSocket(`ws://localhost:8000/api/ws/${requestId}`);

ws.onopen = () => {
    console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case 'connected':
            console.log(`Connected! Status: ${data.status}`);
            break;
        case 'agent_update':
            console.log(`Agent: ${data.agent}, Progress: ${data.progress * 100}%`);
            break;
        case 'completed':
            console.log('Processing completed!');
            break;
        case 'error':
            console.error(`Error: ${data.message}`);
            break;
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};

ws.onclose = () => {
    console.log('WebSocket closed');
};

// Send keepalive ping every 25 seconds
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 25000);
```

### Example (Python)

```python
import asyncio
import websockets
import json

async def watch_request(request_id):
    uri = f"ws://localhost:8000/api/ws/{request_id}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {request_id}")

        # Send keepalive task
        async def send_keepalive():
            while True:
                await asyncio.sleep(25)
                await websocket.send("ping")

        keepalive_task = asyncio.create_task(send_keepalive())

        try:
            async for message in websocket:
                data = json.loads(message)

                if data['type'] == 'agent_update':
                    print(f"Agent: {data['agent']}, Progress: {data['progress']*100:.1f}%")
                elif data['type'] == 'completed':
                    print("Processing completed!")
                    break
                elif data['type'] == 'error':
                    print(f"Error: {data['message']}")
                    break
        finally:
            keepalive_task.cancel()

# Usage
asyncio.run(watch_request("foia-abc123def456"))
```

---

## Data Models

### FOIARequestSubmission

```python
{
  "request_content": str,      # Required: FOIA request content
  "requester_name": str,        # Optional: Requester name
  "requester_email": str,       # Optional: Requester email
  "priority": int,              # Optional: Priority (1-5), default: 1
  "metadata": dict              # Optional: Additional metadata
}
```

### FOIARequestStatus

```python
{
  "request_id": str,            # Unique request identifier
  "status": str,                # Status: pending, processing, completed, failed
  "progress": float,            # Progress: 0.0 - 1.0
  "current_agent": str,         # Current agent name (or null)
  "agent_results": dict,        # Results from each agent
  "created_at": datetime,       # Creation timestamp
  "updated_at": datetime,       # Last update timestamp
  "error": str                  # Error message (or null)
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Common Errors

**Request Not Found:**
```json
{
  "detail": "Request not found"
}
```

**Request Not Completed:**
```json
{
  "detail": "Request is not completed yet. Current status: processing"
}
```

**Cannot Delete Processing Request:**
```json
{
  "detail": "Cannot delete a request that is currently processing"
}
```

---

## Examples

### Complete Workflow (Python)

```python
import requests
import time
import json

API_BASE = "http://localhost:8000"

# 1. Submit request
submit_url = f"{API_BASE}/api/requests/submit"
payload = {
    "request_content": "# FOIA Request\n\nI request all AI policy documents.",
    "requester_name": "John Doe",
    "requester_email": "john@example.com"
}

response = requests.post(submit_url, json=payload)
request_data = response.json()
request_id = request_data["request_id"]

print(f"✅ Request submitted: {request_id}")

# 2. Poll status until complete
status_url = f"{API_BASE}/api/requests/{request_id}/status"

while True:
    response = requests.get(status_url)
    status = response.json()

    print(f"Status: {status['status']}, Progress: {status['progress']*100:.1f}%")

    if status['status'] == 'completed':
        print("✅ Processing completed!")
        break
    elif status['status'] == 'failed':
        print(f"❌ Processing failed: {status['error']}")
        break

    time.sleep(2)

# 3. Get results
results_url = f"{API_BASE}/api/requests/{request_id}/results"
response = requests.get(results_url)
results = response.json()

print(f"\n📦 Results:")
print(f"Processing time: {results['processing_time']:.2f}s")
print(f"Files generated: {list(results['generated_files'].keys())}")

# 4. Download final report
report_url = f"{API_BASE}/api/requests/{request_id}/files/final_report.md"
response = requests.get(report_url)

with open("final_report.md", "w") as f:
    f.write(response.text)

print("📄 Final report saved to final_report.md")
```

### Complete Workflow (cURL)

```bash
#!/bin/bash

# 1. Submit request
RESPONSE=$(curl -s -X POST http://localhost:8000/api/requests/submit \
  -H "Content-Type: application/json" \
  -d '{
    "request_content": "# FOIA Request\n\nI request AI policy documents.",
    "requester_name": "John Doe"
  }')

REQUEST_ID=$(echo $RESPONSE | jq -r '.request_id')
echo "✅ Request submitted: $REQUEST_ID"

# 2. Poll status
while true; do
  STATUS=$(curl -s http://localhost:8000/api/requests/$REQUEST_ID/status)
  STATUS_VALUE=$(echo $STATUS | jq -r '.status')
  PROGRESS=$(echo $STATUS | jq -r '.progress')

  echo "Status: $STATUS_VALUE, Progress: $PROGRESS"

  if [ "$STATUS_VALUE" = "completed" ] || [ "$STATUS_VALUE" = "failed" ]; then
    break
  fi

  sleep 2
done

# 3. Download results
if [ "$STATUS_VALUE" = "completed" ]; then
  curl http://localhost:8000/api/requests/$REQUEST_ID/files/final_report.md \
    -o final_report.md
  echo "📄 Final report downloaded"
fi
```

---

## Production Considerations

### Security

For production deployments, consider:

1. **API Key Authentication**: Add per-request authentication
2. **Rate Limiting**: Prevent abuse with rate limits
3. **HTTPS**: Use TLS for encrypted communication
4. **CORS Configuration**: Restrict allowed origins
5. **Input Validation**: Validate all user inputs

### Scalability

For high-traffic deployments:

1. **Database Backend**: Replace in-memory storage with Redis/PostgreSQL
2. **Queue System**: Use Celery or similar for background processing
3. **Load Balancing**: Deploy multiple instances behind load balancer
4. **Caching**: Cache frequently accessed results
5. **File Storage**: Use S3 or similar for generated files

### Monitoring

Recommended monitoring:

1. **Health Checks**: Regular health endpoint monitoring
2. **Metrics Collection**: Track processing times, success rates
3. **Error Logging**: Comprehensive error logging
4. **WebSocket Connections**: Monitor active connections
5. **Resource Usage**: CPU, memory, disk usage tracking

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-repo/foia-buddy/issues
- Documentation: README.md and DEMO.md

---

Built with ❤️ using FastAPI and NVIDIA Nemotron models
