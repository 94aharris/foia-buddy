from typing import List, Dict, Any, Optional
import time
from datetime import datetime
import urllib.parse
from pathlib import Path
from .base import BaseAgent
from ..models import AgentResult, TaskMessage


class PublicFOIASearchAgent(BaseAgent):
    """
    Searches the State Department's public FOIA library for previously released documents.

    Uses the public FOIA library search API with URL parameters to find documents
    that have already been released through FOIA requests.
    """

    def __init__(self, nvidia_client):
        super().__init__(
            name="public_foia_search",
            description="Searches the State Department FOIA public library for previously released documents",
            nvidia_client=nvidia_client
        )
        self.base_url = "https://foia.state.gov/FOIALIBRARY/SearchResults.aspx"
        self.add_capability("public_document_search")
        self.add_capability("released_foia_analysis")
        self.add_capability("precedent_research")
        self.add_capability("document_download")

    def get_system_prompt(self) -> str:
        return """You are the Public FOIA Search Agent for FOIA-Buddy.

Your role is to:
1. SEARCH the State Department's public FOIA library for previously released documents
2. IDENTIFY relevant documents that have already been made public through FOIA
3. ANALYZE public FOIA documents to find precedents and similar requests
4. EXTRACT useful information from publicly available FOIA releases

When searching the public library:
- Extract key search terms from the FOIA request
- Focus on documents from the relevant timeframe
- Identify document types most likely to contain requested information
- Look for similar FOIA requests that have been fulfilled
- Note case numbers for reference and citation

Provide structured analysis including:
- search_strategy: The search approach and keywords used
- key_findings: Important publicly available documents found
- relevance_scores: How relevant each document is to the current request
- case_references: Case numbers for citation
- precedents: Similar FOIA requests that have been fulfilled"""

    async def execute(self, task: TaskMessage) -> AgentResult:
        """Execute public FOIA library search task."""
        start_time = time.time()

        try:
            # Get FOIA request from task
            foia_request = task.context.get("foia_request", "")

            # Analyze the request to determine search strategy
            search_strategy = await self._plan_search_strategy(foia_request)

            if "error" in search_strategy:
                return self._create_result(
                    task.task_id,
                    success=False,
                    data={"error": search_strategy["error"]},
                    reasoning="Failed to plan search strategy",
                    confidence=0.0,
                    start_time=start_time
                )

            # Perform searches with multiple keyword combinations
            all_results = []
            search_attempts = []

            # Try top keywords
            keywords = search_strategy.get("keywords", [])
            for keyword in keywords[:5]:  # Try top 5 keywords
                search_results = await self._search_foia_library(keyword)
                search_attempts.append({
                    "keyword": keyword,
                    "results_count": search_results.get("total_results", 0),
                    "status": search_results.get("status", "unknown")
                })

                if search_results.get("documents"):
                    all_results.extend(search_results["documents"])

            # Try combined searches
            if len(keywords) >= 2:
                combined_search = f"{keywords[0]} {keywords[1]}"
                search_results = await self._search_foia_library(combined_search)
                search_attempts.append({
                    "keyword": combined_search,
                    "results_count": search_results.get("total_results", 0),
                    "status": search_results.get("status", "unknown")
                })

                if search_results.get("documents"):
                    all_results.extend(search_results["documents"])

            # Deduplicate results by case number
            unique_docs = self._deduplicate_documents(all_results)

            # Download PDFs if requested
            download_dir = task.context.get("download_dir")
            downloaded_pdfs = []

            if download_dir and unique_docs:
                # Download top relevant documents (limit to avoid too many downloads)
                max_downloads = task.context.get("max_downloads", 10)
                docs_to_download = unique_docs[:max_downloads]

                downloaded_pdfs = await self._download_documents(
                    docs_to_download,
                    download_dir
                )

            # Analyze the results
            if unique_docs:
                analyzed_results = await self._analyze_search_results(unique_docs, foia_request)
            else:
                analyzed_results = {
                    "summary": "No publicly available FOIA documents found matching search criteria",
                    "relevance": "NONE",
                    "recommendations": [
                        "The requested information may not have been previously released",
                        "Try alternative search terms or broader queries",
                        "Consider that documents may be classified or not yet processed"
                    ]
                }

            result_data = {
                "search_strategy": search_strategy,
                "search_attempts": search_attempts,
                "total_documents_found": len(unique_docs),
                "documents": unique_docs[:20],  # Return top 20 most relevant
                "downloaded_pdfs": downloaded_pdfs,
                "download_count": len(downloaded_pdfs),
                "analysis": analyzed_results,
                "search_url_base": self.base_url,
                "search_timestamp": datetime.now().isoformat()
            }

            reasoning = (
                f"Searched public FOIA library with {len(search_attempts)} keyword combinations, "
                f"found {len(unique_docs)} unique documents"
            )

            return self._create_result(
                task.task_id,
                success=True,
                data=result_data,
                reasoning=reasoning,
                confidence=0.85 if unique_docs else 0.6,
                start_time=start_time
            )

        except Exception as e:
            return self._create_result(
                task.task_id,
                success=False,
                data={"error": str(e)},
                reasoning=f"Error during public FOIA search: {str(e)}",
                confidence=0.0,
                start_time=start_time
            )

    async def _plan_search_strategy(self, foia_request: str) -> Dict[str, Any]:
        """Use AI to analyze FOIA request and plan search strategy."""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""
Analyze this FOIA request and create a search strategy for the public FOIA library:

FOIA REQUEST:
{foia_request}

Extract the most important search keywords (5-10 terms) that would be effective for finding
relevant documents in the State Department's FOIA library. Consider:
1. Main topics and subjects
2. Specific names, organizations, or programs mentioned
3. Document types likely to contain this information
4. Time periods covered

List the keywords in order of importance, with the most specific and relevant terms first.
"""}
        ]

        response = await self._generate_response(messages, use_thinking=True)

        if "error" in response:
            return {"error": response["error"]}

        content = response["content"]

        # Parse the AI response to extract keywords
        strategy = {
            "raw_analysis": content,
            "keywords": self._extract_keywords(content, foia_request),
            "reasoning": response.get("reasoning", "")
        }

        return strategy

    def _extract_keywords(self, analysis: str, foia_request: str) -> List[str]:
        """Extract key search terms from AI analysis and FOIA request."""
        keywords = []

        # Extract from both analysis and original request
        combined_text = (analysis + " " + foia_request).lower()

        # Domain-specific important terms
        important_terms = [
            'artificial intelligence',
            'ai',
            'machine learning',
            'algorithm',
            'automation',
            'policy',
            'governance',
            'framework',
            'guidelines',
            'ethics',
            'implementation',
            'oversight',
            'compliance',
            'regulation',
            'transparency',
            'accountability',
            'risk assessment',
            'audit',
            'deployment',
            'training',
            'technology',
            'innovation',
            'digital',
            'data'
        ]

        # Find matching terms
        for term in important_terms:
            if term in combined_text and term not in keywords:
                keywords.append(term)

        # Extract quoted phrases
        import re
        quoted = re.findall(r'"([^"]+)"', analysis + " " + foia_request)
        for phrase in quoted:
            if len(phrase) > 3 and phrase.lower() not in keywords:
                keywords.append(phrase.lower())

        # Ensure we have good keywords
        if not keywords:
            keywords = ["policy", "government", "technology"]

        return keywords[:10]  # Return top 10

    async def _search_foia_library(self, search_text: str) -> Dict[str, Any]:
        """
        Perform actual search of the FOIA library using URL parameters.

        Args:
            search_text: The search query string

        Returns:
            Dictionary with search results and metadata
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return {
                "total_results": 0,
                "documents": [],
                "status": "error",
                "error": "Required libraries not installed. Run: pip install requests beautifulsoup4 lxml"
            }

        try:
            # Build search URL with parameters
            params = {
                "searchText": search_text
            }
            search_url = f"{self.base_url}?{urllib.parse.urlencode(params)}"

            # Make request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for "zero results" message
            zero_results = soup.find(string=lambda text: text and "zero results" in text.lower())
            if zero_results:
                return {
                    "total_results": 0,
                    "documents": [],
                    "status": "success",
                    "search_text": search_text,
                    "search_url": search_url
                }

            # Parse results table
            documents = self._parse_search_results(soup)

            return {
                "total_results": len(documents),
                "documents": documents,
                "status": "success",
                "search_text": search_text,
                "search_url": search_url
            }

        except requests.RequestException as e:
            return {
                "total_results": 0,
                "documents": [],
                "status": "error",
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                "total_results": 0,
                "documents": [],
                "status": "error",
                "error": f"Parse error: {str(e)}"
            }

    def _parse_search_results(self, soup: 'BeautifulSoup') -> List[Dict[str, Any]]:
        """
        Parse search results from HTML.

        The results are in a table with columns:
        Subject, Document Date, Sent From, Sent To, Posted Date, Case Number
        """
        documents = []

        try:
            # Find the results table - look for common patterns
            results_table = (
                soup.find('table', id=lambda x: x and 'GridView' in str(x)) or
                soup.find('table', class_=lambda x: x and 'GridView' in str(x)) or
                soup.find('table', attrs={'class': 'table'}) or
                soup.find_all('table')[-1] if soup.find_all('table') else None
            )

            if not results_table:
                return documents

            # Find all data rows (skip header)
            rows = results_table.find_all('tr')

            for row in rows[1:]:  # Skip header row
                cells = row.find_all('td')

                if len(cells) >= 4:  # Ensure we have enough cells
                    # Extract text from each cell
                    doc = {
                        "subject": cells[0].get_text(strip=True) if len(cells) > 0 else "",
                        "document_date": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                        "sent_from": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                        "sent_to": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                        "posted_date": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                        "case_number": cells[5].get_text(strip=True) if len(cells) > 5 else "",
                    }

                    # Try to find document link
                    link = cells[0].find('a') if cells else None
                    if link and link.get('href'):
                        href = link['href']
                        if href.startswith('/'):
                            doc["url"] = f"https://foia.state.gov{href}"
                        elif href.startswith('http'):
                            doc["url"] = href
                        else:
                            doc["url"] = f"https://foia.state.gov/FOIALIBRARY/{href}"

                    # Only add if we have substantive data
                    if doc["subject"] or doc["case_number"]:
                        documents.append(doc)

        except Exception as e:
            # Log error but don't fail completely
            pass

        return documents

    def _deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents based on case number and subject."""
        seen = set()
        unique = []

        for doc in documents:
            # Create unique identifier from case number and subject
            identifier = f"{doc.get('case_number', '')}_{doc.get('subject', '')}"

            if identifier not in seen and identifier != "_":
                seen.add(identifier)
                unique.append(doc)

        return unique

    async def _analyze_search_results(
        self,
        documents: List[Dict[str, Any]],
        foia_request: str
    ) -> Dict[str, Any]:
        """Analyze search results for relevance to FOIA request."""

        if not documents:
            return {
                "summary": "No public documents found",
                "relevance": "NONE",
                "top_matches": [],
                "recommendations": ["Try alternative search terms"]
            }

        # Prepare document summaries for AI analysis
        doc_summaries = "\n\n".join([
            f"Document {i+1}:\n"
            f"  Subject: {doc.get('subject', 'N/A')}\n"
            f"  Date: {doc.get('document_date', 'N/A')}\n"
            f"  From: {doc.get('sent_from', 'N/A')}\n"
            f"  To: {doc.get('sent_to', 'N/A')}\n"
            f"  Case: {doc.get('case_number', 'N/A')}"
            for i, doc in enumerate(documents[:15])  # Analyze top 15
        ])

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""
Analyze these publicly available FOIA documents for relevance to the current request:

CURRENT FOIA REQUEST:
{foia_request}

PUBLICLY AVAILABLE DOCUMENTS FOUND:
{doc_summaries}

Provide:
1. Overall relevance assessment
2. Which specific documents seem most relevant (by number)
3. What information they likely contain that addresses the request
4. Recommendations for using these public documents
5. Any gaps that still need to be filled from other sources
"""}
        ]

        response = await self._generate_response(messages, use_thinking=True)

        # Score documents for relevance
        scored_docs = self._score_document_relevance(documents, foia_request)

        return {
            "summary": response.get("content", "Analysis unavailable")[:600],
            "total_analyzed": len(documents),
            "relevance": self._estimate_overall_relevance(scored_docs),
            "top_matches": [
                {
                    "case_number": doc.get("case_number", ""),
                    "subject": doc.get("subject", "")[:100],
                    "relevance_score": doc.get("relevance_score", 0.0)
                }
                for doc in scored_docs[:5]
            ],
            "recommendations": self._generate_recommendations(documents, foia_request)
        }

    def _score_document_relevance(
        self,
        documents: List[Dict[str, Any]],
        foia_request: str
    ) -> List[Dict[str, Any]]:
        """Score documents for relevance using keyword matching."""

        # Extract keywords from request
        request_lower = foia_request.lower()
        request_words = set(request_lower.split())

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        request_keywords = request_words - stop_words

        scored = []
        for doc in documents:
            # Combine subject and sender/recipient for scoring
            doc_text = f"{doc.get('subject', '')} {doc.get('sent_from', '')} {doc.get('sent_to', '')}".lower()

            # Count keyword matches
            matches = sum(1 for keyword in request_keywords if keyword in doc_text and len(keyword) > 2)

            # Calculate score (0.0 to 1.0)
            score = min(matches / max(len(request_keywords), 1), 1.0) if request_keywords else 0.0

            doc_copy = doc.copy()
            doc_copy["relevance_score"] = score
            scored.append(doc_copy)

        # Sort by relevance score
        scored.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)

        return scored

    def _estimate_overall_relevance(self, scored_docs: List[Dict[str, Any]]) -> str:
        """Estimate overall relevance of found documents."""
        if not scored_docs:
            return "NONE"

        avg_score = sum(d.get("relevance_score", 0.0) for d in scored_docs[:10]) / min(len(scored_docs), 10)

        if avg_score >= 0.6:
            return "HIGH"
        elif avg_score >= 0.3:
            return "MEDIUM"
        elif avg_score > 0:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_recommendations(
        self,
        documents: List[Dict[str, Any]],
        foia_request: str
    ) -> List[str]:
        """Generate recommendations based on search results."""
        recommendations = []

        if len(documents) > 30:
            recommendations.append("Many public documents found - prioritize most recent and relevant")
        elif len(documents) > 10:
            recommendations.append("Moderate number of public documents available for review")
        elif len(documents) > 0:
            recommendations.append("Limited public documents found - may need broader search or local sources")

        recommendations.append("Review case numbers for citation in final FOIA response")
        recommendations.append("Download and analyze full document PDFs for detailed information")
        recommendations.append("Cross-reference with local document repository for additional context")

        return recommendations
