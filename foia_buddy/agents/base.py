from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
from ..models import AgentResult, TaskMessage
from ..utils import NvidiaClient


class BaseAgent(ABC):
    """Base class for all FOIA-Buddy agents."""

    def __init__(self, name: str, description: str, nvidia_client: NvidiaClient):
        self.name = name
        self.description = description
        self.nvidia_client = nvidia_client
        self.capabilities = []

    @abstractmethod
    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute a task and return results."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    def add_capability(self, capability: str):
        """Add a capability to this agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    async def _generate_response(
        self,
        messages: List[Dict[str, str]],
        use_thinking: bool = True
    ) -> Dict[str, Any]:
        """Generate response using Nemotron model."""
        return self.nvidia_client.generate_response(
            messages=messages,
            use_thinking=use_thinking
        )

    def _create_result(
        self,
        task_id: str,
        success: bool,
        data: Any,
        reasoning: str,
        confidence: float,
        start_time: float
    ) -> AgentResult:
        """Create standardized agent result."""
        return AgentResult(
            agent_name=self.name,
            task_id=task_id,
            success=success,
            data=data,
            reasoning=reasoning,
            confidence=confidence,
            execution_time=time.time() - start_time
        )


class AgentRegistry:
    """Registry for managing available agents."""

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """Register an agent."""
        self._agents[agent.name] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def get_agents_with_capability(self, capability: str) -> List[BaseAgent]:
        """Get all agents with specific capability."""
        return [
            agent for agent in self._agents.values()
            if agent.has_capability(capability)
        ]