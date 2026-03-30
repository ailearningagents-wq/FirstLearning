"""
03_intermediate_techniques/01_chain_of_thought.py
═══════════════════════════════════════════════════════════════════

WHAT:   Chain-of-Thought (CoT) prompting encourages the model to reason
        through a problem step-by-step before giving the final answer.
        This dramatically improves accuracy on tasks requiring arithmetic,
        logic, multi-step reasoning, and causal analysis.

WHY:    LLMs predict tokens sequentially. When forced to "think out loud",
        each reasoning step becomes context for the next, reducing errors
        that occur when jumping directly to conclusions.

TWO FLAVORS:
        1. Zero-Shot CoT: Add "Let's think step by step." — works surprisingly well
        2. Few-Shot CoT:  Provide examples WITH reasoning traces — even better

WHEN TO USE:
        ✓ Math / arithmetic problems
        ✓ Multi-step logic or reasoning
        ✓ Causal analysis ("Why did X happen?")
        ✓ Code debugging / root cause analysis
        ✓ Complex decision-making with tradeoffs
        ✗ Simple classification or extraction (CoT adds tokens without benefit)
        ✗ Tasks where speed matters more than accuracy

COMMON PITFALLS:
        - Correct reasoning leading to wrong answer (verify the arithmetic!)
        - CoT makes the model verbose — use it only when accuracy matters
        - Model may "short-circuit" reasoning and jump to conclusion
        - Reasoning steps may be plausible-sounding but factually wrong (hallucination)
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, count_tokens


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1 — Business Math Word Problem
# ─────────────────────────────────────────────────────────────────────────────

BUSINESS_PROBLEM = """
A SaaS company has 1,200 customers. In Q3:
- 180 customers churned (cancelled)
- 220 new customers signed up
- 45 customers upgraded from Basic ($99/mo) to Pro ($299/mo)
- 30 customers downgraded from Pro to Basic

At the start of Q3:
- 800 customers were on Basic ($99/mo)
- 400 customers were on Pro ($299/mo)

What is the Monthly Recurring Revenue (MRR) at the END of Q3?
"""


def example_business_math(client: LLMClient) -> None:
    """Demonstrate zero-shot CoT vs direct answer on a business math problem."""

    system = "You are a financial analyst specializing in SaaS metrics."

    # ❌ Direct answer (no reasoning)
    direct_prompt = f"Calculate the MRR at the end of Q3.\n\n{BUSINESS_PROBLEM}"

    # ✅ Zero-Shot CoT (just add "Let's think step by step.")
    zero_shot_cot = f"""{BUSINESS_PROBLEM}

Let's think through this step by step, tracking each customer segment."""

    # ✅✅ Few-Shot CoT (provide a worked example first)
    few_shot_cot = f"""Solve SaaS MRR calculation problems by breaking them into steps.

EXAMPLE:
Problem: A company has 500 Basic ($50/mo) customers and 200 Pro ($150/mo) customers.
In Q2: 50 Basic churned, 30 Pro churned, 80 new Basic signed up, 
10 Basic upgraded to Pro.

Solution:
Step 1: Track Basic customer changes
  Starting Basic: 500
  - Churned: -50
  - New Basic: +80
  - Upgraded to Pro: -10
  Ending Basic: 500 - 50 + 80 - 10 = 520

Step 2: Track Pro customer changes
  Starting Pro: 200
  - Churned: -30
  - Upgrades from Basic: +10
  Ending Pro: 200 - 30 + 10 = 180

Step 3: Calculate end-of-quarter MRR
  Basic MRR: 520 × $50 = $26,000
  Pro MRR: 180 × $150 = $27,000
  Total MRR = $26,000 + $27,000 = $53,000

---

Now solve this problem using the same step-by-step approach:
{BUSINESS_PROBLEM}

Solution:"""

    print("\n" + "═" * 72)
    print("  EXAMPLE 1: SaaS MRR Calculation (Business Math)")
    print("═" * 72)

    for label, prompt in [("❌ Direct (no reasoning)", direct_prompt),
                           ("✅ Zero-Shot CoT", zero_shot_cot),
                           ("✅✅ Few-Shot CoT", few_shot_cot)]:
        print(f"\n  {label} ({count_tokens(prompt)} tokens):")

        if not client.dry_run:
            response = client.chat(
                user_message=prompt,
                system_message=system,
                temperature=0.0,
                max_tokens=500 if "Few-Shot" in label else 300,
            )
            # Show response
            lines = response.content.strip().split("\n")
            for line in lines:
                print(f"  {line}")
            print(f"\n  [Tokens: {response.total_tokens}, Cost: ${response.cost_usd:.6f}]")
        else:
            print(f"  [DRY RUN]")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2 — Logic Puzzle (requires systematic reasoning)
# ─────────────────────────────────────────────────────────────────────────────

LOGIC_PUZZLE = """
Five software engineers — Alice, Bob, Carol, Dave, and Eve — are being 
considered for promotion. They have these characteristics:

- Alice has been at the company longer than Bob.
- Carol joined after Dave but before Eve.
- Bob joined the company 3 years ago.
- The person who joined earliest has the most seniority.
- Dave is not the most senior.
- Alice joined 5 years ago.
- Eve is more senior than Bob.

If exactly 2 engineers are eligible for the "5+ year tenure bonus", 
who are they?
"""


def example_logic_puzzle(client: LLMClient) -> None:
    """Show how CoT makes logic puzzles tractable."""

    system = "You solve logic puzzles systematically, one deduction at a time."

    direct = f"Answer this logic puzzle:\n{LOGIC_PUZZLE}"

    cot = f"""Solve this logic puzzle step by step.
First, establish facts from each clue. Then build a timeline. Finally answer.

{LOGIC_PUZZLE}

Step-by-step solution:"""

    structured_cot = f"""Solve this logic puzzle using the structured approach below.

APPROACH:
1. List all explicit facts as bullet points
2. Build a timeline from earliest to most recent joiner
3. Derive the seniority order
4. Answer the specific question with justification

{LOGIC_PUZZLE}

1. Explicit facts:"""

    print("\n" + "═" * 72)
    print("  EXAMPLE 2: Logic Puzzle with Chain-of-Thought")
    print("═" * 72)

    for label, prompt in [("Direct answer", direct),
                           ("Zero-shot CoT", cot),
                           ("Structured CoT", structured_cot)]:
        print(f"\n  {label}:")

        if not client.dry_run:
            response = client.chat(
                user_message=prompt,
                system_message=system,
                temperature=0.0,
                max_tokens=400,
            )
            for line in response.content.strip().split("\n")[:15]:
                print(f"  {line}")
            if response.completion_tokens > 400:
                print(f"  ... [truncated, {response.completion_tokens} tokens]")
        else:
            print(f"  [DRY RUN — prompt: {count_tokens(prompt)} tokens]")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3 — Root Cause Analysis (production incident debugging)
# ─────────────────────────────────────────────────────────────────────────────

INCIDENT_SYMPTOMS = """
Production incident symptoms observed on March 14, 2024:
- 14:23 UTC: API response times spike from 50ms to 8,000ms
- 14:24 UTC: Error rate rises from 0.1% to 34% (HTTP 503 errors)
- 14:24 UTC: CPU on web servers: 15% (normal). Memory: 12% (normal)
- 14:25 UTC: Redis connection count: 10,000 (limit is 10,240)
- 14:25 UTC: New Relic: queue depth on /checkout endpoint: 847 requests
- 14:26 UTC: Marketing sent promotional email blast at 14:20 UTC
- 14:27 UTC: Traffic to /checkout: 3.2x normal volume
- 14:28 UTC: Redis timeout errors in payment-service logs
- Redis connection pool size: 50 (configured 6 months ago for 10x less traffic)
- No code deployments in the last 48 hours
"""


def example_root_cause_analysis(client: LLMClient) -> None:
    """Use structured CoT for production incident root cause analysis."""

    prompt = f"""You are a senior site reliability engineer (SRE).
Perform a root cause analysis of this production incident.

Use this analysis framework:
1. TIMELINE: Sequence the events chronologically
2. SYMPTOMS vs ROOT CAUSES: What are symptoms vs. actual causes?
3. ROOT CAUSE: State the fundamental cause (not symptoms)
4. CONTRIBUTING FACTORS: What made this failure possible?
5. IMMEDIATE FIX: What stopped the bleeding?
6. LONG-TERM FIXES: What prevents recurrence?

Incident Data:
```
{INCIDENT_SYMPTOMS.strip()}
```

Analysis:"""

    print("\n" + "═" * 72)
    print("  EXAMPLE 3: Production Incident Root Cause Analysis")
    print("  Structured CoT guides systematic investigation")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(
            user_message=prompt,
            temperature=0.1,
            max_tokens=600,
        )
        format_response(response, title="Root Cause Analysis")
    else:
        print(f"  Structured CoT prompt ({count_tokens(prompt)} tokens)")
        print("  Framework: Timeline → Symptoms → Root Cause → Fixes")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Chain-of-Thought Prompting")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 03 — Chain-of-Thought Prompting")
    print("  Teach the model to reason step-by-step before answering")
    print("═" * 72)

    example_business_math(client)
    example_logic_puzzle(client)
    example_root_cause_analysis(client)

    print("\n✅ Chain-of-Thought examples complete.")
    print("   Next: 02_self_consistency.py — majority voting for reliable answers\n")


if __name__ == "__main__":
    main()
