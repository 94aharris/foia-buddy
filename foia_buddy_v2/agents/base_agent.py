"""
Base agent class with streaming reasoning and decision logging.
All agents inherit from this to provide consistent demo visualization.
"""

import time
from typing import Callable, Any, Dict
from models.messages import TaskMessage, AgentResult, DecisionPoint
from utils.nvidia_client import NvidiaClient
from utils.logger import DemoLogger


class BaseAgent:
    """
    Enhanced base agent with streaming reasoning and decision logging.
    Every agent exposes its thought process in real-time.
    """

    def __init__(self, name: str, description: str, nvidia_client: NvidiaClient):
        self.name = name
        self.description = description
        self.client = nvidia_client
        self.logger = DemoLogger(name)
        self.decision_log = []
        self.reasoning_stream = []
        self.metrics = {
            "tokens_used": 0,
            "api_calls": 0,
            "decisions_made": 0,
            "tools_called": 0,
            "execution_time": 0.0
        }

    async def execute_with_streaming(
        self,
        task: TaskMessage,
        ui_callback: Callable
    ) -> AgentResult:
        """
        Execute task with streaming reasoning to UI.

        Flow:
        1. Announce start → UI shows agent as "Active"
        2. Stream reasoning tokens → UI shows live thinking
        3. Make decisions → UI logs decision points
        4. Execute actions → UI shows progress
        5. Return results → UI shows completion
        """

        start_time = time.time()

        try:
            # Update UI: Agent starting
            ui_callback(self.name, "active", "Starting analysis...")

            # Phase 1: Reasoning (with thinking tokens)
            ui_callback(self.name, "thinking", "🧠 Analyzing request...")
            reasoning = await self._stream_reasoning(task, ui_callback)

            # Phase 2: Planning
            ui_callback(self.name, "planning", "📋 Creating execution plan...")
            plan = await self._generate_plan(reasoning, task, ui_callback)

            # Phase 3: Execution
            ui_callback(self.name, "executing", "⚡ Executing plan...")
            result = await self._execute_plan(plan, task, ui_callback)

            # Phase 4: Reflection
            ui_callback(self.name, "reflecting", "🤔 Evaluating results...")
            evaluation = await self._reflect_on_results(result, ui_callback)

            # Calculate execution time
            self.metrics['execution_time'] = time.time() - start_time

            # Update UI: Agent complete
            ui_callback(
                self.name,
                "complete",
                f"✅ Completed in {self.metrics['execution_time']:.2f}s"
            )

            return AgentResult(
                success=True,
                data=result,
                reasoning=reasoning,
                plan=plan,
                evaluation=evaluation,
                metrics=self.metrics
            )

        except Exception as e:
            ui_callback(self.name, "error", f"❌ Error: {str(e)}")
            return AgentResult(
                success=False,
                data={},
                errors=[str(e)],
                metrics=self.metrics
            )

    async def _stream_reasoning(self, task: TaskMessage, ui_callback: Callable) -> str:
        """
        Generate reasoning using Nemotron (non-streaming for simplicity).
        """

        prompt = f"""
Analyze this task and explain your reasoning step-by-step.

Task: {task.instructions}
Context: {task.context}

Think through:
1. What information do I need?
2. What are the key requirements?
3. What approach should I take?
4. What tools/actions do I need?
"""

        self.metrics['api_calls'] += 1

        # Get complete reasoning response
        reasoning = await self.client.complete(prompt, model="reasoning", temperature=0.3)

        # Send complete reasoning to UI
        ui_callback(
            self.name,
            "reasoning",
            f"💭 {reasoning}"
        )

        self.metrics['tokens_used'] += len(reasoning.split())
        self.reasoning_stream.append(reasoning)
        return reasoning

    async def _generate_plan(
        self,
        reasoning: str,
        task: TaskMessage,
        ui_callback: Callable
    ) -> list[str]:
        """
        Generate execution plan based on reasoning.
        To be overridden by specific agents.
        """

        # Default implementation - agents should override
        return ["Analyze data", "Process information", "Generate results"]

    async def _execute_plan(
        self,
        plan: list[str],
        task: TaskMessage,
        ui_callback: Callable
    ) -> Dict[str, Any]:
        """
        Execute the plan step by step.
        To be overridden by specific agents.
        """

        # Default implementation - agents should override
        results = {}
        for i, step in enumerate(plan):
            ui_callback(self.name, "progress", f"Step {i+1}/{len(plan)}: {step}")
            results[step] = "completed"

        return results

    async def _reflect_on_results(
        self,
        result: Dict[str, Any],
        ui_callback: Callable
    ) -> str:
        """
        Reflect on the results and evaluate success.
        """

        evaluation = f"Successfully completed task. Results: {len(result)} items processed."
        ui_callback(self.name, "reflection", evaluation)
        return evaluation

    def log_decision(
        self,
        decision: str,
        reasoning: str,
        options: list[str],
        confidence: float = 0.0
    ):
        """
        Log an agent decision for visualization.
        """

        decision_point = DecisionPoint(
            agent_name=self.name,
            decision=decision,
            reasoning=reasoning,
            options_considered=options,
            confidence=confidence
        )
        self.decision_log.append(decision_point)
        self.metrics['decisions_made'] += 1
        return decision_point
