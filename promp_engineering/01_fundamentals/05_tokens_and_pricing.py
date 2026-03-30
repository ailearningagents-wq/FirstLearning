"""
01_fundamentals/05_tokens_and_pricing.py
═══════════════════════════════════════════════════════════════════

WHAT:   Understand what tokens are, how to count them, and how to build
        cost awareness into every LLM workflow.

WHY:    LLM APIs charge by the token. A prompt that sends 5,000 tokens
        costs 33x more than one that sends 150. Ignoring token economics
        is the fastest way to rack up unexpected bills in production.

KEY FACTS:
        • 1 token ≈ 4 characters ≈ 0.75 words (English text)
        • Models have context windows (8K / 32K / 128K tokens)
        • You pay for BOTH input tokens and output tokens
        • Structured data (JSON) and code are more token-dense than prose
        • Whitespace, newlines, and special characters cost tokens too

WHEN TO OPTIMIZE:
        - High-volume production pipelines (millions of calls/day)
        - Long documents that need to fit in context windows
        - Budget-constrained projects or MVPs

COMMON PITFALLS:
        - Not knowing your model's context window limit
        - Stuffing too much context → model ignores far end (lost-in-middle)
        - Assuming code is "free" — a 500-line Python file can be 3,000+ tokens
        - Forgetting that system prompts also count toward token usage
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    count_tokens,
    count_messages_tokens,
    estimate_cost,
    print_cost_estimate,
    print_prompt_box,
)


# ─────────────────────────────────────────────────────────────────────────────
# MODEL CONTEXT WINDOWS & PRICING (as of 2024)
# ─────────────────────────────────────────────────────────────────────────────

MODEL_INFO = {
    "gpt-4o-mini": {
        "context_window": 128_000,
        "input_cost_per_1k":  0.000150,
        "output_cost_per_1k": 0.000600,
        "notes": "Best value for most tasks. Default for this course.",
    },
    "gpt-4o": {
        "context_window": 128_000,
        "input_cost_per_1k":  0.005,
        "output_cost_per_1k": 0.015,
        "notes": "Highest capability. 33x more expensive than gpt-4o-mini.",
    },
    "gpt-3.5-turbo": {
        "context_window": 16_385,
        "input_cost_per_1k":  0.0005,
        "output_cost_per_1k": 0.0015,
        "notes": "Legacy model. gpt-4o-mini is better at similar cost.",
    },
    "claude-3-haiku": {
        "context_window": 200_000,
        "input_cost_per_1k":  0.00025,
        "output_cost_per_1k": 0.00125,
        "notes": "Anthropic's fastest/cheapest. Excellent for high-volume.",
    },
    "claude-3-sonnet": {
        "context_window": 200_000,
        "input_cost_per_1k":  0.003,
        "output_cost_per_1k": 0.015,
        "notes": "Anthropic's balanced option.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# DEMO 1 — Tokenization visualization
# ─────────────────────────────────────────────────────────────────────────────

def demo_tokenization() -> None:
    """Show how different types of text tokenize differently."""

    samples = {
        "Short English sentence":
            "The quick brown fox jumps over the lazy dog.",
        "Technical jargon":
            "Transformer-based LLMs use self-attention mechanisms with multi-head "
            "weight matrices for contextual embedding generation.",
        "Python code snippet":
            "def calculate_roi(revenue: float, cost: float) -> float:\n"
            "    return ((revenue - cost) / cost) * 100",
        "JSON structure":
            '{"user_id": "USR-82847", "sentiment": "ANGRY", "category": "BILLING", '
            '"urgency": "CRITICAL", "requires_human": true}',
        "Repeated whitespace (waste)":
            "Please     summarize   the   following   document:    \n\n\n\n",
        "Same without waste":
            "Summarize the following document:",
        "Legal / formal language":
            "Notwithstanding any provision herein to the contrary, the indemnifying "
            "party shall defend, indemnify, and hold harmless the indemnified party "
            "from and against any and all claims.",
        "Non-English (Spanish)":
            "La ingeniería de prompts es la práctica de diseñar entradas para "
            "modelos de lenguaje grandes para obtener resultados de alta calidad.",
    }

    print("\n" + "═" * 72)
    print("  DEMO 1: Token Counts for Different Text Types")
    print("  (Using tiktoken — same tokenizer as OpenAI API)")
    print("═" * 72)
    print(f"\n  {'Text Type':<40} {'Chars':>6}  {'Tokens':>6}  {'Chars/Token':>11}")
    print("  " + "─" * 68)

    for label, text in samples.items():
        chars = len(text)
        tokens = count_tokens(text)
        ratio = chars / tokens if tokens > 0 else 0
        print(f"  {label:<40} {chars:>6}  {tokens:>6}  {ratio:>10.1f}x")

    print("\n  💡 Key insights:")
    print("     • English prose: ~4 chars/token (1 token ≈ 0.75 words)")
    print("     • Code/JSON: ~3.5 chars/token (more tokens per character!)")
    print("     • Unnecessary whitespace burns tokens — clean your prompts")
    print("     • Non-ASCII languages: fewer chars per token")


# ─────────────────────────────────────────────────────────────────────────────
# DEMO 2 — Context window capacity visualizer
# ─────────────────────────────────────────────────────────────────────────────

def demo_context_window() -> None:
    """Visualize how different content types fill up context windows."""

    # Rough token estimates for real-world content
    content_types = {
        "System prompt (typical)":           250,
        "Short user query":                  20,
        "Full product requirements doc":     3_000,
        "10-page legal contract":            8_000,
        "100-page manual":                   80_000,
        "One chapter of a book (~50 pages)": 40_000,
        "Average email thread (20 emails)":  2_000,
        "1,000-line Python codebase":        8_000,
        "GPT-4o context window":             128_000,
    }

    print("\n" + "═" * 72)
    print("  DEMO 2: Context Window Sizes in Perspective")
    print("═" * 72)
    print(f"\n  {'Content Type':<45} {'~Tokens':>10}")
    print("  " + "─" * 58)

    context_window = 128_000
    for label, tokens in content_types.items():
        bar_width = int((tokens / context_window) * 30)
        bar = "█" * bar_width + "░" * (30 - bar_width)
        pct = (tokens / context_window) * 100
        print(f"  {label:<45} {tokens:>10,}  {pct:>5.1f}%")

    print("\n  💡 The 'lost in the middle' problem:")
    print("     Research shows models attend to the START and END of context")
    print("     most strongly. Important info buried in the middle gets 'lost'.")
    print("     → Put critical instructions at the start and end of long prompts.")


# ─────────────────────────────────────────────────────────────────────────────
# DEMO 3 — Real cost calculator for production scenarios
# ─────────────────────────────────────────────────────────────────────────────

def demo_production_cost_calculator() -> None:
    """
    Calculate monthly costs for realistic production scenarios.
    
    Scenario: A SaaS platform that auto-summarizes user-submitted articles.
    """

    scenarios = [
        {
            "name": "Email Auto-Classifier (startup MVP)",
            "calls_per_day": 500,
            "avg_input_tokens": 300,   # Short email
            "avg_output_tokens": 50,   # Classification JSON
        },
        {
            "name": "Document Summarizer (mid-size company)",
            "calls_per_day": 2_000,
            "avg_input_tokens": 2_000,  # 2-page document
            "avg_output_tokens": 300,
        },
        {
            "name": "Customer Support Chatbot (enterprise)",
            "calls_per_day": 50_000,
            "avg_input_tokens": 800,    # Conversation history + query
            "avg_output_tokens": 200,
        },
        {
            "name": "Code Review Tool (developer tool)",
            "calls_per_day": 10_000,
            "avg_input_tokens": 1_500,  # Code snippet
            "avg_output_tokens": 400,
        },
    ]

    models_to_compare = ["gpt-4o-mini", "gpt-4o", "claude-3-haiku"]

    print("\n" + "═" * 72)
    print("  DEMO 3: Monthly Production Cost Calculator")
    print("═" * 72)

    for scenario in scenarios:
        print(f"\n  📊 Scenario: {scenario['name']}")
        print(f"     {scenario['calls_per_day']:,} calls/day  |  "
              f"~{scenario['avg_input_tokens']} input tokens  |  "
              f"~{scenario['avg_output_tokens']} output tokens")
        print(f"     {'Model':<20} {'Daily Cost':>12} {'Monthly Cost':>14} {'Annual Cost':>13}")
        print("     " + "─" * 62)

        for model in models_to_compare:
            if model not in MODEL_INFO:
                continue
            pricing = MODEL_INFO[model]
            daily_cost = scenario["calls_per_day"] * (
                (scenario["avg_input_tokens"] / 1000) * pricing["input_cost_per_1k"]
                + (scenario["avg_output_tokens"] / 1000) * pricing["output_cost_per_1k"]
            )
            monthly = daily_cost * 30
            annual  = daily_cost * 365
            print(f"     {model:<20} ${daily_cost:>10.2f} ${monthly:>12.2f} ${annual:>11.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# DEMO 4 — Token optimization strategies
# ─────────────────────────────────────────────────────────────────────────────

def demo_token_optimization() -> None:
    """
    Show concrete techniques to reduce token usage without losing quality.
    """

    print("\n" + "═" * 72)
    print("  DEMO 4: Token Optimization Strategies")
    print("═" * 72)

    strategies = [
        {
            "name": "Remove verbose framing",
            "before": (
                "I would like you to please take a look at the following text "
                "that I am going to provide to you and could you please summarize "
                "it for me in a concise manner? Thank you very much.\n\n"
                "Text: The Federal Reserve raised interest rates by 25 basis points."
            ),
            "after": (
                "Summarize in one sentence:\n\n"
                "The Federal Reserve raised interest rates by 25 basis points."
            ),
        },
        {
            "name": "Use structured delimiters instead of repetition",
            "before": (
                "User name: John Smith\nUser age: 34\nUser email: john@example.com\n"
                "User subscription: Premium\nUser joined: 2022-01-15\n"
                "User last login: 2024-03-10\nUser total purchases: 47"
            ),
            "after": (
                "User: John Smith, 34, john@example.com, Premium, "
                "joined 2022-01-15, last login 2024-03-10, 47 purchases"
            ),
        },
        {
            "name": "Abbreviate system prompts for high-volume tasks",
            "before": (
                "You are an expert customer service representative working for "
                "Acme Corporation, a leading provider of cloud-based SaaS solutions. "
                "Your role is to assist customers with their inquiries in a "
                "professional, helpful, and empathetic manner. Always maintain..."
                "(300 more words)"
            ),
            "after": (
                "You are Acme Corp support. Be professional, helpful, empathetic. "
                "Resolve billing/tech issues. Escalate if unsure."
            ),
        },
        {
            "name": "Request shorter output explicitly",
            "before": "Explain what machine learning is.",
            "after": "Explain machine learning in exactly 2 sentences.",
        },
    ]

    total_saved = 0
    for s in strategies:
        before_tokens = count_tokens(s["before"])
        after_tokens  = count_tokens(s["after"])
        saved = before_tokens - after_tokens
        pct   = (saved / before_tokens * 100) if before_tokens > 0 else 0
        total_saved += saved

        print(f"\n  ✂️  Strategy: {s['name']}")
        print(f"     Before: {before_tokens} tokens")
        print(f"     After:  {after_tokens} tokens")
        print(f"     Saved:  {saved} tokens ({pct:.0f}% reduction)")

    print(f"\n  Total tokens saved across all strategies: {total_saved}")
    daily_savings_usd = (total_saved / 1000) * 0.000150 * 10_000  # 10K calls/day
    print(f"  At 10,000 calls/day with gpt-4o-mini: ${daily_savings_usd:.2f}/day savings")


# ─────────────────────────────────────────────────────────────────────────────
# Model comparison table
# ─────────────────────────────────────────────────────────────────────────────

def print_model_comparison() -> None:
    """Print a comprehensive model comparison table."""

    print("\n" + "═" * 72)
    print("  MODEL COMPARISON TABLE (2024)")
    print("═" * 72)
    print(f"\n  {'Model':<20} {'Context':>10} {'Input $/1K':>12} {'Output $/1K':>13} {'Best For'}")
    print("  " + "─" * 70)

    for model, info in MODEL_INFO.items():
        print(
            f"  {model:<20} "
            f"{info['context_window']:>10,} "
            f"${info['input_cost_per_1k']:>10.6f} "
            f"${info['output_cost_per_1k']:>11.6f}  "
            f"{info['notes']}"
        )

    print("\n  💡 Rule of thumb: Start with gpt-4o-mini. Only upgrade to gpt-4o")
    print("     if you can measure and prove the quality improvement justifies the cost.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Tokens and pricing demonstrations")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("\n" + "═" * 72)
    print("  MODULE 01 — Tokens and Pricing")
    print("═" * 72)

    demo_tokenization()
    demo_context_window()
    print_model_comparison()
    demo_production_cost_calculator()
    demo_token_optimization()

    print("\n" + "═" * 72)
    print("  MODULE 01 COMPLETE ✅")
    print("  Next: Module 02 — Basic Prompting Techniques")
    print("═" * 72 + "\n")


if __name__ == "__main__":
    main()
