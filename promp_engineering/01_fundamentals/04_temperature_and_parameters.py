"""
01_fundamentals/04_temperature_and_parameters.py
═══════════════════════════════════════════════════════════════════

WHAT:   Explore the key parameters that control LLM generation behavior:
        temperature, top_p, max_tokens, frequency_penalty, presence_penalty.

WHY:    The same prompt with different parameters produces very different
        outputs. Understanding these knobs is essential for tuning quality,
        creativity, and consistency.

PARAMETER REFERENCE:
        ┌─────────────────────┬────────────────────────────────────────────┐
        │ Parameter           │ Effect                                     │
        ├─────────────────────┼────────────────────────────────────────────┤
        │ temperature         │ 0=deterministic, 1=balanced, 2=chaotic     │
        │ top_p               │ Nucleus sampling — use instead of temp     │
        │ max_tokens          │ Hard cap on response length                │
        │ frequency_penalty   │ Penalizes token repetition based on count  │
        │ presence_penalty    │ Penalizes any already-used token           │
        └─────────────────────┴────────────────────────────────────────────┘

WHEN TO USE WHICH TEMPERATURE:
        0.0 – 0.2  : Factual tasks (classification, extraction, code)
        0.3 – 0.6  : Summarization, Q&A, translation
        0.7 – 1.0  : Creative writing, brainstorming, chatbots
        1.1 – 2.0  : Experimental, highly creative (expect incoherence)

COMMON PITFALLS:
        - Setting temperature=0 for creative tasks → boring, repetitive
        - Setting temperature=1.5 for factual tasks → hallucinations
        - Using both temperature and top_p simultaneously (pick one)
        - Setting max_tokens too low → truncated responses
"""

import sys
import os
import argparse
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, print_cost_estimate


# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 1 — Temperature spectrum on a creative task
# ─────────────────────────────────────────────────────────────────────────────

def experiment_temperature(client: LLMClient, temperatures: list[float]) -> None:
    """
    Run the same creative prompt at multiple temperatures and compare outputs.
    
    Task: Write a product tagline for a cybersecurity startup.
    """
    prompt = (
        "Write ONE punchy product tagline (≤ 10 words) for a cybersecurity "
        "startup called 'VaultGuard' that protects small businesses from ransomware. "
        "Output only the tagline, no explanation."
    )

    print("\n" + "═" * 72)
    print("  EXPERIMENT 1: Temperature Effect on Creative Task")
    print("  Prompt: VaultGuard cybersecurity tagline")
    print("═" * 72)

    for temp in temperatures:
        # Create a client instance with the specific temperature
        temp_client = LLMClient(dry_run=client.dry_run, temperature=temp)

        print(f"\n  🌡  temperature = {temp}")
        response = temp_client.chat(user_message=prompt, max_tokens=30)

        if client.dry_run:
            break  # Only one iteration needed in dry-run mode

        print(f"  → {response.content.strip()}")
        print(f"     ({response.total_tokens} tokens, ${response.cost_usd:.6f})")
        time.sleep(0.5)  # Rate limit courtesy pause


# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 2 — Temperature on a factual task (should stay low)
# ─────────────────────────────────────────────────────────────────────────────

def experiment_temperature_factual(client: LLMClient) -> None:
    """
    Demonstrate why temperature should be low for factual/deterministic tasks.
    
    Task: Extract a dollar amount from a sentence.
    """
    prompt = (
        "Extract the total invoice amount from the following sentence. "
        "Reply with ONLY the numeric value, no symbols.\n\n"
        "Sentence: 'The final invoice for Q3 services totals $14,782.50 including tax.'"
    )

    print("\n" + "═" * 72)
    print("  EXPERIMENT 2: Temperature on a Factual Extraction Task")
    print("  Rule: Use low temperature (0–0.2) for factual tasks")
    print("═" * 72)

    for temp in [0.0, 0.7, 1.5]:
        temp_client = LLMClient(dry_run=client.dry_run, temperature=temp)
        print(f"\n  🌡  temperature = {temp}")
        response = temp_client.chat(user_message=prompt, max_tokens=20)

        if client.dry_run:
            break

        correctness = "✅ Correct" if "14782.50" in response.content or "14,782.50" in response.content else "⚠️  Unexpected"
        print(f"  → {response.content.strip()}  {correctness}")
        time.sleep(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 3 — max_tokens truncation awareness
# ─────────────────────────────────────────────────────────────────────────────

def experiment_max_tokens(client: LLMClient) -> None:
    """
    Show how max_tokens affects response completeness.
    
    Rule: Always estimate output length and set max_tokens 20% above that.
    """
    prompt = (
        "List the top 10 Python best practices for writing production-grade code. "
        "Number each one and give a one-sentence explanation."
    )

    print("\n" + "═" * 72)
    print("  EXPERIMENT 3: max_tokens Effect on Completeness")
    print("═" * 72)

    for max_tok, label in [(50, "Too low — forces truncation"),
                            (300, "Appropriate — likely complete"),
                            (1000, "Generous — definite complete")]:

        tok_client = LLMClient(dry_run=client.dry_run, temperature=0.3)
        print(f"\n  📏 max_tokens = {max_tok}  ({label})")

        response = tok_client.chat(user_message=prompt, max_tokens=max_tok)

        if client.dry_run:
            break

        # Check if the response appears truncated (simple heuristic)
        content = response.content.strip()
        truncated = not content.endswith((".", "!", "?", '"', "'"))
        status = "⚠️  TRUNCATED" if truncated else "✅ Complete"
        preview = content[:120] + "..." if len(content) > 120 else content
        print(f"  Status: {status}")
        print(f"  Preview: {preview}")
        print(f"  Output tokens used: {response.completion_tokens}/{max_tok}")
        time.sleep(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 4 — frequency_penalty and presence_penalty
# ─────────────────────────────────────────────────────────────────────────────

def experiment_penalties(client: LLMClient) -> None:
    """
    Demonstrate frequency_penalty and presence_penalty effects.
    
    Use case: Generating marketing copy — avoiding repetitive phrases.
    """
    prompt = (
        "Write a 4-sentence product description for 'Lumina', a smart home "
        "lighting system. Emphasize ease of use, automation, and energy savings."
    )

    print("\n" + "═" * 72)
    print("  EXPERIMENT 4: Repetition Penalties")
    print("  Task: Marketing copy for a smart lighting product")
    print("═" * 72)

    configs = [
        {"frequency_penalty": 0.0, "presence_penalty": 0.0,  "label": "No penalties (may repeat)"},
        {"frequency_penalty": 0.8, "presence_penalty": 0.0,  "label": "frequency_penalty=0.8 (discourages repeated words)"},
        {"frequency_penalty": 0.0, "presence_penalty": 0.8,  "label": "presence_penalty=0.8 (discourages any reuse)"},
    ]

    for cfg in configs:
        print(f"\n  ⚙️  {cfg['label']}")

        if not client.dry_run:
            from openai import OpenAI
            import dotenv
            dotenv.load_dotenv()

            oa = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            resp = oa.chat.completions.create(
                model=client.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
                frequency_penalty=cfg["frequency_penalty"],
                presence_penalty=cfg["presence_penalty"],
            )
            content = resp.choices[0].message.content
            print(f"  {content}")
            time.sleep(0.5)
        else:
            print(f"  [DRY RUN — would call API with freq_pen={cfg['frequency_penalty']}, "
                  f"pres_pen={cfg['presence_penalty']}]")


# ─────────────────────────────────────────────────────────────────────────────
# Parameter Quick-Reference
# ─────────────────────────────────────────────────────────────────────────────

def print_parameter_reference() -> None:
    """Print a quick-reference guide for all key parameters."""
    print("\n" + "═" * 72)
    print("  PARAMETER QUICK REFERENCE")
    print("═" * 72)

    params = [
        {
            "name": "temperature",
            "range": "0.0 – 2.0",
            "default": "1.0",
            "effect": "Controls randomness in token selection",
            "recommended": {
                "Code/extraction/classification": "0.0 – 0.2",
                "Summarization / Q&A":            "0.3 – 0.6",
                "Creative writing / chat":        "0.7 – 1.0",
            },
        },
        {
            "name": "top_p",
            "range": "0.0 – 1.0",
            "default": "1.0",
            "effect": "Nucleus sampling — only sample from top P% probability mass",
            "recommended": {
                "Factual tasks":  "0.1 – 0.5",
                "Balanced":       "0.7 – 0.9",
                "Creative tasks": "0.95 – 1.0",
            },
        },
        {
            "name": "max_tokens",
            "range": "1 – model limit",
            "default": "inf (model decides)",
            "effect": "Hard cap on response length. Response may be truncated.",
            "recommended": {
                "Short answers":     "50 – 150",
                "Paragraphs":        "200 – 500",
                "Long-form content": "500 – 2000",
            },
        },
        {
            "name": "frequency_penalty",
            "range": "-2.0 – 2.0",
            "default": "0.0",
            "effect": "Penalizes tokens proportionally to how often they've appeared",
            "recommended": {
                "Normal prose":    "0.0",
                "Reduce repetition": "0.3 – 0.8",
            },
        },
        {
            "name": "presence_penalty",
            "range": "-2.0 – 2.0",
            "default": "0.0",
            "effect": "Flat penalty for any token that has appeared at all",
            "recommended": {
                "Normal":        "0.0",
                "Maximum variety": "0.5 – 1.0",
            },
        },
    ]

    for p in params:
        print(f"\n  📌 {p['name']}")
        print(f"     Range:   {p['range']}   Default: {p['default']}")
        print(f"     Effect:  {p['effect']}")
        print(f"     When to set:")
        for context, value in p["recommended"].items():
            print(f"       • {context:<35} → {value}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Temperature & parameters experiments")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview prompts without API calls")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print_parameter_reference()

    # Temperature experiments
    experiment_temperature(client, temperatures=[0.0, 0.3, 0.7, 1.0, 1.5])
    experiment_temperature_factual(client)

    # Token limit experiment
    experiment_max_tokens(client)

    # Penalty experiment
    experiment_penalties(client)

    print("\n✅ Parameter experiments complete.")
    print(
        "   Rule of thumb: temperature=0.2 for code/facts, 0.7 for creativity.\n"
    )


if __name__ == "__main__":
    main()
