from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum


class MessageType(str, Enum):
    TASK = "task"
    RESULT = "result"
    ERROR = "error"
    STATUS = "status"


class AgentMessage(BaseModel):
    """Standard message format for agent communication."""
    type: MessageType
    sender: str
    recipient: str
    content: Dict[str, Any]
    timestamp: Optional[str] = None


class TaskMessage(BaseModel):
    """Task assignment message."""
    task_id: str
    agent_type: str
    instructions: str
    context: Dict[str, Any]
    priority: int = 1


class ResultMessage(BaseModel):
    """Result message from agent execution."""
    task_id: str
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class FOIARequest(BaseModel):
    """Parsed FOIA request structure."""
    title: str
    description: str
    requested_documents: List[str]
    timeframe: Optional[str] = None
    agency: Optional[str] = None
    priority: int = 1
    raw_content: str


class DocumentResult(BaseModel):
    """Document search result."""
    file_path: str
    relevance_score: float
    relevant_sections: List[str]
    summary: str
    metadata: Dict[str, Any] = {}


class AgentResult(BaseModel):
    """Standard agent result format."""
    agent_name: str
    task_id: str
    success: bool
    data: Any
    reasoning: str
    confidence: float
    execution_time: float