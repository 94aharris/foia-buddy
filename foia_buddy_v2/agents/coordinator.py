"""
Coordinator Agent - Orchestrates all other agents with visible decision-making.
Shows real-time coordination logic and agent selection.
"""

import asyncio
from typing import Callable, Dict, Any, List
from agents.base_agent import BaseAgent
from models.messages import TaskMessage, AgentResult, AgentHandoff


class CoordinatorAgent(BaseAgent):
    """
    Orchestrates all other agents with visible decision-making.
    Shows real-time coordination logic and agent selection.
    """

    def __init__(self, nvidia_client, agents: Dict[str, BaseAgent] = None):
        super().__init__(
            name="Coordinator",
            description="Orchestrates multi-agent workflow for FOIA processing",
            nvidia_client=nvidia_client
        )
        self.agents = agents or {}

    async def execute_with_streaming(
        self,
        task: TaskMessage,
        ui_callback: Callable
    ) -> AgentResult:
        """
        Execute coordination with visible planning and handoffs.
        """

        import time
        start_time = time.time()

        try:
            # Phase 1: Request Analysis
            ui_callback(self.name, "phase", "📊 Phase 1: Analyzing FOIA Request")

            ui_callback(self.name, "reasoning", "🧠 Extracting key topics from request...")
            topics = await self._extract_topics(
                task.context.get("foia_request", ""),
                ui_callback
            )

            ui_callback(
                self.name,
                "decision",
                f"✅ Identified {len(topics)} key topics: {', '.join(topics)}"
            )

            # Phase 2: Agent Selection
            ui_callback(self.name, "phase", "🎯 Phase 2: Selecting Agents")

            ui_callback(self.name, "reasoning", "🤔 Determining which agents are needed...")
            agent_plan = await self._plan_agent_execution(topics, task, ui_callback)

            decision = self.log_decision(
                decision=f"Execute {len(agent_plan)} agents in sequence",
                reasoning=f"Based on topics identified, need specialized agents for each stage",
                options=["Sequential execution", "Parallel execution", "Hybrid approach"],
                confidence=0.85
            )

            ui_callback(
                self.name,
                "decision",
                f"📋 Plan: Execute {len(agent_plan)} agents in sequence"
            )

            # Show the plan visually
            for i, step in enumerate(agent_plan):
                ui_callback(
                    self.name,
                    "plan_step",
                    f"{i+1}. {step['agent']} → {step['task']}"
                )

            # Phase 3: Coordination
            ui_callback(self.name, "phase", "🎭 Phase 3: Orchestrating Agents")

            results = {}
            previous_agent = self.name

            for i, step in enumerate(agent_plan):
                current_agent = step['agent']

                ui_callback(
                    self.name,
                    "handoff",
                    f"📤 Handing off to {current_agent} ({i+1}/{len(agent_plan)})..."
                )

                # Create handoff record
                handoff = AgentHandoff(
                    from_agent=previous_agent,
                    to_agent=current_agent,
                    task=step['task'],
                    data={"topics": step.get('topics', [])}
                )

                # Send handoff event to UI
                ui_callback(
                    self.name,
                    "agent_handoff",
                    handoff
                )

                # Execute the agent
                agent_result = await self._execute_agent(step, ui_callback)
                results[current_agent] = agent_result

                ui_callback(
                    self.name,
                    "handoff_complete",
                    f"📥 {current_agent} completed successfully"
                )

                previous_agent = current_agent

            self.metrics['execution_time'] = time.time() - start_time

            ui_callback(
                self.name,
                "complete",
                f"✅ All agents completed in {self.metrics['execution_time']:.2f}s"
            )

            return AgentResult(
                success=True,
                data={
                    "coordination_plan": agent_plan,
                    "agent_results": results,
                    "topics_analyzed": topics
                },
                reasoning=f"Coordinated {len(agent_plan)} agents to process FOIA request",
                plan=[step['task'] for step in agent_plan],
                metrics=self.metrics
            )

        except Exception as e:
            ui_callback(self.name, "error", f"❌ Coordination error: {str(e)}")
            return AgentResult(
                success=False,
                data={},
                errors=[str(e)],
                metrics=self.metrics
            )

    async def _extract_topics(
        self,
        foia_request: str,
        ui_callback: Callable
    ) -> List[str]:
        """
        Extract key topics from FOIA request.
        """

        prompt = f"""
Analyze this FOIA request and extract the key topics/subjects being requested.

FOIA Request:
{foia_request}

List the main topics (3-5 topics maximum). Be specific and concise.
Format: Return only the topics as a comma-separated list.
"""

        self.metrics['api_calls'] += 1
        response = await self.client.complete(prompt, model="fast", temperature=0.3)

        # Parse topics from response
        topics = [t.strip() for t in response.strip().split(',')][:5]

        ui_callback(self.name, "analysis", f"Extracted topics: {', '.join(topics)}")

        return topics

    async def _plan_agent_execution(
        self,
        topics: List[str],
        task: TaskMessage,
        ui_callback: Callable
    ) -> List[Dict[str, str]]:
        """
        Use LLM to actually decide which agents to execute and in what order.
        """

        foia_request = task.context.get("foia_request", "")

        # Actually ask the LLM to plan!
        prompt = f"""You are a coordinator for a multi-agent FOIA processing system.

Available agents:
- PDFSearcher: Searches local filesystem for relevant PDF documents
- PDFParser: Parses PDFs and extracts structured content (text, tables, charts)
- DocumentResearcher: Performs semantic search across markdown document repository
- ReportGenerator: Synthesizes findings into comprehensive FOIA response

FOIA Request:
{foia_request}

Topics identified: {', '.join(topics)}

Based on this request, determine which agents are needed and in what order. Consider:
1. What types of documents are being requested?
2. Do we need to search PDFs, text documents, or both?
3. What order makes sense for data flow?

Respond with a JSON array of agent steps. Each step should have:
- "agent": agent name from the list above
- "task": brief description of what this agent should do
- "reasoning": why this agent is needed

Example format:
[
  {{"agent": "PDFSearcher", "task": "Find relevant PDFs", "reasoning": "Request mentions documents likely stored as PDFs"}},
  {{"agent": "PDFParser", "task": "Extract PDF content", "reasoning": "Need to parse discovered PDFs"}},
  {{"agent": "ReportGenerator", "task": "Create response", "reasoning": "Synthesize findings"}}
]

Return ONLY the JSON array, no other text."""

        self.metrics['api_calls'] += 1
        ui_callback(self.name, "thinking", "🤔 Using LLM to plan agent execution...")

        response = await self.client.complete(prompt, model="reasoning", temperature=0.3, max_tokens=1000)

        # Parse JSON response
        import json
        try:
            # Extract JSON from response (in case there's extra text)
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")

            json_str = response[start_idx:end_idx]
            plan_steps = json.loads(json_str)

            # Add topics to each step
            for step in plan_steps:
                step['topics'] = topics

            ui_callback(
                self.name,
                "planning",
                f"LLM planned {len(plan_steps)}-step execution: {' → '.join([s['agent'] for s in plan_steps])}"
            )

            # Log the decision
            self.log_decision(
                decision=f"Execute {len(plan_steps)} agents: {' → '.join([s['agent'] for s in plan_steps])}",
                reasoning=f"LLM determined optimal agent sequence based on request analysis",
                options=["All agents", "Subset of agents", "Different ordering"],
                confidence=0.9
            )

            return plan_steps

        except (json.JSONDecodeError, ValueError) as e:
            # If LLM response isn't valid JSON, fall back to default plan
            ui_callback(self.name, "warning", f"⚠️ LLM response parsing failed, using default plan: {str(e)}")

            default_plan = [
                {
                    "agent": "PDFSearcher",
                    "task": "Search local filesystem for relevant PDF documents",
                    "topics": topics,
                    "reasoning": "Default: always search PDFs"
                },
                {
                    "agent": "PDFParser",
                    "task": "Parse discovered PDFs",
                    "topics": topics,
                    "reasoning": "Default: parse found PDFs"
                },
                {
                    "agent": "DocumentResearcher",
                    "task": "Search document repository",
                    "topics": topics,
                    "reasoning": "Default: search text documents"
                },
                {
                    "agent": "ReportGenerator",
                    "task": "Generate FOIA response",
                    "topics": topics,
                    "reasoning": "Default: always generate report"
                }
            ]
            return default_plan

    async def _execute_agent(
        self,
        step: Dict[str, Any],
        ui_callback: Callable
    ) -> Dict[str, Any]:
        """
        Execute a specific agent as part of the plan.
        """

        agent_name = step['agent']

        # For demo purposes, simulate agent execution with realistic data
        ui_callback(agent_name, "active", f"Starting {step['task']}")

        await asyncio.sleep(0.5)  # Simulate processing

        # Return mock results based on agent type
        if agent_name == "PDFSearcher":
            return {
                "pdfs_found": 8,
                "relevant_pdfs": 5,
                "total_scanned": 23
            }
        elif agent_name == "PDFParser":
            return {
                "pages_parsed": 142,
                "charts_found": 7,
                "tables_found": 12
            }
        elif agent_name == "DocumentResearcher":
            return {
                "documents_searched": 156,
                "relevant_chunks": 34
            }
        elif agent_name == "ReportGenerator":
            return {
                "report_generated": True,
                "word_count": 2450,
                "sections": 3
            }

        return {"status": "completed"}
