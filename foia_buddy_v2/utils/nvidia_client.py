"""
NVIDIA API Client with streaming support for Nemotron models.
Supports thinking tokens and real-time streaming for demo visualization.
"""

import os
import json
from typing import AsyncIterator, Dict, Any, Optional
import asyncio
from dataclasses import dataclass
import aiohttp


@dataclass
class StreamChunk:
    """Represents a chunk of streamed content."""
    content: str
    is_thinking: bool = False
    metadata: Optional[Dict[str, Any]] = None


class NvidiaClient:
    """
    Client for NVIDIA API with streaming support.
    Optimized for demo visualization with thinking tokens.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"

        # Model configurations
        self.models = {
            "reasoning": "nvidia/nvidia-nemotron-nano-9b-v2",
            "parse": "nvidia/nv-embed-v1",
            "fast": "nvidia/nvidia-nemotron-nano-9b-v2"
        }

    async def stream_with_thinking(
        self,
        prompt: str,
        model: str = "reasoning",
        temperature: float = 0.6,
        max_tokens: int = 2048,
        min_thinking_tokens: int = 1024,
        max_thinking_tokens: int = 2048
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream response with thinking tokens visible.
        Yields both thinking tokens and final response.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.models.get(model, model),
            "messages": [{"role": "system", "content": "/think"}],
            "temperature": temperature,
            "top_p": 0.95,
            "max_tokens": max_tokens,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": True,
            "extra_body": {
                "min_thinking_tokens": min_thinking_tokens,
                "max_thinking_tokens": max_thinking_tokens
            }
        }

        # Add user message
        payload["messages"].append({"role": "user", "content": prompt})

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"NVIDIA API Error {response.status}: {error_text}")

                async for line in response.content:
                    if line:
                        line_text = line.decode('utf-8').strip()
                        if line_text.startswith('data: '):
                            if line_text == 'data: [DONE]':
                                break
                            try:
                                data = json.loads(line_text[6:])
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})

                                    # Check for reasoning content (thinking tokens)
                                    reasoning = delta.get('reasoning_content')
                                    if reasoning:
                                        yield StreamChunk(
                                            content=reasoning,
                                            is_thinking=True,
                                            metadata=data
                                        )

                                    # Check for regular content
                                    content = delta.get('content', '')
                                    if content:
                                        yield StreamChunk(
                                            content=content,
                                            is_thinking=False,
                                            metadata=data
                                        )
                            except json.JSONDecodeError:
                                continue

    async def complete(
        self,
        prompt: str,
        model: str = "reasoning",
        temperature: float = 0.6,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
        use_thinking: bool = False
    ) -> str:
        """
        Get complete response without streaming.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        elif use_thinking:
            messages.append({"role": "system", "content": "/think"})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.models.get(model, model),
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.95,
            "max_tokens": max_tokens,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

        if use_thinking:
            payload["extra_body"] = {
                "min_thinking_tokens": 1024,
                "max_thinking_tokens": 2048
            }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"NVIDIA API Error {response.status}: {error_text}")

                result = await response.json()
                return result['choices'][0]['message']['content']

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for semantic search using NVIDIA API."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.models["parse"],
            "input": text
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"NVIDIA Embeddings API Error {response.status}: {error_text}")

                result = await response.json()
                return result['data'][0]['embedding']
