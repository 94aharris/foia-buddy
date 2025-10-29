import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json


class NvidiaClient:
    """NVIDIA Nemotron API client wrapper."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("NVIDIA API key required. Set NVIDIA_API_KEY environment variable.")

        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "nvidia/nvidia-nemotron-nano-9b-v2",
        temperature: float = 0.6,
        max_tokens: int = 2048,
        use_thinking: bool = True
    ) -> Dict[str, Any]:
        """Generate response using NVIDIA Nemotron model."""

        extra_body = {}
        if use_thinking:
            extra_body = {
                "min_thinking_tokens": 512,
                "max_thinking_tokens": 1024
            }

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=0.95,
                max_tokens=max_tokens,
                frequency_penalty=0,
                presence_penalty=0,
                stream=False,
                extra_body=extra_body
            )

            response = {
                "content": completion.choices[0].message.content,
                "reasoning": getattr(completion.choices[0].message, "reasoning_content", ""),
                "model": model,
                "usage": completion.usage.dict() if completion.usage else {}
            }

            return response

        except Exception as e:
            return {
                "error": str(e),
                "content": "",
                "reasoning": "",
                "model": model,
                "usage": {}
            }

    def generate_with_function_calling(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        model: str = "nvidia/nvidia-nemotron-nano-9b-v2"
    ) -> Dict[str, Any]:
        """Generate response with function calling capability."""

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
                functions=functions,
                function_call="auto",
                temperature=0.6,
                max_tokens=2048
            )

            message = completion.choices[0].message

            response = {
                "content": message.content,
                "function_call": message.function_call.dict() if message.function_call else None,
                "model": model,
                "usage": completion.usage.dict() if completion.usage else {}
            }

            return response

        except Exception as e:
            return {
                "error": str(e),
                "content": "",
                "function_call": None,
                "model": model,
                "usage": {}
            }