"""
utils/llm_client.py — Provider-agnostic LLM wrapper.

WHY THIS EXISTS:
    Every module in this course imports LLMClient rather than calling
    openai.chat.completions.create() directly.  This single abstraction means:

    1. Swap providers (OpenAI → Anthropic → local Ollama) by changing ONE env var.
    2. Automatic retry with exponential back-off on rate-limit errors.
    3. Built-in token counting and cost estimation on every call.
    4. Dry-run mode: print the prompt without spending a token.
    5. Structured logging of every request/response for later analysis.

SUPPORTED PROVIDERS:
    - openai   : GPT-4o, GPT-4o-mini, GPT-3.5-turbo, etc.
    - anthropic: Claude 3 Haiku / Sonnet / Opus
    - local    : Any OpenAI-compatible server (Ollama, LM Studio, vLLM)
"""

from __future__ import annotations

import os
import time
import logging
from typing import Optional

from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Pricing table (USD per 1,000 tokens) — update as providers change pricing
# ─────────────────────────────────────────────────────────────────────────────
PRICING: dict[str, dict[str, float]] = {
    # model_id: {"input": $/1K tokens, "output": $/1K tokens}
    "gpt-4o":             {"input": 0.005,    "output": 0.015},
    "gpt-4o-mini":        {"input": 0.000150, "output": 0.000600},
    "gpt-4-turbo":        {"input": 0.010,    "output": 0.030},
    "gpt-3.5-turbo":      {"input": 0.0005,   "output": 0.0015},
    "claude-3-haiku":     {"input": 0.00025,  "output": 0.00125},
    "claude-3-sonnet":    {"input": 0.003,    "output": 0.015},
    "claude-3-opus":      {"input": 0.015,    "output": 0.075},
    # Fallback for unknown / local models (treat as free)
    "local":              {"input": 0.0,      "output": 0.0},
}


class LLMResponse:
    """Structured container for LLM API responses."""

    def __init__(
        self,
        content: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
    ):
        self.content = content            # The actual text response
        self.model = model                # Which model produced the response
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.latency_ms = latency_ms

        # Calculate cost using pricing table (fall back to "local" for unknowns)
        pricing_key = next(
            (k for k in PRICING if model.startswith(k)), "local"
        )
        price = PRICING[pricing_key]
        self.cost_usd = (
            (prompt_tokens / 1000) * price["input"]
            + (completion_tokens / 1000) * price["output"]
        )

    def __repr__(self) -> str:
        return (
            f"LLMResponse(model={self.model!r}, "
            f"tokens={self.total_tokens}, "
            f"cost=${self.cost_usd:.6f}, "
            f"latency={self.latency_ms:.0f}ms)"
        )


class LLMClient:
    """
    Provider-agnostic wrapper for LLM API calls.

    Usage:
        client = LLMClient()
        response = client.chat("Summarize this article: ...")
        print(response.content)
        print(response.cost_usd)

    Provider is selected via the LLM_PROVIDER environment variable:
        LLM_PROVIDER=openai     → uses openai SDK
        LLM_PROVIDER=anthropic  → uses anthropic SDK
        LLM_PROVIDER=local      → OpenAI-compatible local server
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        dry_run: Optional[bool] = None,
    ):
        # Allow env var overrides or explicit constructor args
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Dry-run: print prompt, skip API call (saves money during development)
        env_dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        self.dry_run = dry_run if dry_run is not None else env_dry_run

        # Initialize the appropriate SDK client
        if self.provider == "openai" or self.provider == "local":
            self._init_openai(model)
        elif self.provider == "anthropic":
            self._init_anthropic(model)
        else:
            raise ValueError(
                f"Unknown provider: {self.provider!r}. "
                "Set LLM_PROVIDER to 'openai', 'anthropic', or 'local'."
            )

    # ─────────────────────────────────────────────────────────────
    # Provider initializers
    # ─────────────────────────────────────────────────────────────

    def _init_openai(self, model: Optional[str]) -> None:
        """Set up the OpenAI (or compatible) client."""
        try:
            from openai import OpenAI, RateLimitError, APIError
        except ImportError:
            raise ImportError("Run: pip install openai")

        self._RateLimitError = RateLimitError
        self._APIError = APIError

        base_url = os.getenv("OPENAI_BASE_URL")  # None → official OpenAI endpoint
        api_key = os.getenv("OPENAI_API_KEY", "sk-no-key-set")

        # For local providers (Ollama etc.) a dummy key is fine
        if self.provider == "local" and api_key == "sk-no-key-set":
            api_key = "local"

        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def _init_anthropic(self, model: Optional[str]) -> None:
        """Set up the Anthropic (Claude) client."""
        try:
            from anthropic import Anthropic, RateLimitError, APIError
        except ImportError:
            raise ImportError("Run: pip install anthropic")

        self._RateLimitError = RateLimitError
        self._APIError = APIError
        self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        self.model = model or "claude-3-haiku-20240307"

    # ─────────────────────────────────────────────────────────────
    # Core chat method
    # ─────────────────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        messages: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Send a chat completion request to the configured LLM.

        Args:
            user_message:   The human turn message (required unless messages is set).
            system_message: Optional system/persona instructions.
            messages:       Full conversation history (overrides user_message if given).
            temperature:    Override instance default temperature.
            max_tokens:     Override instance default max_tokens.

        Returns:
            LLMResponse with .content, .cost_usd, .total_tokens, .latency_ms
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        # Build message list
        if messages is None:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": user_message})

        # ── Dry-run mode ──────────────────────────────────────────
        if self.dry_run:
            self._print_dry_run(messages, temp, max_tok)
            return LLMResponse(
                content="[DRY RUN — no API call made]",
                model=self.model,
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=0,
            )

        # ── Actual API call ───────────────────────────────────────
        if self.provider in ("openai", "local"):
            return self._call_openai(messages, temp, max_tok)
        else:
            return self._call_anthropic(messages, temp, max_tok)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    def _call_openai(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Issue request to OpenAI (retries on rate limit)."""
        start = time.perf_counter()
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            latency_ms=latency_ms,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    def _call_anthropic(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Issue request to Anthropic Claude (retries on rate limit)."""
        # Separate system message from conversation
        system = ""
        conv_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                conv_messages.append(msg)

        start = time.perf_counter()
        response = self._client.messages.create(
            model=self.model,
            system=system or "You are a helpful assistant.",
            messages=conv_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        content = response.content[0].text if response.content else ""
        usage = response.usage
        return LLMResponse(
            content=content,
            model=response.model,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            latency_ms=latency_ms,
        )

    # ─────────────────────────────────────────────────────────────
    # Helper utilities
    # ─────────────────────────────────────────────────────────────

    def _print_dry_run(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> None:
        """Display the prompt that would be sent, without calling the API."""
        separator = "─" * 60
        print(f"\n{'[DRY RUN MODE]':^60}")
        print(separator)
        print(f"  Model: {self.model}  |  temp={temperature}  |  max_tokens={max_tokens}")
        print(separator)
        for msg in messages:
            role = msg["role"].upper()
            print(f"\n[{role}]\n{msg['content']}")
        print(f"\n{separator}\n")

    def get_model_info(self) -> dict:
        """Return metadata about the currently configured model."""
        pricing_key = next(
            (k for k in PRICING if self.model.startswith(k)), "local"
        )
        return {
            "provider": self.provider,
            "model": self.model,
            "pricing": PRICING[pricing_key],
            "dry_run": self.dry_run,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Quick self-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing LLMClient (dry-run mode)...")

    # Test with dry_run=True so no API key is required
    client = LLMClient(dry_run=True)
    response = client.chat(
        system_message="You are a helpful assistant.",
        user_message="What is prompt engineering?",
    )
    print(f"\nResponse object: {response}")
    print(f"Provider info: {client.get_model_info()}")
    print("\n✅ LLMClient is working correctly.")
