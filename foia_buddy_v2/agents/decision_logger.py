"""
Agent decision tracking system for demo visualization.
"""

from typing import List, Dict, Any
from models.messages import DecisionPoint


class DecisionLogger:
    """
    Centralized decision tracking for all agents.
    Used to visualize decision-making process in the UI.
    """

    def __init__(self):
        self.decisions: List[DecisionPoint] = []

    def log(self, decision: DecisionPoint):
        """Log a decision point."""
        self.decisions.append(decision)

    def get_decisions_by_agent(self, agent_name: str) -> List[DecisionPoint]:
        """Get all decisions made by a specific agent."""
        return [d for d in self.decisions if d.agent_name == agent_name]

    def get_all_decisions(self) -> List[DecisionPoint]:
        """Get all logged decisions."""
        return self.decisions

    def clear(self):
        """Clear all logged decisions."""
        self.decisions = []

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of decisions."""
        agent_counts = {}
        for decision in self.decisions:
            agent_counts[decision.agent_name] = agent_counts.get(decision.agent_name, 0) + 1

        return {
            "total_decisions": len(self.decisions),
            "by_agent": agent_counts,
            "average_confidence": sum(d.confidence for d in self.decisions) / len(self.decisions) if self.decisions else 0.0
        }
