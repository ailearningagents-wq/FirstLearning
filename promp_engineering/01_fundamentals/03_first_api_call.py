"""
01_fundamentals/03_first_api_call.py
═══════════════════════════════════════════════════════════════════

WHAT:   Your first real API call to OpenAI using our LLMClient wrapper.
        Three progressively richer examples: classify, summarize, generate code.

WHY:    Seeing the API work end-to-end, with real input/output and cost
        tracking, is the fastest way to build the right mental model for
        everything that follows.

WHEN TO USE:
        Use as a template for any new prompt — copy this file and swap in
        your task.

COMMON PITFALLS:
        - Not loading the .env file → "Invalid API key" error
        - Forgetting max_tokens → model truncates or runs long
        - Not checking response.content before using it

USAGE:
        python 03_first_api_call.py                    # runs all examples
        python 03_first_api_call.py --dry-run          # prints prompts only
        python 03_first_api_call.py --task classify    # run one example
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, print_cost_estimate, print_prompt_box


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1 — Classification (customer support ticket)
# ─────────────────────────────────────────────────────────────────────────────

def example_classify(client: LLMClient) -> None:
    """Classify a customer support ticket by category and urgency."""

    ticket = """
    Subject: My subscription was charged twice this month!
    
    Hi, I noticed that my credit card was billed $49.99 on March 1st and 
    again on March 3rd. I only have one account. This has caused my card 
    to be declined elsewhere. I need a refund IMMEDIATELY. My account ID 
    is USR-82847. Order numbers: ORD-11221 and ORD-11398.
    
    - James Murphy
    """

    system = (
        "You are a customer support triage agent. "
        "Classify incoming tickets to route them to the right team."
    )

    user = f"""Classify the following customer support ticket.

Return a JSON object with these exact keys:
- "category": one of [BILLING, TECHNICAL, ACCOUNT, SHIPPING, OTHER]
- "urgency": one of [CRITICAL, HIGH, MEDIUM, LOW]
- "sentiment": one of [ANGRY, FRUSTRATED, NEUTRAL, HAPPY]
- "requires_human": true or false
- "summary": one sentence describing the issue
- "suggested_team": which internal team should handle this

Customer ticket:
```
{ticket.strip()}
```"""

    print("\n" + "═" * 72)
    print("  EXAMPLE 1: Customer Support Ticket Classification")
    print("═" * 72)

    # Show cost estimate before calling
    print_cost_estimate([
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ], label="Ticket Classification")

    # Make the API call
    response = client.chat(user_message=user, system_message=system, max_tokens=300)

    # Display result
    format_response(response, title="Ticket Classification Result")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2 — Summarization (financial news article)
# ─────────────────────────────────────────────────────────────────────────────

def example_summarize(client: LLMClient) -> None:
    """Summarize a financial news article for a busy executive."""

    article = """
    Federal Reserve Raises Interest Rates by 25 Basis Points
    
    The Federal Open Market Committee (FOMC) voted unanimously yesterday to 
    raise the federal funds rate target range to 5.25%-5.50%, the highest 
    level in 22 years. The decision comes amid persistent inflation that, 
    while lower than its June 2022 peak of 9.1%, remains above the Fed's 
    2% annual target at 3.2%.
    
    Fed Chair Jerome Powell signaled in his post-meeting press conference 
    that further tightening remains possible but that the committee would 
    approach future decisions "meeting by meeting." Markets reacted with 
    mixed signals: the S&P 500 fell 0.4% while the 10-year Treasury yield 
    rose to 4.21%, a 16-year high.
    
    Economists are divided on the impact. Morgan Stanley's chief economist 
    Ellen Zentner projects one more 25 bps hike before a pause, while 
    Goldman Sachs maintains its forecast of no further increases. Both firms 
    agree that rate cuts are unlikely before Q2 2024.
    
    The housing market has been the most immediately affected sector, with 
    the average 30-year fixed mortgage rate reaching 7.48%, causing existing 
    home sales to fall to their lowest level since 2010.
    """

    user = f"""Summarize the following financial news article for a C-suite executive 
who has 30 seconds to read it.

Requirements:
- Maximum 3 bullet points
- Each bullet: ≤ 20 words
- Start each bullet with: MARKET IMPACT, POLICY SIGNAL, or OUTLOOK
- Avoid jargon; assume reader knows finance basics

Article:
```
{article.strip()}
```"""

    print("\n" + "═" * 72)
    print("  EXAMPLE 2: Financial News Article → Executive Summary")
    print("═" * 72)

    print_cost_estimate(user, label="Article Summarization")
    response = client.chat(user_message=user, max_tokens=200)
    format_response(response, title="Executive Summary")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3 — Code Generation (from requirements → Python function)
# ─────────────────────────────────────────────────────────────────────────────

def example_code_generation(client: LLMClient) -> None:
    """Generate a production-ready Python function from a specification."""

    specification = """
    Function: parse_invoice_total
    
    Business requirement:
    We receive invoices from vendors as plain text. Extract the total amount 
    due and return it as a float. Amounts can appear as:
    - "Total: $1,234.56"
    - "Amount Due: USD 890.00"
    - "TOTAL DUE: 5,000"
    - "Total Amount: €2,400.50"
    
    Requirements:
    - Python 3.11, type hints, Google-style docstring
    - Return float (the numeric value, strip currency symbols/commas)
    - Return None if no total found
    - Handle edge cases: empty string, multiple matches (return first), 
      non-numeric values
    - Include 5 pytest test cases covering happy path and edge cases
    """

    user = f"""Generate a production-ready Python function based on the specification below.

Output ONLY the Python code (no explanations outside the docstring).
Include the function and the pytest tests in a single code block.

Specification:
```
{specification.strip()}
```"""

    print("\n" + "═" * 72)
    print("  EXAMPLE 3: Requirements → Production Python Function")
    print("═" * 72)

    print_cost_estimate(user, label="Code Generation", expected_output_tokens=500)
    response = client.chat(user_message=user, max_tokens=700)
    format_response(response, title="Generated Python Function + Tests")


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="First API Call examples — Prompt Engineering Module 01"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling the API (no cost incurred)",
    )
    parser.add_argument(
        "--task",
        choices=["classify", "summarize", "code", "all"],
        default="all",
        help="Which example to run (default: all)",
    )
    args = parser.parse_args()

    # Initialize the LLM client (dry_run=True overrides .env DRY_RUN setting)
    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 01 — First API Call")
    print(f"  Provider : {client.provider}")
    print(f"  Model    : {client.model}")
    print(f"  Dry Run  : {client.dry_run}")
    print("═" * 72)

    # Run selected examples
    if args.task in ("classify", "all"):
        example_classify(client)

    if args.task in ("summarize", "all"):
        example_summarize(client)

    if args.task in ("code", "all"):
        example_code_generation(client)

    print("\n✅ All examples complete.")
    print("   Next: Run 04_temperature_and_parameters.py to explore model parameters.\n")


if __name__ == "__main__":
    main()
