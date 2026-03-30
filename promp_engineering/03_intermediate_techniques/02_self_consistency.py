"""
03_intermediate_techniques/02_self_consistency.py
═══════════════════════════════════════════════════════════════════

WHAT:   Self-Consistency samples multiple independent Chain-of-Thought
        reasoning paths for the same problem and selects the most common
        (majority vote) answer.

WHY:    A single CoT trace can go wrong — hallucinated intermediate steps
        cascade into wrong answers. Running 3–7 traces and voting on the
        final answer improves accuracy significantly on complex reasoning.

        Research finding: Self-Consistency improved GSM8K math benchmark
        accuracy by ~17% over single-trace CoT (Wang et al., 2022).

WHEN TO USE:
        ✓ High-stakes decisions where errors are costly
        ✓ Math / quantitative problems with a single correct answer
        ✓ Complex reasoning with multiple valid reasoning paths
        ✗ Subjective tasks (no single "correct" answer to vote on)
        ✗ Cost-sensitive pipelines (3-7x more expensive than single call)
        ✗ Simple tasks (zero-shot works fine)

COST vs. ACCURACY TRADEOFF:
        N=1:  cheapest, ~baseline accuracy
        N=3:  3x cost, significant improvement
        N=5:  5x cost, often optimal
        N=7+: diminishing returns for most tasks

COMMON PITFALLS:
        - Using temperature=0 (all traces identical → no benefit from voting)
        - Not extracting the final answer before voting (comparing prose)
        - Treating "majority" as certain — still fail on adversarial inputs
"""

import sys
import os
import re
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import count_tokens, estimate_cost


# ─────────────────────────────────────────────────────────────────────────────
# CORE: Self-Consistency Engine
# ─────────────────────────────────────────────────────────────────────────────

def self_consistent_answer(
    client: LLMClient,
    problem: str,
    n_samples: int = 5,
    temperature: float = 0.7,
    max_tokens: int = 400,
    extract_answer_fn=None,
) -> dict:
    """
    Run a problem through CoT n_samples times and return majority vote.

    Args:
        client:            LLM client
        problem:           The problem prompt (should include CoT instructions)
        n_samples:         Number of independent reasoning traces to generate
        temperature:       Should be > 0 (otherwise all traces are identical)
        max_tokens:        Per-trace token limit
        extract_answer_fn: Function that extracts the final answer from a trace.
                           If None, uses the last non-empty line.

    Returns:
        Dict with: majority_answer, vote_counts, traces, cost_usd
    """
    if temperature == 0:
        print("⚠️  Warning: temperature=0 produces identical traces. "
              "Use temperature ≥ 0.5 for self-consistency.")

    traces = []
    total_cost = 0.0

    for i in range(n_samples):
        print(f"  Generating trace {i+1}/{n_samples}...", end="\r")
        response = client.chat(
            user_message=problem,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not client.dry_run:
            traces.append(response.content.strip())
            total_cost += response.cost_usd
        else:
            traces.append(f"[DRY RUN trace {i+1}]")

    print()  # Clear the carriage return line

    # Extract final answers from each trace
    if extract_answer_fn:
        answers = [extract_answer_fn(trace) for trace in traces]
    else:
        # Default: last non-empty line (often the conclusion)
        answers = []
        for trace in traces:
            lines = [l.strip() for l in trace.split("\n") if l.strip()]
            answers.append(lines[-1] if lines else "")

    # Majority vote
    vote_counts = Counter(answers)
    majority_answer = vote_counts.most_common(1)[0][0] if vote_counts else "NO ANSWER"

    return {
        "majority_answer": majority_answer,
        "vote_counts": dict(vote_counts),
        "agreement_pct": (vote_counts[majority_answer] / n_samples * 100) if n_samples > 0 else 0,
        "traces": traces,
        "n_samples": n_samples,
        "cost_usd": total_cost,
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1 — Financial Calculation (high-stakes math)
# ─────────────────────────────────────────────────────────────────────────────

FINANCE_PROBLEM = """
A venture fund made the following investments:
- Series A: $2M for 20% equity in StartupX
- Series B: $5M for 15% equity in StartupY (valued at $50M)
- Seed: $500K for 10% equity in StartupZ

Returns:
- StartupX was acquired for $40M
- StartupY IPO'd at a $300M valuation. The fund sold half their stake at IPO.
- StartupZ shut down (total loss)

Calculate the fund's total return multiple (TVPI = Total Value / Paid-In Capital).
Show your arithmetic clearly. Round to 2 decimal places.
Final answer format: "TVPI = X.XXx"
"""


def extract_tvpi(trace: str) -> str:
    """Extract the TVPI value from a reasoning trace."""
    # Look for "TVPI = X.XXx" pattern
    match = re.search(r"TVPI\s*=\s*(\d+\.?\d*)\s*x?", trace, re.IGNORECASE)
    if match:
        return f"TVPI = {float(match.group(1)):.2f}x"
    # Fallback: look for a number near the end
    numbers = re.findall(r"\d+\.\d+", trace[-200:])
    return f"TVPI ≈ {numbers[-1]}x" if numbers else "UNCLEAR"


def example_financial_calculation(client: LLMClient, n_samples: int) -> None:
    """Demonstrate self-consistency on a venture fund return calculation."""

    problem = f"""{FINANCE_PROBLEM}

Let's work through this step by step."""

    print("\n" + "═" * 72)
    print("  EXAMPLE 1: Venture Fund Return Calculation (TVPI)")
    print(f"  Running {n_samples} independent reasoning traces...")
    print("═" * 72)

    # Estimate cost
    est = estimate_cost(problem, expected_output_tokens=300)
    print(f"\n  Estimated cost: ${est['total_cost'] * n_samples:.4f} "
          f"({n_samples} × ${est['total_cost']:.4f} per trace)")

    result = self_consistent_answer(
        client=client,
        problem=problem,
        n_samples=n_samples,
        temperature=0.6,
        max_tokens=400,
        extract_answer_fn=extract_tvpi,
    )

    print(f"\n  Results across {n_samples} traces:")
    for answer, votes in sorted(result["vote_counts"].items(),
                                 key=lambda x: -x[1]):
        bar = "█" * votes + "░" * (n_samples - votes)
        print(f"    {bar}  {votes}/{n_samples}  {answer}")

    print(f"\n  🏆 Majority answer: {result['majority_answer']}")
    print(f"  Agreement: {result['agreement_pct']:.0f}%")
    print(f"  Total cost: ${result['cost_usd']:.6f}")

    # Note: correct answer
    # StartupX: $2M → 20% of $40M = $8M
    # StartupY: $5M → 15% of $300M = $45M, sold half at IPO = $22.5M
    # StartupZ: total loss
    # Total returned: $8M + $22.5M = $30.5M
    # Total invested: $2M + $5M + $0.5M = $7.5M
    # TVPI = 30.5 / 7.5 = 4.07x
    print(f"\n  ✓ Correct answer: TVPI = 4.07x")
    print(f"  ($8M from X) + ($22.5M from Y) - ($0.5M loss on Z) = $30M / $7.5M invested")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2 — Clinical Decision Support (high-stakes, ambiguous)
# ─────────────────────────────────────────────────────────────────────────────

CLINICAL_SCENARIO = """
Patient: 67-year-old male
Chief Complaint: Sudden onset chest pain radiating to left arm, started 2 hours ago
Vitals: HR 98, BP 155/90, SpO2 96%, RR 18
ECG: ST-segment elevation in leads II, III, aVF
Labs: Troponin I: 2.4 ng/mL (normal < 0.04)
PMH: Type 2 diabetes (A1c 8.2%), hypertension, 40 pack-year smoking history
Current Meds: Metformin 1000mg BID, Lisinopril 10mg daily

Question: What is the most likely diagnosis, and what are the FIRST THREE 
immediate interventions in order of priority?
Answer format: 
Diagnosis: [diagnosis]
Priority 1: [action]
Priority 2: [action]  
Priority 3: [action]
"""


def extract_diagnosis(trace: str) -> str:
    """Extract the diagnosis line from a clinical reasoning trace."""
    for line in trace.split("\n"):
        line = line.strip()
        if line.lower().startswith("diagnosis:"):
            return line.replace("Diagnosis:", "").replace("diagnosis:", "").strip()
    return "UNCLEAR"


def example_clinical_decision(client: LLMClient, n_samples: int) -> None:
    """Use self-consistency for clinical decision support (consensus matters)."""

    problem = f"""{CLINICAL_SCENARIO}

Reason through the clinical picture systematically:
Step 1: Interpret the ECG finding
Step 2: Interpret the troponin level
Step 3: Synthesize the clinical picture
Step 4: List interventions in MONA order (Morphine, Oxygen, Nitrates, Aspirin) 
        adjusted for current guidelines"""

    print("\n" + "═" * 72)
    print("  EXAMPLE 2: Clinical Decision Support")
    print("  Use case: LLM assistance for clinical reasoning (NOT medical advice)")
    print(f"  Running {n_samples} traces → consensus answer")
    print("═" * 72)

    result = self_consistent_answer(
        client=client,
        problem=problem,
        n_samples=n_samples,
        temperature=0.5,
        max_tokens=300,
        extract_answer_fn=extract_diagnosis,
    )

    print(f"\n  Diagnosis consensus across {n_samples} traces:")
    for diag, votes in result["vote_counts"].items():
        print(f"    {votes}/{n_samples}  {diag}")

    print(f"\n  🏆 Majority diagnosis: {result['majority_answer']}")
    print(f"  Agreement: {result['agreement_pct']:.0f}%")

    if result["agreement_pct"] < 60:
        print("  ⚠️  Low agreement — this case may require additional information or specialist review")

    # Show one full trace as example
    if result["traces"] and not client.dry_run:
        print(f"\n  Sample reasoning trace (Trace 1):")
        for line in result["traces"][0].split("\n")[:12]:
            print(f"  {line}")


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS — N samples vs. accuracy visualization
# ─────────────────────────────────────────────────────────────────────────────

def analyze_sample_count_tradeoff() -> None:
    """Show the theoretical accuracy vs. cost tradeoff for different N."""

    print("\n" + "═" * 72)
    print("  ANALYSIS: N Samples vs. Accuracy vs. Cost")
    print("  (Based on research benchmarks — approximate)")
    print("═" * 72)

    data = [
        {"n": 1,  "relative_accuracy": 100, "cost_multiplier": 1, "note": "Baseline CoT"},
        {"n": 3,  "relative_accuracy": 112, "cost_multiplier": 3, "note": "Good sweet spot"},
        {"n": 5,  "relative_accuracy": 117, "cost_multiplier": 5, "note": "Recommended"},
        {"n": 10, "relative_accuracy": 119, "cost_multiplier": 10, "note": "Diminishing returns"},
        {"n": 20, "relative_accuracy": 120, "cost_multiplier": 20, "note": "Rarely justified"},
        {"n": 40, "relative_accuracy": 121, "cost_multiplier": 40, "note": "Research only"},
    ]

    base_cost = 0.001  # $0.001 per single call
    print(f"\n  {'N':>4}  {'Relative Acc':>14}  {'Cost/call':>12}  {'Note'}")
    print("  " + "─" * 60)
    for row in data:
        cost = base_cost * row["cost_multiplier"]
        acc_bar = "█" * int(row["relative_accuracy"] / 10) + f" {row['relative_accuracy']}%"
        print(f"  {row['n']:>4}  {acc_bar:<20} ${cost:.4f}  {row['note']}")

    print("\n  💡 Recommendation:")
    print("     N=5 is the sweet spot for most production use cases.")
    print("     Use N=1 when cost matters more than accuracy.")
    print("     Use N=10+ only when errors have serious consequences.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Self-Consistency Prompting")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--n", type=int, default=3,
                        help="Number of reasoning traces (default: 3)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 03 — Self-Consistency Prompting")
    print("  Run N CoT traces, take majority vote for reliable answers")
    print("═" * 72)

    analyze_sample_count_tradeoff()
    example_financial_calculation(client, n_samples=args.n)
    example_clinical_decision(client, n_samples=args.n)

    print("\n✅ Self-consistency examples complete.")
    print("   Next: 03_react_prompting.py — Reason + Act for tool-using agents\n")


if __name__ == "__main__":
    main()
