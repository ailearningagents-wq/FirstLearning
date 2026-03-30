"""
utils/helpers.py — Token counting, cost estimation, and response formatting.

These utilities are used throughout the curriculum to make every example
cost-transparent and visually clean in the terminal.
"""

from __future__ import annotations

import os
import textwrap
from typing import Optional, Union

# ─────────────────────────────────────────────────────────────────────────────
# Token counting
# ─────────────────────────────────────────────────────────────────────────────

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Count the number of tokens in a string using tiktoken.

    tiktoken is OpenAI's official tokenizer — same one the API uses.
    For non-OpenAI models we fall back to a rough word-based estimate.

    Args:
        text:  The string to tokenize.
        model: Model name (determines which BPE encoding to use).

    Returns:
        Integer token count.

    Example:
        >>> count_tokens("Hello, world!")
        4
    """
    try:
        import tiktoken

        # tiktoken encoding names differ from model names
        encoding_map = {
            "gpt-4o":        "o200k_base",
            "gpt-4o-mini":   "o200k_base",
            "gpt-4-turbo":   "cl100k_base",
            "gpt-4":         "cl100k_base",
            "gpt-3.5-turbo": "cl100k_base",
        }
        encoding_name = next(
            (v for k, v in encoding_map.items() if model.startswith(k)),
            "cl100k_base",   # safe default
        )
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))

    except ImportError:
        # Rough fallback: ~0.75 words per token (average for English text)
        word_count = len(text.split())
        return int(word_count / 0.75)


def count_messages_tokens(messages: list[dict], model: str = "gpt-4o-mini") -> int:
    """
    Count tokens for a full messages list (as passed to chat completions).

    Includes per-message overhead tokens (role headers, etc.).

    Args:
        messages: List of {"role": ..., "content": ...} dicts.
        model:    Model name for encoding selection.

    Returns:
        Total estimated token count.
    """
    # OpenAI adds ~4 tokens per message for role formatting
    tokens_per_message = 4
    total = 0
    for msg in messages:
        total += tokens_per_message
        total += count_tokens(msg.get("content", ""), model)
        total += count_tokens(msg.get("role", ""), model)
    total += 3  # Reply priming tokens
    return total


# ─────────────────────────────────────────────────────────────────────────────
# Cost estimation
# ─────────────────────────────────────────────────────────────────────────────

# Pricing: USD per 1,000 tokens (keep in sync with llm_client.py)
COST_PER_1K: dict[str, dict[str, float]] = {
    "gpt-4o":             {"input": 0.005,    "output": 0.015},
    "gpt-4o-mini":        {"input": 0.000150, "output": 0.000600},
    "gpt-4-turbo":        {"input": 0.010,    "output": 0.030},
    "gpt-3.5-turbo":      {"input": 0.0005,   "output": 0.0015},
    "claude-3-haiku":     {"input": 0.00025,  "output": 0.00125},
    "claude-3-sonnet":    {"input": 0.003,    "output": 0.015},
    "claude-3-opus":      {"input": 0.015,    "output": 0.075},
}


def estimate_cost(
    prompt: Union[str, list[dict]],
    model: str = "gpt-4o-mini",
    expected_output_tokens: int = 256,
) -> dict[str, float]:
    """
    Estimate the USD cost of sending a prompt to the specified model.

    Args:
        prompt:                 Either a string or a messages list.
        model:                  Model name for pricing lookup.
        expected_output_tokens: Approximate completion length (default 256).

    Returns:
        Dict with keys: input_tokens, output_tokens, total_tokens,
                        input_cost, output_cost, total_cost (all in USD).

    Example:
        >>> est = estimate_cost("Summarize this 500-word article...", model="gpt-4o-mini")
        >>> print(f"Estimated cost: ${est['total_cost']:.6f}")
    """
    if isinstance(prompt, str):
        input_tokens = count_tokens(prompt, model)
    else:
        input_tokens = count_messages_tokens(prompt, model)

    pricing_key = next(
        (k for k in COST_PER_1K if model.startswith(k)), None
    )
    if pricing_key is None:
        # Unknown model → treat as free (local)
        return {
            "input_tokens": input_tokens,
            "output_tokens": expected_output_tokens,
            "total_tokens": input_tokens + expected_output_tokens,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
        }

    prices = COST_PER_1K[pricing_key]
    input_cost = (input_tokens / 1000) * prices["input"]
    output_cost = (expected_output_tokens / 1000) * prices["output"]

    return {
        "input_tokens": input_tokens,
        "output_tokens": expected_output_tokens,
        "total_tokens": input_tokens + expected_output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
    }


def print_cost_estimate(
    prompt: Union[str, list[dict]],
    model: str = "gpt-4o-mini",
    expected_output_tokens: int = 256,
    label: str = "Cost Estimate",
) -> None:
    """Print a formatted cost estimate table to stdout."""
    est = estimate_cost(prompt, model, expected_output_tokens)
    line = "─" * 50
    print(f"\n{line}")
    print(f"  💰 {label}")
    print(f"  Model          : {model}")
    print(f"  Input tokens   : {est['input_tokens']:,}")
    print(f"  Output tokens  : {est['output_tokens']:,}  (estimated)")
    print(f"  Total tokens   : {est['total_tokens']:,}")
    print(f"  Input cost     : ${est['input_cost']:.6f}")
    print(f"  Output cost    : ${est['output_cost']:.6f}")
    print(f"  Total cost     : ${est['total_cost']:.6f}")
    print(f"{line}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Response formatting
# ─────────────────────────────────────────────────────────────────────────────

def format_response(
    response,
    title: str = "LLM Response",
    width: int = 72,
    show_stats: bool = True,
) -> str:
    """
    Pretty-print an LLMResponse object to the terminal.

    Args:
        response:   An LLMResponse from LLMClient.chat().
        title:      Box header label.
        width:      Terminal wrap width.
        show_stats: Whether to include token/cost stats below the response.

    Returns:
        The formatted string (also prints it).
    """
    from .llm_client import LLMResponse  # local import to avoid circular

    border = "═" * width
    thin   = "─" * width

    lines = [
        f"\n{border}",
        f"  {title}",
        border,
        "",
    ]

    # Word-wrap the content for readability
    for paragraph in response.content.split("\n"):
        if paragraph.strip():
            wrapped = textwrap.fill(paragraph, width=width - 2)
            lines.append(wrapped)
        else:
            lines.append("")

    if show_stats:
        lines += [
            "",
            thin,
            f"  Model: {response.model}  |  "
            f"Tokens: {response.total_tokens:,} "
            f"({response.prompt_tokens:,} in / {response.completion_tokens:,} out)  |  "
            f"Cost: ${response.cost_usd:.6f}  |  "
            f"Latency: {response.latency_ms:.0f}ms",
        ]

    lines.append(border + "\n")

    output = "\n".join(lines)
    print(output)
    return output


def truncate(text: str, max_chars: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_chars, appending suffix if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)] + suffix


def print_prompt_box(
    prompt: str,
    title: str = "Prompt",
    width: int = 72,
) -> None:
    """Print a prompt inside a formatted box for easy reading."""
    border = "┌" + "─" * (width - 2) + "┐"
    bottom = "└" + "─" * (width - 2) + "┘"
    title_line = f"│  {title}" + " " * (width - 4 - len(title)) + "│"

    print(border)
    print(title_line)
    print("│" + "─" * (width - 2) + "│")
    for line in prompt.split("\n"):
        # Wrap long lines
        for chunk in textwrap.wrap(line, width=width - 4) or [""]:
            padded = f"│  {chunk}" + " " * (width - 4 - len(chunk)) + "│"
            print(padded)
    print(bottom)


# ─────────────────────────────────────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample_text = (
        "Prompt engineering is the practice of crafting inputs to large "
        "language models to elicit the most useful, accurate, and relevant "
        "outputs. It combines elements of linguistics, UX design, and "
        "machine learning intuition."
    )

    tokens = count_tokens(sample_text)
    print(f"Sample text token count: {tokens}")

    print_cost_estimate(
        sample_text,
        model="gpt-4o-mini",
        expected_output_tokens=150,
        label="Sample Prompt",
    )

    print_prompt_box(sample_text, title="Sample Prompt Preview")
    print("\n✅ helpers.py working correctly.")
