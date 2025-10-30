"""
PDF Searcher Agent - Discovers relevant PDFs from local filesystem.
Shows intelligent filtering and relevance ranking.
"""

import os
import glob
from typing import Callable, Dict, Any, List
from agents.base_agent import BaseAgent
from models.messages import TaskMessage, AgentResult


class PDFSearcherAgent(BaseAgent):
    """
    Searches local filesystem for relevant PDFs.
    Demonstrates intelligent document discovery and ranking.
    """

    def __init__(self, nvidia_client, search_paths: List[str] = None):
        super().__init__(
            name="PDFSearcher",
            description="Discovers and ranks relevant PDF documents",
            nvidia_client=nvidia_client
        )
        self.search_paths = search_paths or ["./sample_data/pdfs"]

    async def _generate_plan(
        self,
        reasoning: str,
        task: TaskMessage,
        ui_callback: Callable
    ) -> List[str]:
        """Generate search plan."""
        return [
            "Scan directories for PDF files",
            "Extract metadata from PDFs",
            "Rank by relevance to topics",
            "Select top candidates"
        ]

    async def _execute_plan(
        self,
        plan: List[str],
        task: TaskMessage,
        ui_callback: Callable
    ) -> Dict[str, Any]:
        """
        Execute PDF search with visible progress.
        """

        import asyncio

        topics = task.context.get("topics", [])
        ui_callback(self.name, "info", f"Searching for PDFs related to: {', '.join(topics)}")

        # Step 1: Scan directories
        ui_callback(self.name, "progress", "Step 1/4: Scanning directories...")
        all_pdfs = []
        for search_path in self.search_paths:
            if os.path.exists(search_path):
                pattern = os.path.join(search_path, "**", "*.pdf")
                pdfs = glob.glob(pattern, recursive=True)
                all_pdfs.extend(pdfs)

        self.metrics['tools_called'] += 1
        ui_callback(self.name, "metric", f"Found {len(all_pdfs)} PDFs in filesystem")

        await asyncio.sleep(0.3)

        # Step 2: Extract metadata (simulated)
        ui_callback(self.name, "progress", "Step 2/4: Extracting metadata...")
        pdf_metadata = []
        for pdf_path in all_pdfs:
            filename = os.path.basename(pdf_path)
            pdf_metadata.append({
                "path": pdf_path,
                "filename": filename,
                "size": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
            })

        await asyncio.sleep(0.3)

        # Step 3: Rank by relevance
        ui_callback(self.name, "progress", "Step 3/4: Ranking by relevance...")
        ranked_pdfs = await self._rank_pdfs(pdf_metadata, topics, ui_callback)

        decision = self.log_decision(
            decision=f"Selected top {min(5, len(ranked_pdfs))} PDFs",
            reasoning=f"Ranked {len(ranked_pdfs)} PDFs by keyword matching with topics",
            options=[f"Top {n}" for n in [3, 5, 10]],
            confidence=0.78
        )

        await asyncio.sleep(0.3)

        # Step 4: Select top candidates
        ui_callback(self.name, "progress", "Step 4/4: Selecting top candidates...")
        top_pdfs = ranked_pdfs[:5]

        ui_callback(
            self.name,
            "result",
            f"✅ Selected {len(top_pdfs)} PDFs for parsing"
        )

        return {
            "total_scanned": len(all_pdfs),
            "pdfs_found": len(ranked_pdfs),
            "relevant_pdfs": top_pdfs,
            "search_paths": self.search_paths
        }

    async def _rank_pdfs(
        self,
        pdf_metadata: List[Dict[str, Any]],
        topics: List[str],
        ui_callback: Callable
    ) -> List[Dict[str, Any]]:
        """
        Rank PDFs by relevance to topics.
        """

        # Simple keyword-based ranking for demo
        ranked = []
        for pdf in pdf_metadata:
            score = 0
            filename_lower = pdf['filename'].lower()

            # Check for topic keywords in filename
            for topic in topics:
                topic_words = topic.lower().split()
                for word in topic_words:
                    if word in filename_lower:
                        score += 1

            pdf['relevance_score'] = score
            if score > 0:
                ranked.append(pdf)

        # Sort by relevance score
        ranked.sort(key=lambda x: x['relevance_score'], reverse=True)

        ui_callback(
            self.name,
            "insight",
            f"Ranked PDFs: {len(ranked)} relevant out of {len(pdf_metadata)} total"
        )

        return ranked
