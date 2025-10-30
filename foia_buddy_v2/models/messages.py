"""
Data models for agent communication and task messages.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class TaskMessage:
    """
    Task message passed between agents.
    """
    task_id: str
    agent_name: str
    instructions: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentResult:
    """
    Result returned by an agent after task execution.
    """
    success: bool
    data: Any
    reasoning: str = ""
    plan: Optional[List[str]] = None
    evaluation: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentStatus:
    """
    Current status of an agent.
    """
    name: str
    status: str  # idle, thinking, planning, executing, reflecting, complete, error
    current_task: str = ""
    progress: float = 0.0
    reasoning_tokens: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DecisionPoint:
    """
    Captures an agent decision for visualization.
    """
    agent_name: str
    decision: str
    reasoning: str
    options_considered: List[str]
    confidence: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentHandoff:
    """
    Records agent-to-agent handoff.
    """
    from_agent: str
    to_agent: str
    task: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
