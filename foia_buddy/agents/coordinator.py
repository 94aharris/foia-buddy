from typing import List, Dict, Any
import json
import time
from .base import BaseAgent
from ..models import AgentResult, TaskMessage, FOIARequest


class CoordinatorAgent(BaseAgent):
    """Coordinates FOIA request processing across multiple specialized agents."""

    def __init__(self, nvidia_client):
        super().__init__(
            name="coordinator",
            description="Orchestrates FOIA request processing using ReAct pattern reasoning",
            nvidia_client=nvidia_client
        )
        self.add_capability("request_analysis")
        self.add_capability("agent_orchestration")
        self.add_capability("planning")

    def get_system_prompt(self) -> str:
        return """You are the Coordinator Agent for FOIA-Buddy, an intelligent system that processes Freedom of Information Act requests.

Your role is to:
1. ANALYZE incoming FOIA requests to understand what information is needed
2. CREATE execution plans by deciding which agents to deploy
3. COORDINATE the work of specialized sub-agents
4. SYNTHESIZE results from multiple agents into coherent responses

Available Sub-Agents:
- document_researcher: Searches local document repositories for relevant files
- public_foia_search: Searches the State Department's public FOIA library for previously released documents
- report_generator: Creates comprehensive reports from gathered information

Use the ReAct pattern:
1. REASON about the request complexity and information needs
2. ACT by creating specific tasks for sub-agents
3. OBSERVE results and determine next steps

Always respond with structured JSON containing:
- analysis: Your reasoning about the request
- execution_plan: List of tasks for sub-agents
- priority: Overall priority level (1-5)
- estimated_complexity: low/medium/high"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute coordination task for FOIA request."""
        start_time = time.time()

        try:
            # Parse FOIA request from task context
            foia_content = task.context.get("foia_request", "")

            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"""
Analyze this FOIA request and create an execution plan:

FOIA REQUEST:
{foia_content}

Provide a detailed analysis and execution plan for processing this request using available agents.
"""}
            ]

            response = await self._generate_response(messages, use_thinking=True)

            if "error" in response:
                return self._create_result(
                    task.task_id,
                    success=False,
                    data={"error": response["error"]},
                    reasoning="Failed to generate coordination plan",
                    confidence=0.0,
                    start_time=start_time
                )

            # Parse the response to extract structured plan
            content = response["content"]
            reasoning = response.get("reasoning", "")

            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    # Fallback: create structured plan from text
                    plan_data = self._parse_text_plan(content)
            except:
                plan_data = self._parse_text_plan(content)

            # Create coordination result
            result_data = {
                "coordination_plan": plan_data,
                "raw_response": content,
                "available_agents": ["document_researcher", "public_foia_search", "report_generator"],
                "execution_sequence": self._create_execution_sequence(plan_data)
            }

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning=reasoning or "Successfully analyzed FOIA request and created execution plan",
                confidence=0.9,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during coordination: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    def _parse_text_plan(self, content: str) -> Dict[str, Any]:
        """Parse text response into structured plan."""
        return {
            "analysis": content[:500] + "..." if len(content) > 500 else content,
            "execution_plan": [
                {
                    "agent": "public_foia_search",
                    "task": "Search public FOIA library for previously released documents",
                    "priority": 1
                },
                {
                    "agent": "document_researcher",
                    "task": "Search local document repository for relevant files",
                    "priority": 2
                },
                {
                    "agent": "report_generator",
                    "task": "Generate final FOIA response report",
                    "priority": 3
                }
            ],
            "priority": 3,
            "estimated_complexity": "medium"
        }

    def _create_execution_sequence(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create execution sequence from plan data."""
        execution_plan = plan_data.get("execution_plan", [])

        # Sort by priority if available
        if execution_plan and isinstance(execution_plan, list):
            execution_plan.sort(key=lambda x: x.get("priority", 5))

        return execution_plan