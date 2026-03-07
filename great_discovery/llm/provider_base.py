"""
llm/provider_base.py
The Great Discovery

Base class and Anthropic API provider for LLM-powered investigation.

Two providers:
    LLMProvider          -- abstract base, implement complete(prompt) -> str
    AnthropicProvider    -- calls the Anthropic API (claude-sonnet-4-20250514)
    LocalLLMProvider     -- stub for local models (in local_llm_provider.py)

Usage:
    from llm.provider_base import AnthropicProvider
    llm = AnthropicProvider()
    response = llm.complete("What concept bridges physics and biology?")
"""

import json
import urllib.request
import urllib.error


class LLMProvider:
    """Abstract base. Subclasses implement complete(prompt) -> str."""

    def complete(self, prompt):
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    """
    Calls the Anthropic API.

    The API key is read from the ANTHROPIC_API_KEY environment variable,
    or can be passed directly at construction time.

    Model: claude-sonnet-4-20250514
    """

    MODEL   = "claude-sonnet-4-20250514"
    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key=None, max_tokens=512):
        import os
        self.api_key    = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.max_tokens = max_tokens

    def complete(self, prompt):
        """
        Send prompt to Anthropic API and return the response text.
        Returns empty string on any error so the engine degrades gracefully.
        """
        if not self.api_key:
            return ""

        payload = json.dumps({
            "model":      self.MODEL,
            "max_tokens": self.max_tokens,
            "messages":   [{"role": "user", "content": prompt}],
        }).encode("utf-8")

        req = urllib.request.Request(
            self.API_URL,
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["content"][0]["text"].strip()
        except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError):
            return ""
